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
    "center_spread",
    "max_center_spread",
    "missing_count",
    "duplicate_count",
    "city_mismatch",
    "subset_size",
    "reported_size",
    "isosceles_count",
    "invalid_point_count",
    "out_of_range_count",
    "mean_distance",
    "max_distance",
    "p90_distance",
    "coverage_fraction",
    "coverage_count",
    "coverage_radius",
    "reported_score",
    "duplicate_facility_penalty",
    "facility_count_error",
    "point_mismatch",
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
    if problem_type == "facility_location" and "mean_distance" in keys:
        return "mean_distance"
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
    elif problem_type == "facility_location":
        script = f"""
import importlib.util, json, os, numpy as np
CLUSTER_CENTERS = np.asarray([
    [0.18, 0.22],
    [0.28, 0.78],
    [0.52, 0.50],
    [0.74, 0.24],
    [0.82, 0.78],
    [0.50, 0.86],
], dtype=float)
CLUSTER_WEIGHTS = np.asarray([0.18, 0.16, 0.24, 0.14, 0.18, 0.10], dtype=float)
CLUSTER_STD = 0.065
def generate_demand_points(n, seed):
    rng = np.random.default_rng(seed)
    assignments = rng.choice(len(CLUSTER_CENTERS), size=n, p=CLUSTER_WEIGHTS / CLUSTER_WEIGHTS.sum())
    points = CLUSTER_CENTERS[assignments] + rng.normal(0.0, CLUSTER_STD, size=(n, 2))
    return np.clip(points, 0.02, 0.98)
spec = importlib.util.spec_from_file_location('program', {str(program_path)!r})
program = importlib.util.module_from_spec(spec)
spec.loader.exec_module(program)
if hasattr(program, 'run_facility_location'):
    returned_points, facilities, reported_score = program.run_facility_location()
else:
    returned_points, facilities, reported_score = program.run_packing()
n = int(os.environ.get('FACILITY_N', '50'))
seed = int(os.environ.get('FACILITY_SEED', '0'))
demand_points = generate_demand_points(n, seed)
print(json.dumps({{
    'demand_points': np.asarray(demand_points, dtype=float).tolist(),
    'returned_demand_points': np.asarray(returned_points, dtype=float).tolist(),
    'facilities': np.asarray(facilities, dtype=float).tolist(),
    'reported_score': float(reported_score),
    'coverage_radius': float(os.environ.get('FACILITY_COVERAGE_RADIUS', '0.16')),
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
    stdout_lines = [line for line in result.stdout.strip().splitlines() if line.strip()]
    if not stdout_lines:
        raise RuntimeError("best_program.py produced no visualization JSON")
    return json.loads(stdout_lines[-1])


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
