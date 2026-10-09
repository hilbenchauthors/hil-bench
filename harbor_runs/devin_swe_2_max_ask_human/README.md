# Devin SWE-2 Max ask-human run

This configuration runs Devin SWE-2 Max on the 100 SQL and 100 SWE ask-human HiL-Bench tasks, with three attempts per task and ten concurrent trials. Baseline and full-information tasks are excluded.

## Setup

From the repository root:

```sh
sh harbor_runs/devin_swe_2_max_ask_human/setup.sh
```

The setup installs public upstream Harbor at merge commit `dbd6dd045cbd7135c4a3994515df3907e3b9f0ea`, which contains [harbor-framework/harbor#3485](https://github.com/harbor-framework/harbor/pull/3485), into the ignored `scratch/.venv-harbor-devin/` environment.

Create the repository-root `.env` file with the credentials required by Harbor, Devin, and the task services. The runner forces the ask-human backend to `litellm_proxy` and model to `gpt-4.1-mini`.

## Run

```sh
sh harbor_runs/devin_swe_2_max_ask_human/run.sh --yes
```

The run writes all generated data to:

```text
scratch/devin-swe-2-max-ask-human/hil-bench-devin-swe-2-max-ask-human/
```

That path is relative to the user's checkout and is ignored by Git. After a complete 600-trial run, `run.sh` writes `pass3-summary.json` there with pass@3 and micro-averaged precision, recall, and F1.

The adapter is intentionally kept with this run configuration. It preserves the exact host-namespace Devin installation and execution behavior used for the completed run, while Harbor provides task orchestration, MCP injection, and verification.

The completed reference results from the original run remain locally at:

```text
scratch/devin-swe-2-max-ask-human-final/results/
```
