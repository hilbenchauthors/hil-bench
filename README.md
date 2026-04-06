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
3. In each agent config YAML, set explicit hosting mode in top-level `hosting.type`:
   - `litellm_proxy` (requires `LITELLM_BASE_URL`)
   - `provider_direct` (requires `LITELLM_BASE_URL` to be unset)
   - `self_hosted` (requires `agent.model.api_base` or `hosting.api_base_env`)
4. Create configs and a `config_mappings.yaml` (see `config_mappings.example.yaml`). The configs can be for specific task type, mode, and/or model system and user prompts. **Only modify the prompts and LLM configs from the provided example config YAMLs; all other configuration fields should remain untouched.** If you do modify the prompts, make sure you keep the same set of placeholder variables.
5. Create `judge_config.yaml` (see `judge_config.example.yaml`). This is the model hosting configuration for the `ask_human` tool and must include explicit `hosting.type` (`litellm_proxy`, `provider_direct`, or `self_hosted`).
   - Agent self-hosted URLs can be env-driven via `hosting.api_base_env` (or set directly with `agent.model.api_base`).
   - ask_human self-hosted URL can be env-driven via `hosting.self_hosted_base_url_env` (or set directly with `hosting.self_hosted_base_url`).

## Examples of How to Run

SQL only:

```bash
uv run python run_hil_bench.py \
  --task-type sql \
  --models openai/gpt-5.3-codex \
  --num-datapoints 20 \
  -c 4 \
  --passes 3 \
  --modes baseline ask_human full_info \
  --agent-config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --workspace-dir /tmp \
  --output-dir results
```

SWE only:

```bash
uv run python run_hil_bench.py \
  --task-type swe \
  --models openai/gpt-5.3-codex \
  --num-datapoints 10 \
  --modes baseline ask_human \
  --agent-config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml
```

SQL + SWE together:

```bash
uv run python run_hil_bench.py \
  --task-type both \
  --models openai/gpt-5.3-codex anthropic/claude-sonnet-4 \
  --passes 2 \
  --agent-config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml
```

## Reproducing Paper Metrics

To reproduce `pass@3` and `ask_f1` (Figures 1 and 3 in the paper), run the benchmark with `--passes 3`.
- `pass@3` is computed from the pass-level outputs across the requested task type(s), model(s), and mode(s).
- `ask_f1` is computed from runs in `ask_human` mode.
- The main summary outputs are written under `<output_dir>/<run_name>/public_metrics/`.
For example, to reproduce the public metrics for a model, run with `--passes 3` and include `ask_human` mode:

```bash
uv run python run_hil_bench.py \
  --task-type swe \
  --models openai/gpt-5.3-codex \
  --passes 3 \
  --modes baseline ask_human full_info \
  --agent-config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --output-dir results
```

SQL can be reproduced the same way through the standard uv workflow:

```bash
uv run python run_hil_bench.py \
  --task-type sql \
  --models openai/gpt-5.3-codex \
  --passes 3 \
  --modes baseline ask_human full_info \
  --agent-config-mapping config_mappings.yaml \
  --judge-config judge_config.yaml \
  --output-dir results
```


## Harbor (SWE Only)

Harbor support is currently provided for SWE tasks.

## Harbor Assets

The Harbor-specific packaging assets live under `harbor/`.

- `harbor/harbor_swe/swe_0` through `harbor/harbor_swe/swe_99` contain the per-task Harbor packages.
- `harbor/harbor_swe/warmup_images.sh` resolves task images from local Docker, a local archive tree, or the configured HF bucket.
- `harbor/harbor_swe/build_images.sh` builds the packaged sidecar images used by the Harbor tasks.
- `harbor/harbor_swe/shared/image_source_defaults.json` points at the default image bucket.

## Running Harbor

To build the Harbor helper images:

```bash
cd harbor/harbor_swe
bash build_images.sh
```

To warm or fetch the SWE task images:

`bash warmup_images.sh`

To run a single SWE task:

`uvx harbor run -p harbor/harbor_swe/swe_0/baseline`

Or similarly, for `ask_human` or `full_info`. 

## Output Structure

Each run writes under `<output_dir>/<run_name>/public_metrics/`:

- `pass_level_metrics.csv`
- `summary_metrics.json` (top levels: `SQL`, `SWE`, `BOTH`)
- `trajectories/<mode>/<model>/<task>/pass_<i>_trajectory.json`

