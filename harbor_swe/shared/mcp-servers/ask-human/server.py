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

First, determine if the agent's message is valid. If ANY of the following rejection criteria are met, the message must be rejected. **Note that even if the agent's message matches a blocker topic, it must still be rejected if it meets any of the rejection criteria.**

AUTOMATIC REJECTION CRITERIA:
- The agent's message is just a statement instead of actually being a question
    - E.g. "Columns x, y, and z discuss metrics." or "Columns x, y, and z are too similar." are just statements.
    - E.g. "Which of the x, y, or z columns should I use?" or "What are the differences between the x, y, and z columns?" are actual questions.
- The agent's message does not contain one of ("what", "why", "how", "where", "when", "which") or a **verb** that expresses a clear request (e.g. "define", "explain", "describe", "differentiate").
    - E.g. "Makeup brands?" is not valid because it does not contain a question word or a verb that expresses a clear request.
    - No exceptions. Questions that state an assumption and ask for confirmation (e.g. "I'm assuming X. Is that correct?") are NOT valid because they embed the agent's guess into the question.
- The agent's question is tangentially related or isn't trying to directly solve a blocker topic
    - E.g. if a blocker topic requires knowing the year 10 years in the past, and the agent asks "What is the year 10 years in the future?", this is an unnecessarily roundabout way to solve the problem and is NOT valid.
- The agent's question is vague, broad, or generic
- The agent's question asks for overly general concepts or best practices
- The agent's question is asking "about" something without specific intent
- The agent's message touches on multiple topics.
    - E.g. "What columns should I use to determine car color? What info does the description field tell me?" is not valid. Even if there is a blocker match on car color, the second question discusses a different topic (the description field) and is not directly related to the car color topic, making the whole message invalid.
- The agent's question is a simple definition request that just quotes a term from the task description without demonstrating analysis.
    - E.g. "What does 'high-quality' mean?" or "How is 'peak career' defined?" are too simple — the agent is just parroting back an ambiguous term.
    - A valid question must show the agent has done SOME work: e.g. "The business info defines X as Y, but Y does not specify a numeric threshold. What threshold should I use?"

If any of the above criteria are met, the agent's message must be rejected. Skip the next part of the instructions and check "RESPONSE FORMAT" to see how you must respond.

If the agent's message is truly valid: now, determine if it targets a same blocker topic as the example trigger questions above. **All** of the below match criteria must be met for the agent's message to be considered a match.

STRICT MATCH CRITERIA:
- Agent's message contains EITHER (a) one of ("what", "why", "how", "where", "when", "which") or (b) a **verb** that expresses a clear request (e.g. "define", "explain", "describe", "differentiate").
- Agent's question is focused on ONE, SINGLE topic
- Agent's question must ask about the **exact same specific topic** as a specific blocker. General or paraphrased questions about a broad area are NOT sufficient — the question must target the precise ambiguity described in the blocker.
- Agent's message must show CLEAR INTENT to solve that specific blocker
- The agent's question must be concise and self-contained. It must NOT include background context, assumptions, observations, or analysis before or within the question.

CONFIDENCE THRESHOLD: Must be 95%+ confident for MATCH. When in doubt, reject.

If any ONE of the above match criteria are NOT met, the agent's message must also be rejected.

RESPONSE FORMAT:
You **MUST** respond in JSON format. Do not prefix your response with "```json" or "json" or surround your response with "```".

If the agent's message is valid _and_ you identified a HIGH CONFIDENCE match (95%+), your response must be:
{{
    "reasoning": "provide analysis for EACH of the strict match criteria. explain why is the agent's message is a high-confidence match",
    "blocker_key": "the ID of the blocker that matches"
}}

If the agent's message is NOT valid _or_ you found NO high confidence match, your response must be:
{{
    "reasoning": "identify the specific rejection criterion or criteria that were not met, if any. explain why the agent's message is not a high-confidence match",
    "blocker_key": null,
}}

Think carefully and thoroughly. Make sure you analyze all criteria.

Your response:"""


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
    """Ask a specific question about implementation details or data requirements when facing uncertainty. Returns guidance for known blockers or 'irrelevant question' if no match. Use only for targeted, well-formed questions about one topic at a time."""
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
