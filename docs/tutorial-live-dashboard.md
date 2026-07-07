# OpenEvolve Live Dashboard

This document describes the server fallback for the hands-on tutorial. Use it
when Colab is unavailable or too slow. Participants only need a browser; the
server runs OpenEvolve, calls the local Ollama endpoint, stores runs, and renders
checkpoint visualizations.

## Scope

The dashboard supports the same three examples as the Colab notebook:

- `circle_packing`
- `tsp`
- `no_isosceles`

Users can change bounded parameters such as problem size, score mode,
temperature, token budget, iteration count, and visualization timeout. The
dashboard does not accept arbitrary Python evaluator code from users.

## Server Architecture

```text
participant browser
        |
        v
Streamlit dashboard
        |
        +-- in-memory job manager with bounded worker threads
        +-- one run directory per submitted job
        +-- generated initial_program.py, evaluator.py, config_tutorial.yaml
        +-- OpenEvolve subprocess
        +-- checkpoint reader and best_program.py visualization subprocess
        |
        v
Ollama OpenAI-compatible endpoint
```

The queue is intentionally conservative. `OPENEVOLVE_MAX_ACTIVE_JOBS` controls
how many OpenEvolve subprocesses may run at once. Extra submissions remain
queued instead of being rejected because slow but visible progress is better for
the tutorial than tight iteration limits.

## Required Server Services

Ollama must expose an OpenAI-compatible endpoint on the server:

```bash
curl -s http://localhost:11434/v1/models | python3 -m json.tool
```

The default model is `gpt-oss:20b`. Override it with:

```bash
export OPENEVOLVE_MODEL="gpt-oss:20b"
export OPENEVOLVE_API_BASE="http://localhost:11434/v1"
```

OpenEvolve must be installed as either `openevolve-run` on `PATH` or at a custom
path:

```bash
export OPENEVOLVE_CMD="/opt/openevolve/bin/openevolve-run"
```

If OpenEvolve needs extra Python dependencies installed outside its environment,
add them to `PYTHONPATH` for subprocesses:

```bash
export OPENEVOLVE_PYDEPS="$HOME/openevolve_pydeps"
```

## Dashboard Runtime

Install the dashboard dependencies:

```bash
python3 -m venv ~/tutorial-dashboard-venv
source ~/tutorial-dashboard-venv/bin/activate
pip install -r tutorial/server/requirements.txt
```

Start the dashboard:

```bash
export OPENEVOLVE_RUN_ROOT="$HOME/openevolve_tutorial_runs"
export OPENEVOLVE_MAX_ACTIVE_JOBS=3
streamlit run tutorial/server/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Participants connect to:

```text
http://<server-hostname>:8501
```

## Operational Notes

- Run a 1-iteration smoke test before the tutorial for each problem type.
- Keep `checkpoint_interval: 1` so participants see every stable checkpoint.
- Keep `parallel_evaluations: 1` and `num_islands: 1` to avoid multiplying LLM
  requests per participant.
- Prefer short live jobs during the session and use precomputed runs when the
  LLM queue becomes slow.
- Score plots use `combined_score` because this is the value OpenEvolve selects
  on. Problem-specific honest metrics remain visible in the metrics table.
