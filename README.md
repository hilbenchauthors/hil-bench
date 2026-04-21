# HiL-Bench

Repo to run on the public dataset of HiL-Bench, a benchmark designed to measure agents' ability to identify when they need to ask for help in coding tasks. Every task has blockers, ambiguities that **must** be clarified in order for the task to be solved correctly.

Task types:

- SQL
- SWE

Modes:

- Baseline: the agent is presented with the task with blockers as is
- Full info: the agent is given the task AND the blocker resolutions upfront
- Ask human: the agent is presented with the task with blockers as is and has access to an `ask_human` tool to get clarifications

## Setup

1. Create a `uv` project venv.
2. Copy `.env_template` to `.env` and set your provider keys.
3. The public dataset is hosted externally on Hugging Face at [ScaleAI/hil-bench](https://huggingface.co/datasets/ScaleAI/hil-bench), not committed into this repo; download or materialize the task inputs locally and pass their path to the CLI.
4. In each agent config YAML, set explicit hosting mode in top-level `hosting.type`:
   - `litellm_proxy` (requires `LITELLM_BASE_URL`)
   - `provider_direct` (requires `LITELLM_BASE_URL` to be unset)
   - `self_hosted` (requires `agent.model.api_base` or `hosting.api_base_env`)
5. Create configs and a `config_mappings.yaml` (see `config_mappings.example.yaml`). The configs can be for specific task type, mode, and/or model system and user prompts. **Only modify the prompts and LLM configs from the provided example config YAMLs; all other configuration fields should remain untouched.** If you do modify the prompts, make sure you keep the same set of placeholder variables.
6. Create `judge_config.yaml` (see `judge_config.example.yaml`). This is the model hosting configuration for the `ask_human` tool and must include explicit `hosting.type` (`litellm_proxy`, `provider_direct`, or `self_hosted`).
   - Agent self-hosted URLs can be env-driven via `hosting.api_base_env` (or set directly with `agent.model.api_base`).
   - ask_human self-hosted URL can be env-driven via `hosting.self_hosted_base_url_env` (or set directly with `hosting.self_hosted_base_url`).

## Examples of How to Run

SQL only:

```bash
uv run hil sql /path/to/sql_task_dir \
  --model openai/gpt-5.3-codex \
  --num-workers 4 \
  --passes 3 \
  --all-modes \
  --config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --output-dir results
```

SWE only:

```bash
uv run hil swe /path/to/swe_tasks_dir \
  --model openai/gpt-5.3-codex \
  --num-tasks 10 \
  --passes 3 \
  --all-modes \
  --config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --output-dir results
```

SQL + SWE:

```bash
uv run hil sql /path/to/sql_task_dir \
  --model openai/gpt-5.3-codex anthropic/claude-sonnet-4 \
  --passes 2 \
  --all-modes \
  --config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --output-dir results

uv run hil swe /path/to/swe_tasks_dir \
  --model openai/gpt-5.3-codex anthropic/claude-sonnet-4 \
  --passes 2 \
  --all-modes \
  --config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --output-dir results
```

## Reproducing Paper Metrics

To reproduce `pass@3` and `ask_f1` (Figures 1 and 3 in the paper), run the benchmark with `--passes 3`.
- `pass@3` is computed from the pass-level outputs across the requested task type(s), model(s), and mode(s).
- `ask_f1` is computed from runs in `ask_human` mode.
- The main summary outputs are written under `<output_dir>/<run_name>/public_metrics/`.
For example, to reproduce the public metrics for a model, run with `--passes 3` and include `ask_human` mode:

```bash
uv run hil swe /path/to/swe_tasks_dir \
  --model openai/gpt-5.3-codex \
  --passes 3 \
  --all-modes \
  --config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --output-dir results
```

SQL can be reproduced the same way through the standard uv workflow:

```bash
uv run hil sql /path/to/sql_task_dir \
  --model openai/gpt-5.3-codex \
  --passes 3 \
  --all-modes \
  --config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --output-dir results
```


## Harbor (SWE Only)

Harbor support is currently provided for SWE tasks.

## Harbor Assets

The Harbor-specific packaging assets live under `harbor_swe/`.

- `harbor_swe/swe_0` through `harbor_swe/swe_99` contain the per-task Harbor packages.
- `harbor_swe/warmup_images.sh` resolves task images from local Docker, a local archive tree, or the configured HF bucket.
- `harbor_swe/build_images.sh` builds the packaged sidecar images used by the Harbor tasks.
- `harbor_swe/shared/image_source_defaults.json` points at the default image bucket.

## Running Harbor

To build the Harbor helper images:

```bash
cd harbor_swe
bash build_images.sh
```

To warm or fetch the SWE task images:

```bash
cd harbor_swe
bash warmup_images.sh
```

The SWE Harbor images are hosted externally at [ScaleAI/hil-bench-swe-images](https://huggingface.co/buckets/ScaleAI/hil-bench-swe-images).

To run a single SWE task:

```bash
uvx harbor run -p harbor_swe/swe_0/baseline
```

Or similarly, for `ask_human` or `full_info`. 

## Output Structure

Each run writes under `<output_dir>/<run_name>/public_metrics/`:

- `pass_level_metrics.csv`
- `summary_metrics.json` (top levels: `SQL`, `SWE`, `BOTH`)
- `trajectories/<mode>/<model>/<task>/pass_<i>_trajectory.json`

