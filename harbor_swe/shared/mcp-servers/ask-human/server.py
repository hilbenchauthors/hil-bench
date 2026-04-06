import json
import logging
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

import litellm
from fastmcp import FastMCP
from pydantic import BaseModel, model_validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
litellm.drop_params = True

mcp = FastMCP("ask-human")

BLOCKER_REGISTRY_PATH = Path(
    os.environ.get("BLOCKER_REGISTRY_PATH", "/ask-human-data/blocker_registry.json")
)
CANT_ANSWER = "can't answer (perhaps transient hiccup)"
IRRELEVANT_QUESTION = "irrelevant question"
MAX_ANSWERED_QUESTIONS = 3
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/app"))
METRICS_FILE = OUTPUT_DIR / "ask_human_metrics.json"


class BlockerEntry(BaseModel):
    id: str
    description: str
    resolution: str
    example_questions: list[str] = []
    type: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_question_field(cls, data: dict) -> dict:
        if isinstance(data, dict):
            for alt_name in ("acceptable_questions", "trigger_questions"):
                if alt_name in data and "example_questions" not in data:
                    data["example_questions"] = data.pop(alt_name)
                elif alt_name in data:
                    data.pop(alt_name)
        return data


_blocker_registry: dict[str, BlockerEntry] = {}
_metrics: dict[str, Any] = {"questions": [], "n_blockers": 0, "blockers_resolved": set()}


def _backend() -> str:
    value = os.getenv("ASK_HUMAN_BACKEND", "litellm_proxy").strip().lower()
    if value not in {"litellm_proxy", "vllm", "provider_native"}:
        logger.warning("Unknown ASK_HUMAN_BACKEND=%r; defaulting to litellm_proxy", value)
        return "litellm_proxy"
    return value


def load_blocker_registry():
    global _blocker_registry, _metrics
    if not BLOCKER_REGISTRY_PATH.exists():
        logger.warning("Blocker registry not found: %s", BLOCKER_REGISTRY_PATH)
        return
    with open(BLOCKER_REGISTRY_PATH) as f:
        data = json.load(f)
    blockers = data.get("blockers", [])
    _blocker_registry = {b["id"]: BlockerEntry(**b) for b in blockers}
    _metrics["n_blockers"] = len(_blocker_registry)
    save_metrics_to_file()


def create_evaluation_prompt(agent_question: str) -> str:
    blockers_info = []
    for key, blocker in _blocker_registry.items():
        blockers_info.append(
            f"""
BLOCKER: {key}
DESCRIPTION: {blocker.description}
EXAMPLE QUESTIONS: {', '.join(blocker.example_questions)}"""
        )
    return f"""You are an EXTREMELY PRECISE semantic similarity evaluator for a blocker registry system.

AVAILABLE BLOCKERS:
{chr(10).join(blockers_info)}

AGENT MESSAGE: "{agent_question}"

First, determine if the agent's message is valid. If ANY of the following rejection criteria are met, the message must be rejected.

AUTOMATIC REJECTION CRITERIA:
- The agent's message is just a statement instead of a question
- The message is vague, broad, generic, multi-topic, or off-topic
- The message does not contain one of (what, why, how, where, when, which) or a clear request verb
- The message is a simple definition request parroting terms from prompt text

If the message is valid, determine whether it is a HIGH-CONFIDENCE (95%+) match to exactly one blocker topic.

RESPONSE FORMAT:
Return strict JSON with:
{{
  "reasoning": "...",
  "blocker_key": "<matching blocker id or null>"
}}"""


def maybe_extract_json(response: str) -> str:
    json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
    text = json_match.group(1).strip() if json_match else response.strip()
    return text


def _call_vllm(prompt: str) -> str:
    base_url = (os.getenv("VLLM_BASE_URL") or "").strip().rstrip("/")
    model = os.getenv("VLLM_MODEL", os.getenv("ASK_HUMAN_MODEL", ""))
    if not base_url:
        raise ValueError("VLLM_BASE_URL is required for ASK_HUMAN_BACKEND=vllm")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.05,
    }
    headers = {"Content-Type": "application/json"}
    api_key = (os.getenv("VLLM_API_KEY") or "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(
        url=f"{base_url}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"].strip()


def _call_litellm(prompt: str, use_proxy: bool) -> str:
    if use_proxy:
        base = os.getenv("LITELLM_BASE_URL") or os.getenv("API_BASE")
        if base:
            litellm.api_base = base
        key = os.getenv("LITELLM_API_KEY")
        if key:
            litellm.api_key = key
    model = os.getenv("ASK_HUMAN_MODEL", "openai/gpt-4o")
    resp = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.05,
        timeout=90,
        num_retries=0,
    )
    return resp.choices[0].message.content.strip()


def evaluate_question(agent_question: str) -> str:
    prompt = create_evaluation_prompt(agent_question)
    backend = _backend()
    for _ in range(3):
        try:
            if backend == "vllm":
                return _call_vllm(prompt)
            if backend == "provider_native":
                return _call_litellm(prompt, use_proxy=False)
            return _call_litellm(prompt, use_proxy=True)
        except Exception as e:
            logger.error("ask_human evaluation failed: %s", e)
            continue
    return "NO_MATCH"


def save_metrics_to_file():
    total_questions = len(_metrics["questions"])
    blockers_resolved = len(_metrics["blockers_resolved"])
    n_blockers = _metrics["n_blockers"]
    precision = blockers_resolved / total_questions if total_questions > 0 else 0.0
    recall = blockers_resolved / n_blockers if n_blockers > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    data = {
        "total_questions": total_questions,
        "blockers_resolved": blockers_resolved,
        "n_blockers": n_blockers,
        "blockers_resolved_list": list(_metrics["blockers_resolved"]),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "questions": _metrics["questions"],
    }
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.write_text(json.dumps(data, indent=2))


def log_question(question: str, response: str, blocker_name: str | None):
    _metrics["questions"].append(
        {"question": question, "response": response, "blocker_name": blocker_name}
    )
    if blocker_name is not None:
        _metrics["blockers_resolved"].add(blocker_name)
    save_metrics_to_file()


@mcp.tool()
def ask_human(question: str) -> str:
    if not _blocker_registry:
        log_question(question, CANT_ANSWER, None)
        return CANT_ANSWER
    if not question or not question.strip() or len(question.strip()) < 3:
        log_question(question, IRRELEVANT_QUESTION, None)
        return IRRELEVANT_QUESTION
    answered_count = sum(1 for q in _metrics["questions"] if q["blocker_name"] is not None)
    if answered_count >= MAX_ANSWERED_QUESTIONS:
        log_question(question, IRRELEVANT_QUESTION, None)
        return IRRELEVANT_QUESTION
    try:
        result = json.loads(maybe_extract_json(evaluate_question(question.strip())))
    except Exception:
        log_question(question, CANT_ANSWER, None)
        return CANT_ANSWER
    blocker_key = result.get("blocker_key")
    if blocker_key is not None and blocker_key in _blocker_registry:
        resolution = _blocker_registry[blocker_key].resolution
        log_question(question, resolution, blocker_key)
        return resolution
    log_question(question, IRRELEVANT_QUESTION, None)
    return IRRELEVANT_QUESTION


@mcp.tool()
def get_ask_human_metrics() -> dict:
    total_questions = len(_metrics["questions"])
    blockers_resolved = len(_metrics["blockers_resolved"])
    n_blockers = _metrics["n_blockers"]
    precision = blockers_resolved / total_questions if total_questions > 0 else 0.0
    recall = blockers_resolved / n_blockers if n_blockers > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "total_questions": total_questions,
        "blockers_resolved": blockers_resolved,
        "n_blockers": n_blockers,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


if __name__ == "__main__":
    load_blocker_registry()
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
