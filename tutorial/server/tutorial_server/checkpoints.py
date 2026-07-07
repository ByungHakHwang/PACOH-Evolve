from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


METRIC_KEYS = (
    "combined_score",
    "sum_radii",
    "tour_length",
    "reported_sum",
    "reported_length",
    "validity",
    "overlap_penalty",
    "boundary_penalty",
    "missing_count",
    "duplicate_count",
    "city_mismatch",
    "subset_size",
    "reported_size",
    "isosceles_count",
    "invalid_point_count",
    "out_of_range_count",
)


@dataclass(frozen=True)
class StableCheckpoint:
    number: int
    directory: Path
    info: dict[str, Any]

    @property
    def program_path(self) -> Path:
        return self.directory / "best_program.py"

    @property
    def info_path(self) -> Path:
        return self.directory / "best_program_info.json"


def checkpoint_number(path: Path) -> int:
    match = re.fullmatch(r"checkpoint_(\d+)", path.name)
    return int(match.group(1)) if match else -1


def stable_checkpoints(run_dir: Path | str, min_age_seconds: float = 1.0) -> list[StableCheckpoint]:
    checkpoints_dir = Path(run_dir) / "checkpoints"
    if not checkpoints_dir.exists():
        return []
    now = time.time()
    checkpoints: list[StableCheckpoint] = []
    for path in checkpoints_dir.glob("checkpoint_*"):
        number = checkpoint_number(path)
        if number < 0:
            continue
        program_path = path / "best_program.py"
        info_path = path / "best_program_info.json"
        if not program_path.exists() or not info_path.exists():
            continue
        if max(program_path.stat().st_mtime, info_path.stat().st_mtime) > now - min_age_seconds:
            continue
        try:
            info = json.loads(info_path.read_text())
        except Exception:
            continue
        checkpoints.append(StableCheckpoint(number=number, directory=path, info=info))
    return sorted(checkpoints, key=lambda item: item.number)


def latest_stable_checkpoint(run_dir: Path | str, min_age_seconds: float = 1.0) -> StableCheckpoint | None:
    checkpoints = stable_checkpoints(run_dir, min_age_seconds=min_age_seconds)
    return checkpoints[-1] if checkpoints else None


def checkpoint_history(run_dir: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for checkpoint in stable_checkpoints(run_dir, min_age_seconds=0.0):
        metrics = checkpoint.info.get("metrics", {})
        row = {
            "checkpoint": checkpoint.number,
            "current_iteration": checkpoint.info.get("current_iteration", checkpoint.number),
            "program_birth_iteration": checkpoint.info.get("iteration"),
        }
        for key in METRIC_KEYS:
            if key in metrics:
                row[key] = metrics[key]
        rows.append(row)
    return rows


def score_column(problem_type: str, history: list[dict[str, Any]]) -> str | None:
    if not history:
        return None
    keys = set().union(*(row.keys() for row in history))
    if "combined_score" in keys:
        return "combined_score"
    if problem_type == "circle_packing" and "sum_radii" in keys:
        return "sum_radii"
    if problem_type == "tsp" and "tour_length" in keys:
        return "tour_length"
    if problem_type == "no_isosceles" and "subset_size" in keys:
        return "subset_size"
    return None


def execute_program(program_path: Path | str, env: dict[str, str] | None = None, problem_type: str = "circle_packing", timeout: int = 90):
    program_path = Path(program_path)
    if problem_type == "tsp":
        script = f"""
import importlib.util, json, numpy as np
spec = importlib.util.spec_from_file_location('program', {str(program_path)!r})
program = importlib.util.module_from_spec(spec)
spec.loader.exec_module(program)
if hasattr(program, 'run_tsp'):
    cities, tour, reported_length = program.run_tsp()
else:
    cities, tour, reported_length = program.run_packing()
print(json.dumps({{
    'cities': np.asarray(cities, dtype=float).tolist(),
    'tour': np.asarray(tour, dtype=int).tolist(),
    'reported_length': float(reported_length),
}}))
"""
    elif problem_type == "no_isosceles":
        script = f"""
import importlib.util, json, numpy as np
spec = importlib.util.spec_from_file_location('program', {str(program_path)!r})
program = importlib.util.module_from_spec(spec)
spec.loader.exec_module(program)
if hasattr(program, 'run_no_isosceles'):
    grid_n, selected_points, reported_size = program.run_no_isosceles()
else:
    grid_n, selected_points, reported_size = program.run_packing()
print(json.dumps({{
    'grid_n': int(grid_n),
    'selected_points': np.asarray(selected_points, dtype=int).tolist(),
    'reported_size': float(reported_size),
}}))
"""
    else:
        script = f"""
import importlib.util, json, numpy as np
spec = importlib.util.spec_from_file_location('program', {str(program_path)!r})
program = importlib.util.module_from_spec(spec)
spec.loader.exec_module(program)
centers, radii, sum_radii = program.run_packing()
print(json.dumps({{
    'centers': np.asarray(centers, dtype=float).tolist(),
    'radii': np.asarray(radii, dtype=float).tolist(),
    'sum_radii': float(sum_radii),
}}))
"""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=run_env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"best_program.py did not finish within {timeout}s") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or result.stdout[-2000:])
    return json.loads(result.stdout)


def log_tail(run_dir: Path | str, limit: int = 4000) -> str:
    log_dir = Path(run_dir) / "logs"
    if not log_dir.exists():
        return ""
    log_files = sorted(log_dir.glob("*.log"), key=lambda path: path.stat().st_mtime)
    if not log_files:
        return ""
    return log_files[-1].read_text(errors="replace")[-limit:]


def best_source(run_dir: Path | str, min_age_seconds: float = 1.0) -> str:
    checkpoint = latest_stable_checkpoint(run_dir, min_age_seconds=min_age_seconds)
    if checkpoint and checkpoint.program_path.exists():
        return checkpoint.program_path.read_text(errors="replace")
    best_path = Path(run_dir) / "best" / "best_program.py"
    if best_path.exists():
        return best_path.read_text(errors="replace")
    return ""
