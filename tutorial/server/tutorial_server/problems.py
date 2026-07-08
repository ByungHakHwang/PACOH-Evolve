from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path


PROBLEM_TYPES = ("circle_packing", "tsp", "no_isosceles", "facility_location")

CIRCLE_N_OPTIONS = (8, 10, 12, 16, 20, 26, 32)
CIRCLE_SCORE_MODES = (
    "actual_sum_minus_penalty",
    "hard_valid_sum",
    "upstream_target_ratio_n26",
    "soft_penalty",
    "intentionally_bad_reported_sum",
)

TSP_N_OPTIONS = (12, 16, 20, 30, 40, 60)
TSP_SCORE_MODES = ("negative_length", "soft_penalty", "intentionally_bad_reported_length")

NOISO_N_OPTIONS = (6, 8, 10, 12)
NOISO_SCORE_MODES = ("size_minus_penalty", "hard_valid_size", "intentionally_bad_reported_size")

FACILITY_N_OPTIONS = (30, 50, 80, 120)
FACILITY_K_OPTIONS = (3, 4, 5, 6, 8, 10)
FACILITY_SCORE_MODES = (
    "mean_plus_max_distance",
    "negative_mean_distance",
    "negative_max_distance",
    "soft_coverage",
    "hard_coverage",
    "intentionally_bad_reported_score",
)

ITERATION_OPTIONS = (1, 2, 3, 5, 10, 20)
MAX_TOKEN_OPTIONS = (1024, 1536, 2048, 4096)
PROMPT_STYLES = ("balanced", "conservative", "creative")


@dataclass(frozen=True)
class DashboardParams:
    problem_type: str = "circle_packing"
    iterations: int = 2
    temperature: float = 0.4
    max_tokens: int = 1536
    prompt_style: str = "balanced"
    packing_n: int = 16
    score_mode: str = "actual_sum_minus_penalty"
    tsp_n: int = 20
    tsp_seed: int = 0
    tsp_score_mode: str = "negative_length"
    noiso_n: int = 8
    noiso_score_mode: str = "size_minus_penalty"
    facility_n: int = 50
    facility_k: int = 5
    facility_seed: int = 0
    facility_score_mode: str = "mean_plus_max_distance"
    visualization_timeout: int = 90

    def __post_init__(self):
        if self.problem_type not in PROBLEM_TYPES:
            raise ValueError(f"unknown problem_type: {self.problem_type!r}")
        if not 1 <= self.iterations <= 200:
            raise ValueError("iterations must be between 1 and 200")
        if not 0.1 <= self.temperature <= 1.2:
            raise ValueError("temperature must be between 0.1 and 1.2")
        if self.max_tokens not in MAX_TOKEN_OPTIONS:
            raise ValueError(f"max_tokens must be one of {MAX_TOKEN_OPTIONS}")
        if self.prompt_style not in PROMPT_STYLES:
            raise ValueError(f"prompt_style must be one of {PROMPT_STYLES}")
        if not 4 <= self.packing_n <= 40:
            raise ValueError("packing_n must be between 4 and 40")
        if self.score_mode not in CIRCLE_SCORE_MODES:
            raise ValueError(f"score_mode must be one of {CIRCLE_SCORE_MODES}")
        if not 5 <= self.tsp_n <= 80:
            raise ValueError("tsp_n must be between 5 and 80")
        if self.tsp_score_mode not in TSP_SCORE_MODES:
            raise ValueError(f"tsp_score_mode must be one of {TSP_SCORE_MODES}")
        if not 4 <= self.noiso_n <= 14:
            raise ValueError("noiso_n must be between 4 and 14")
        if self.noiso_score_mode not in NOISO_SCORE_MODES:
            raise ValueError(f"noiso_score_mode must be one of {NOISO_SCORE_MODES}")
        if not 10 <= self.facility_n <= 300:
            raise ValueError("facility_n must be between 10 and 300")
        if not 1 <= self.facility_k <= 20:
            raise ValueError("facility_k must be between 1 and 20")
        if self.facility_k > self.facility_n:
            raise ValueError("facility_k must be no larger than facility_n")
        if not 0 <= self.facility_seed <= 100000:
            raise ValueError("facility_seed must be between 0 and 100000")
        if self.facility_score_mode not in FACILITY_SCORE_MODES:
            raise ValueError(f"facility_score_mode must be one of {FACILITY_SCORE_MODES}")
        if not 5 <= self.visualization_timeout <= 300:
            raise ValueError("visualization_timeout must be between 5 and 300")


@dataclass(frozen=True)
class ProblemFiles:
    directory: Path
    initial_program: Path
    hacked_program: Path
    evaluator: Path
    config: Path


CIRCLE_INITIAL_PROGRAM = r'''
import math
import os
import numpy as np


def packing_size():
    return int(os.environ.get("PACKING_N", "16"))


# EVOLVE-BLOCK-START
CENTER_SPREAD = 0.62
EDGE_MARGIN = 0.02


def initial_centers(n, spread=CENTER_SPREAD):
    """Compressed grid seed; increasing spread visibly moves centers outward."""
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    centers = []
    for k in range(n):
        row = k // cols
        col = k % cols
        x_grid = 0.5 if cols == 1 else col / max(1, cols - 1)
        y_grid = 0.5 if rows == 1 else row / max(1, rows - 1)
        if row % 2 == 1 and cols > 1:
            x_grid += 0.18 / max(1, cols - 1)
        x = 0.5 + spread * (x_grid - 0.5)
        y = 0.5 + spread * (y_grid - 0.5)
        centers.append((
            min(max(x, EDGE_MARGIN), 1.0 - EDGE_MARGIN),
            min(max(y, EDGE_MARGIN), 1.0 - EDGE_MARGIN),
        ))
    return np.asarray(centers, dtype=float)


def compute_max_radii(centers):
    centers = np.asarray(centers, dtype=float)
    n = centers.shape[0]
    radii = np.empty(n, dtype=float)
    for i, (x, y) in enumerate(centers):
        radii[i] = max(0.0, min(x, y, 1.0 - x, 1.0 - y))
    for _ in range(6):
        changed = False
        for i in range(n):
            for j in range(i + 1, n):
                dist = float(np.linalg.norm(centers[i] - centers[j]))
                allowed = max(0.0, dist - 1e-6)
                total = radii[i] + radii[j]
                if total > allowed and total > 0:
                    scale = allowed / total
                    radii[i] *= scale
                    radii[j] *= scale
                    changed = True
        if not changed:
            break
    return radii


def construct_packing():
    n = packing_size()
    centers = initial_centers(n)
    radii = compute_max_radii(centers)
    return centers, radii, float(np.sum(radii))
# EVOLVE-BLOCK-END


def run_packing():
    return construct_packing()
'''


CIRCLE_HACKED_PROGRAM = r'''
# EVOLVE-BLOCK-START
import os
import numpy as np


def construct_packing():
    n = int(os.environ.get("PACKING_N", "16"))
    centers = np.full((n, 2), 0.5, dtype=float)
    radii = np.full(n, 0.5, dtype=float)
    reported_sum = 999.0
    return centers, radii, reported_sum
# EVOLVE-BLOCK-END


def run_packing():
    return construct_packing()
'''


CIRCLE_EVALUATOR = r'''
import os
import pickle
import subprocess
import sys
import tempfile
import time

import numpy as np


REFERENCE_VALUE_N26 = 2.635
SCORE_FLOOR = -1e9
REPORTED_LIMIT = 1e6


def _config():
    return (
        int(os.environ.get("PACKING_N", "26")),
        os.environ.get("SCORE_MODE", "actual_sum_minus_penalty"),
        float(os.environ.get("OVERLAP_WEIGHT", "1.0")),
        float(os.environ.get("BOUNDARY_WEIGHT", "1.0")),
        float(os.environ.get("HONEST_OVERLAP_WEIGHT", "20.0")),
        float(os.environ.get("HONEST_BOUNDARY_WEIGHT", "20.0")),
    )


def safe_float(value, default=0.0):
    try:
        result = float(value)
    except Exception:
        return float(default)
    return result if np.isfinite(result) else float(default)


def clamp_reported(value, default=0.0):
    return float(np.clip(safe_float(value, default), -REPORTED_LIMIT, REPORTED_LIMIT))


def finite_score(value):
    try:
        result = float(value)
    except Exception:
        return SCORE_FLOOR
    return result if np.isfinite(result) else SCORE_FLOOR


def sanitize_metrics(metrics):
    for key, value in list(metrics.items()):
        if isinstance(value, (int, float, np.integer, np.floating)):
            numeric = float(value)
            metrics[key] = numeric if np.isfinite(numeric) else (SCORE_FLOOR if key == "combined_score" else 0.0)
    return metrics


def validate_packing(centers, radii):
    n = centers.shape[0]
    if not np.isfinite(centers).all() or not np.isfinite(radii).all():
        return False
    for i in range(n):
        if radii[i] < 0:
            return False
        x, y = centers[i]
        r = radii[i]
        if x - r < -1e-6 or x + r > 1 + 1e-6 or y - r < -1e-6 or y + r > 1 + 1e-6:
            return False
    for i in range(n):
        for j in range(i + 1, n):
            dist = np.sqrt(np.sum((centers[i] - centers[j]) ** 2))
            if dist < radii[i] + radii[j] - 1e-6:
                return False
    return True


def compute_penalties(centers, radii):
    n = centers.shape[0]
    overlap_penalty = 0.0
    boundary_penalty = 0.0
    if not np.isfinite(centers).all() or not np.isfinite(radii).all():
        return 1e6, 1e6
    for i in range(n):
        x, y = centers[i]
        r = radii[i]
        wall_dist = min(x, y, 1 - x, 1 - y)
        boundary_penalty += max(0.0, r - wall_dist)
        boundary_penalty += max(0.0, -r)
    for i in range(n):
        for j in range(i + 1, n):
            dist = np.sqrt(np.sum((centers[i] - centers[j]) ** 2))
            overlap_penalty += max(0.0, (radii[i] + radii[j]) - dist)
    return float(overlap_penalty), float(boundary_penalty)


def run_with_timeout(program_path, timeout_seconds=30):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        script = f"""
import importlib.util, os, pickle, traceback
import numpy as np
try:
    spec = importlib.util.spec_from_file_location("program", {program_path!r})
    program = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(program)
    centers, radii, sum_radii = program.run_packing()
    with open({temp_file.name!r} + ".results", "wb") as f:
        pickle.dump({{"centers": centers, "radii": radii, "sum_radii": sum_radii}}, f)
except Exception as e:
    traceback.print_exc()
    with open({temp_file.name!r} + ".results", "wb") as f:
        pickle.dump({{"error": str(e)}}, f)
"""
        temp_file.write(script.encode())
        temp_file_path = temp_file.name
    results_path = f"{temp_file_path}.results"
    try:
        process = subprocess.Popen([sys.executable, temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            if process.returncode != 0:
                raise RuntimeError(stderr.decode(errors="replace")[-2000:] or stdout.decode(errors="replace")[-2000:])
            if not os.path.exists(results_path):
                raise RuntimeError("Results file not found")
            with open(results_path, "rb") as f:
                results = pickle.load(f)
            if "error" in results:
                raise RuntimeError(results["error"])
            return results["centers"], results["radii"], results["sum_radii"]
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise TimeoutError(f"Process timed out after {timeout_seconds} seconds")
    finally:
        for cleanup_path in (temp_file_path, results_path):
            try:
                os.unlink(cleanup_path)
            except OSError:
                pass


def _zero_metrics(eval_time, error=None):
    metrics = {
        "combined_score": SCORE_FLOOR,
        "sum_radii": 0.0,
        "reported_sum": 0.0,
        "validity": 0.0,
        "overlap_penalty": 0.0,
        "boundary_penalty": 0.0,
        "center_spread": 0.0,
        "max_center_spread": 0.0,
        "eval_time": float(eval_time),
    }
    if error is not None:
        metrics["error"] = str(error)
    return metrics


def evaluate(program_path):
    n, score_mode, overlap_weight, boundary_weight, honest_overlap_weight, honest_boundary_weight = _config()
    start_time = time.time()
    try:
        centers, radii, reported_sum = run_with_timeout(program_path, timeout_seconds=30)
        reported_sum = clamp_reported(reported_sum)
        centers = np.asarray(centers, dtype=float)
        radii = np.asarray(radii, dtype=float)
        if centers.shape != (n, 2) or radii.shape != (n,):
            metrics = _zero_metrics(time.time() - start_time, error="invalid shapes")
            metrics["reported_sum"] = reported_sum
            if score_mode == "intentionally_bad_reported_sum":
                metrics["combined_score"] = reported_sum
            return sanitize_metrics(metrics)
        if not np.isfinite(centers).all() or not np.isfinite(radii).all():
            metrics = _zero_metrics(time.time() - start_time, error="non-finite packing")
            metrics["reported_sum"] = reported_sum
            return sanitize_metrics(metrics)

        valid = validate_packing(centers, radii)
        actual_sum = safe_float(np.sum(radii))
        overlap_penalty, boundary_penalty = compute_penalties(centers, radii)
        center_distances = np.linalg.norm(centers - 0.5, axis=1)
        center_spread = safe_float(np.mean(center_distances))
        max_center_spread = safe_float(np.max(center_distances))
        if score_mode == "hard_valid_sum":
            combined_score = actual_sum if valid else 0.0
        elif score_mode == "actual_sum_minus_penalty":
            combined_score = actual_sum - honest_overlap_weight * overlap_penalty - honest_boundary_weight * boundary_penalty
        elif score_mode == "upstream_target_ratio_n26":
            combined_score = (actual_sum / REFERENCE_VALUE_N26) if valid else 0.0
        elif score_mode == "soft_penalty":
            combined_score = reported_sum - overlap_weight * overlap_penalty - boundary_weight * boundary_penalty
        elif score_mode == "intentionally_bad_reported_sum":
            combined_score = reported_sum
        else:
            raise ValueError(f"Unknown SCORE_MODE: {score_mode!r}")
        combined_score = finite_score(combined_score)
    except Exception as e:
        return _zero_metrics(time.time() - start_time, error=e)

    metrics = {
        "combined_score": float(combined_score),
        "sum_radii": float(actual_sum),
        "reported_sum": float(reported_sum),
        "validity": 1.0 if valid else 0.0,
        "overlap_penalty": float(overlap_penalty),
        "boundary_penalty": float(boundary_penalty),
        "center_spread": center_spread,
        "max_center_spread": max_center_spread,
        "honest_overlap_weight": float(honest_overlap_weight),
        "honest_boundary_weight": float(honest_boundary_weight),
        "eval_time": float(time.time() - start_time),
    }
    if n == 26:
        metrics["reference_ratio"] = float(actual_sum / REFERENCE_VALUE_N26)
        metrics["upstream_target_ratio"] = float((actual_sum / REFERENCE_VALUE_N26) if valid else 0.0)
    print(
        f"Evaluation: mode={score_mode}, valid={valid}, actual_sum={actual_sum:.6f}, "
        f"reported_sum={float(reported_sum):.6f}, combined_score={combined_score:.6f}, "
        f"overlap={overlap_penalty:.4f}, boundary={boundary_penalty:.4f}, center_spread={center_spread:.4f}"
    )
    return sanitize_metrics(metrics)
'''


TSP_INITIAL_PROGRAM = r'''
# EVOLVE-BLOCK-START
import os
import numpy as np


def generate_cities(n, seed):
    rng = np.random.default_rng(seed)
    return rng.random((n, 2))


def tour_length(cities, tour):
    tour = np.asarray(tour, dtype=int)
    ordered = cities[tour]
    closed = np.vstack([ordered, ordered[:1]])
    return float(np.sum(np.linalg.norm(np.diff(closed, axis=0), axis=1)))


def nearest_neighbor_tour(cities):
    n = len(cities)
    unvisited = set(range(1, n))
    tour = [0]
    current = 0
    while unvisited:
        nxt = min(unvisited, key=lambda j: float(np.linalg.norm(cities[current] - cities[j])))
        tour.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return np.asarray(tour, dtype=int)


def run_tsp():
    n = int(os.environ.get("TSP_N", "20"))
    seed = int(os.environ.get("TSP_SEED", "0"))
    cities = generate_cities(n, seed)
    tour = nearest_neighbor_tour(cities)
    length = tour_length(cities, tour)
    return cities, tour, length
# EVOLVE-BLOCK-END


def run_packing():
    return run_tsp()
'''


TSP_HACKED_PROGRAM = r'''
# EVOLVE-BLOCK-START
import os
import numpy as np


def generate_cities(n, seed):
    rng = np.random.default_rng(seed)
    return rng.random((n, 2))


def run_tsp():
    n = int(os.environ.get("TSP_N", "20"))
    seed = int(os.environ.get("TSP_SEED", "0"))
    cities = generate_cities(n, seed)
    # Valid tour with dishonest length: demonstrates why trusting reported metrics is unsafe.
    tour = np.arange(n, dtype=int)
    reported_length = -999.0
    return cities, tour, reported_length
# EVOLVE-BLOCK-END


def run_packing():
    return run_tsp()
'''


TSP_EVALUATOR = r'''
import os
import pickle
import subprocess
import sys
import tempfile
import time

import numpy as np


SCORE_FLOOR = -1e9
REPORTED_LIMIT = 1e6


def _config():
    return (
        int(os.environ.get("TSP_N", "20")),
        int(os.environ.get("TSP_SEED", "0")),
        os.environ.get("TSP_SCORE_MODE", "negative_length"),
        float(os.environ.get("TSP_INVALID_PENALTY", "1000.0")),
    )


def safe_float(value, default=0.0):
    try:
        result = float(value)
    except Exception:
        return float(default)
    return result if np.isfinite(result) else float(default)


def clamp_reported(value, default=0.0):
    return float(np.clip(safe_float(value, default), -REPORTED_LIMIT, REPORTED_LIMIT))


def finite_score(value):
    try:
        result = float(value)
    except Exception:
        return SCORE_FLOOR
    return result if np.isfinite(result) else SCORE_FLOOR


def sanitize_metrics(metrics):
    for key, value in list(metrics.items()):
        if isinstance(value, (int, float, np.integer, np.floating)):
            numeric = float(value)
            metrics[key] = numeric if np.isfinite(numeric) else (SCORE_FLOOR if key == "combined_score" else 0.0)
    return metrics


def generate_cities(n, seed):
    rng = np.random.default_rng(seed)
    return rng.random((n, 2))


def tour_length(cities, tour):
    ordered = cities[np.asarray(tour, dtype=int)]
    closed = np.vstack([ordered, ordered[:1]])
    return float(np.sum(np.linalg.norm(np.diff(closed, axis=0), axis=1)))


def run_with_timeout(program_path, timeout_seconds=30):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        script = f"""
import importlib.util, pickle, traceback
import numpy as np
try:
    spec = importlib.util.spec_from_file_location("program", {program_path!r})
    program = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(program)
    if hasattr(program, "run_tsp"):
        cities, tour, reported_length = program.run_tsp()
    else:
        cities, tour, reported_length = program.run_packing()
    with open({temp_file.name!r} + ".results", "wb") as f:
        pickle.dump({{"cities": cities, "tour": tour, "reported_length": reported_length}}, f)
except Exception as e:
    traceback.print_exc()
    with open({temp_file.name!r} + ".results", "wb") as f:
        pickle.dump({{"error": str(e)}}, f)
"""
        temp_file.write(script.encode())
        temp_file_path = temp_file.name
    results_path = f"{temp_file_path}.results"
    try:
        process = subprocess.Popen([sys.executable, temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            if process.returncode != 0:
                raise RuntimeError(stderr.decode(errors="replace")[-2000:] or stdout.decode(errors="replace")[-2000:])
            if not os.path.exists(results_path):
                raise RuntimeError("Results file not found")
            with open(results_path, "rb") as f:
                results = pickle.load(f)
            if "error" in results:
                raise RuntimeError(results["error"])
            return results["cities"], results["tour"], results["reported_length"]
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise TimeoutError(f"Process timed out after {timeout_seconds} seconds")
    finally:
        for cleanup_path in (temp_file_path, results_path):
            try:
                os.unlink(cleanup_path)
            except OSError:
                pass


def _zero_metrics(eval_time, error=None):
    metrics = {
        "combined_score": -1e9,
        "tour_length": 1e9,
        "reported_length": 1e9,
        "validity": 0.0,
        "missing_count": 0.0,
        "duplicate_count": 0.0,
        "out_of_range_count": 0.0,
        "city_mismatch": 0.0,
        "eval_time": float(eval_time),
    }
    if error is not None:
        metrics["error"] = str(error)
    return metrics


def analyze_tour(returned_cities, returned_tour, n, seed):
    canonical = generate_cities(n, seed)
    returned_cities = np.asarray(returned_cities, dtype=float)
    tour = np.asarray(returned_tour, dtype=int).reshape(-1)
    if returned_cities.shape != canonical.shape or not np.isfinite(returned_cities).all():
        city_mismatch = 1.0
    else:
        city_mismatch = float(np.max(np.abs(returned_cities - canonical)))
    in_range = (tour >= 0) & (tour < n)
    out_of_range_count = int(len(tour) - np.count_nonzero(in_range))
    in_range_tour = [int(x) for x in tour[in_range]]
    duplicate_count = len(in_range_tour) - len(set(in_range_tour))
    missing_count = n - len(set(in_range_tour))
    valid = len(tour) == n and out_of_range_count == 0 and duplicate_count == 0 and missing_count == 0
    if valid:
        actual_length = tour_length(canonical, tour)
    else:
        safe_tour = np.asarray(in_range_tour, dtype=int)
        actual_length = tour_length(canonical, safe_tour) if len(safe_tour) > 1 else 1e9
    return canonical, tour, actual_length, valid, missing_count, duplicate_count, out_of_range_count, city_mismatch


def evaluate(program_path):
    n, seed, score_mode, invalid_penalty = _config()
    start_time = time.time()
    try:
        returned_cities, returned_tour, reported_length = run_with_timeout(program_path, timeout_seconds=30)
        reported_length = clamp_reported(reported_length)
        _, tour, actual_length, valid, missing_count, duplicate_count, out_of_range_count, city_mismatch = analyze_tour(
            returned_cities, returned_tour, n, seed
        )
        actual_length = safe_float(actual_length, 1e9)
        city_mismatch = safe_float(city_mismatch, 1.0)
        violation_count = missing_count + duplicate_count + out_of_range_count
        if score_mode == "negative_length":
            combined_score = -actual_length if valid else -1e6 - invalid_penalty * violation_count
        elif score_mode == "soft_penalty":
            combined_score = -reported_length - invalid_penalty * violation_count - city_mismatch
        elif score_mode == "intentionally_bad_reported_length":
            combined_score = -reported_length
        else:
            raise ValueError(f"Unknown TSP_SCORE_MODE: {score_mode!r}")
        combined_score = finite_score(combined_score)
    except Exception as e:
        return _zero_metrics(time.time() - start_time, error=e)

    metrics = {
        "combined_score": float(combined_score),
        "tour_length": float(actual_length),
        "reported_length": float(reported_length),
        "validity": 1.0 if valid else 0.0,
        "missing_count": float(missing_count),
        "duplicate_count": float(duplicate_count),
        "out_of_range_count": float(out_of_range_count),
        "city_mismatch": float(city_mismatch),
        "eval_time": float(time.time() - start_time),
    }
    print(
        f"Evaluation: mode={score_mode}, valid={valid}, length={actual_length:.6f}, "
        f"reported={float(reported_length):.6f}, score={combined_score:.6f}, violations={violation_count}"
    )
    return sanitize_metrics(metrics)
'''


NOISO_INITIAL_PROGRAM = r'''
# EVOLVE-BLOCK-START
import os
import numpy as np


def construct_subset():
    n = int(os.environ.get("NOISO_N", "8"))
    points = [(x, 0) for x in range(0, n, 2)]
    return n, np.asarray(points, dtype=int), len(points)
# EVOLVE-BLOCK-END


def run_no_isosceles():
    return construct_subset()


def run_packing():
    return construct_subset()
'''


NOISO_HACKED_PROGRAM = r'''
# EVOLVE-BLOCK-START
import os
import numpy as np


def construct_subset():
    n = int(os.environ.get("NOISO_N", "8"))
    points = [(x, y) for x in range(n) for y in range(n)]
    reported_size = 999
    return n, np.asarray(points, dtype=int), reported_size
# EVOLVE-BLOCK-END


def run_no_isosceles():
    return construct_subset()


def run_packing():
    return construct_subset()
'''


NOISO_EVALUATOR = r'''
import itertools
import os
import pickle
import subprocess
import sys
import tempfile
import time

import numpy as np


SCORE_FLOOR = -1e9
REPORTED_LIMIT = 1e6


def _config():
    return (
        int(os.environ.get("NOISO_N", "8")),
        os.environ.get("NOISO_SCORE_MODE", "size_minus_penalty"),
        float(os.environ.get("NOISO_ISOSCELES_PENALTY", "1.5")),
        float(os.environ.get("NOISO_INVALID_PENALTY", "10.0")),
    )


def safe_float(value, default=0.0):
    try:
        result = float(value)
    except Exception:
        return float(default)
    return result if np.isfinite(result) else float(default)


def clamp_reported(value, default=0.0):
    return float(np.clip(safe_float(value, default), -REPORTED_LIMIT, REPORTED_LIMIT))


def finite_score(value):
    try:
        result = float(value)
    except Exception:
        return SCORE_FLOOR
    return result if np.isfinite(result) else SCORE_FLOOR


def sanitize_metrics(metrics):
    for key, value in list(metrics.items()):
        if isinstance(value, (int, float, np.integer, np.floating)):
            numeric = float(value)
            metrics[key] = numeric if np.isfinite(numeric) else (SCORE_FLOOR if key == "combined_score" else 0.0)
    return metrics


def run_with_timeout(program_path, timeout_seconds=30):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        script = f"""
import importlib.util, pickle, traceback
import numpy as np
try:
    spec = importlib.util.spec_from_file_location("program", {program_path!r})
    program = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(program)
    if hasattr(program, "run_no_isosceles"):
        grid_n, selected_points, reported_size = program.run_no_isosceles()
    else:
        grid_n, selected_points, reported_size = program.run_packing()
    with open({temp_file.name!r} + ".results", "wb") as f:
        pickle.dump({{"grid_n": grid_n, "selected_points": selected_points, "reported_size": reported_size}}, f)
except Exception as e:
    traceback.print_exc()
    with open({temp_file.name!r} + ".results", "wb") as f:
        pickle.dump({{"error": str(e)}}, f)
"""
        temp_file.write(script.encode())
        temp_file_path = temp_file.name
    results_path = f"{temp_file_path}.results"
    try:
        process = subprocess.Popen([sys.executable, temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            if process.returncode != 0:
                raise RuntimeError(stderr.decode(errors="replace")[-2000:] or stdout.decode(errors="replace")[-2000:])
            if not os.path.exists(results_path):
                raise RuntimeError("Results file not found")
            with open(results_path, "rb") as f:
                results = pickle.load(f)
            if "error" in results:
                raise RuntimeError(results["error"])
            return results["grid_n"], results["selected_points"], results["reported_size"]
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise TimeoutError(f"Process timed out after {timeout_seconds} seconds")
    finally:
        for cleanup_path in (temp_file_path, results_path):
            try:
                os.unlink(cleanup_path)
            except OSError:
                pass


def normalize_points(points, n):
    shape_error = 0
    try:
        arr = np.asarray(points, dtype=int)
    except Exception:
        return np.empty((0, 2), dtype=int), 1, 0, 1
    if arr.size == 0:
        arr = np.empty((0, 2), dtype=int)
    if arr.ndim != 2 or arr.shape[1] != 2:
        return np.empty((0, 2), dtype=int), 0, 0, 1
    in_bounds = (arr[:, 0] >= 0) & (arr[:, 0] < n) & (arr[:, 1] >= 0) & (arr[:, 1] < n)
    out_of_range_count = int(np.size(in_bounds) - np.count_nonzero(in_bounds))
    in_grid = [tuple(map(int, point)) for point in arr[in_bounds]]
    duplicate_count = len(in_grid) - len(set(in_grid))
    unique_sorted = sorted(set(in_grid))
    return np.asarray(unique_sorted, dtype=int).reshape((-1, 2)), duplicate_count, out_of_range_count, shape_error


def squared_distance(a, b):
    dx = int(a[0]) - int(b[0])
    dy = int(a[1]) - int(b[1])
    return dx * dx + dy * dy


def twice_area(a, b, c):
    return (int(b[0]) - int(a[0])) * (int(c[1]) - int(a[1])) - (int(b[1]) - int(a[1])) * (int(c[0]) - int(a[0]))


def count_isosceles(points):
    count = 0
    examples = []
    for i, j, k in itertools.combinations(range(len(points)), 3):
        a, b, c = points[i], points[j], points[k]
        if twice_area(a, b, c) == 0:
            continue
        d_ab = squared_distance(a, b)
        d_ac = squared_distance(a, c)
        d_bc = squared_distance(b, c)
        if d_ab == d_ac or d_ab == d_bc or d_ac == d_bc:
            count += 1
            if len(examples) < 3:
                examples.append([points[i].tolist(), points[j].tolist(), points[k].tolist()])
    return count, examples


def _zero_metrics(eval_time, error=None):
    metrics = {
        "combined_score": -1e9,
        "subset_size": 0.0,
        "reported_size": 0.0,
        "validity": 0.0,
        "isosceles_count": 0.0,
        "duplicate_count": 0.0,
        "out_of_range_count": 0.0,
        "invalid_point_count": 1.0,
        "eval_time": float(eval_time),
    }
    if error is not None:
        metrics["error"] = str(error)
    return metrics


def evaluate(program_path):
    n, score_mode, iso_penalty, invalid_penalty = _config()
    start_time = time.time()
    try:
        returned_n, points, reported_size = run_with_timeout(program_path, timeout_seconds=30)
        reported_size = clamp_reported(reported_size)
        grid_mismatch = 0 if int(returned_n) == n else 1
        selected, duplicate_count, out_of_range_count, shape_error = normalize_points(points, n)
        isosceles_count, examples = count_isosceles(selected)
        invalid_point_count = duplicate_count + out_of_range_count + shape_error + grid_mismatch
        subset_size = len(selected)
        valid = isosceles_count == 0 and invalid_point_count == 0
        if score_mode == "hard_valid_size":
            combined_score = float(subset_size if valid else 0.0)
        elif score_mode == "size_minus_penalty":
            combined_score = float(subset_size - iso_penalty * isosceles_count - invalid_penalty * invalid_point_count)
        elif score_mode == "intentionally_bad_reported_size":
            combined_score = reported_size
        else:
            raise ValueError(f"Unknown NOISO_SCORE_MODE: {score_mode!r}")
        combined_score = finite_score(combined_score)
    except Exception as e:
        return _zero_metrics(time.time() - start_time, error=e)
    metrics = {
        "combined_score": float(combined_score),
        "subset_size": float(subset_size),
        "reported_size": float(reported_size),
        "validity": 1.0 if valid else 0.0,
        "isosceles_count": float(isosceles_count),
        "duplicate_count": float(duplicate_count),
        "out_of_range_count": float(out_of_range_count),
        "invalid_point_count": float(invalid_point_count),
        "grid_n": float(n),
        "eval_time": float(time.time() - start_time),
    }
    if examples:
        metrics["example_isosceles_triangle"] = str(examples[0])
    print(
        f"Evaluation: mode={score_mode}, valid={valid}, size={subset_size}, "
        f"reported={reported_size}, isosceles={isosceles_count}, invalid_points={invalid_point_count}, "
        f"score={combined_score:.3f}"
    )
    return sanitize_metrics(metrics)
'''


FACILITY_INITIAL_PROGRAM = r'''
# EVOLVE-BLOCK-START
import os
import numpy as np


CLUSTER_CENTERS = np.asarray(
    [
        [0.18, 0.22],
        [0.28, 0.78],
        [0.52, 0.50],
        [0.74, 0.24],
        [0.82, 0.78],
        [0.50, 0.86],
    ],
    dtype=float,
)
CLUSTER_WEIGHTS = np.asarray([0.18, 0.16, 0.24, 0.14, 0.18, 0.10], dtype=float)
CLUSTER_STD = 0.065
FACILITY_SPREAD = 0.16
LLOYD_STEPS = 0


def facility_problem_size():
    n = int(os.environ.get("FACILITY_N", "50"))
    k = int(os.environ.get("FACILITY_K", "5"))
    seed = int(os.environ.get("FACILITY_SEED", "0"))
    return n, k, seed


def generate_demand_points(n, seed):
    rng = np.random.default_rng(seed)
    assignments = rng.choice(len(CLUSTER_CENTERS), size=n, p=CLUSTER_WEIGHTS / CLUSTER_WEIGHTS.sum())
    points = CLUSTER_CENTERS[assignments] + rng.normal(0.0, CLUSTER_STD, size=(n, 2))
    return np.clip(points, 0.02, 0.98)


def initial_facilities(points, k):
    if k == 1:
        return np.asarray([[0.5, 0.5]], dtype=float)
    angles = np.linspace(0.0, 2.0 * np.pi, k, endpoint=False)
    facilities = np.column_stack(
        [
            0.5 + FACILITY_SPREAD * np.cos(angles),
            0.5 + FACILITY_SPREAD * np.sin(angles),
        ]
    )
    return np.clip(facilities, 0.02, 0.98)


def assignment_distances(points, facilities):
    distances = np.linalg.norm(points[:, None, :] - facilities[None, :, :], axis=2)
    return np.min(distances, axis=1)


def lloyd_refine(points, facilities, steps=LLOYD_STEPS):
    facilities = np.asarray(facilities, dtype=float).copy()
    for _ in range(int(steps)):
        distances = np.linalg.norm(points[:, None, :] - facilities[None, :, :], axis=2)
        labels = np.argmin(distances, axis=1)
        next_facilities = facilities.copy()
        for j in range(len(facilities)):
            members = points[labels == j]
            if len(members):
                next_facilities[j] = members.mean(axis=0)
            else:
                nearest = np.min(distances, axis=1)
                next_facilities[j] = points[int(np.argmax(nearest))]
        facilities = np.clip(next_facilities, 0.0, 1.0)
    return facilities


def score_solution(points, facilities):
    distances = assignment_distances(points, facilities)
    return -float(np.mean(distances))


def solve_facility_location():
    n, k, seed = facility_problem_size()
    demand_points = generate_demand_points(n, seed)
    facilities = initial_facilities(demand_points, k)
    facilities = lloyd_refine(demand_points, facilities)
    reported_score = score_solution(demand_points, facilities)
    return demand_points, facilities, reported_score
# EVOLVE-BLOCK-END


def run_facility_location():
    return solve_facility_location()


def run_packing():
    return solve_facility_location()
'''


FACILITY_HACKED_PROGRAM = r'''
# EVOLVE-BLOCK-START
import os
import numpy as np


def run_facility_location():
    n = int(os.environ.get("FACILITY_N", "50"))
    k = int(os.environ.get("FACILITY_K", "5"))
    demand_points = np.full((n, 2), 0.5, dtype=float)
    facilities = np.full((k, 2), 2.0, dtype=float)
    reported_score = 999.0
    return demand_points, facilities, reported_score
# EVOLVE-BLOCK-END


def run_packing():
    return run_facility_location()
'''


FACILITY_EVALUATOR = r'''
import os
import pickle
import subprocess
import sys
import tempfile
import time

import numpy as np


SCORE_FLOOR = -1e9
REPORTED_LIMIT = 1e6


CLUSTER_CENTERS = np.asarray(
    [
        [0.18, 0.22],
        [0.28, 0.78],
        [0.52, 0.50],
        [0.74, 0.24],
        [0.82, 0.78],
        [0.50, 0.86],
    ],
    dtype=float,
)
CLUSTER_WEIGHTS = np.asarray([0.18, 0.16, 0.24, 0.14, 0.18, 0.10], dtype=float)
CLUSTER_STD = 0.065


def _config():
    return (
        int(os.environ.get("FACILITY_N", "50")),
        int(os.environ.get("FACILITY_K", "5")),
        int(os.environ.get("FACILITY_SEED", "0")),
        os.environ.get("FACILITY_SCORE_MODE", "mean_plus_max_distance"),
        float(os.environ.get("FACILITY_COVERAGE_RADIUS", "0.16")),
        float(os.environ.get("FACILITY_MAX_WEIGHT", "0.35")),
        float(os.environ.get("FACILITY_DIVERSITY_WEIGHT", "0.03")),
        float(os.environ.get("FACILITY_INVALID_PENALTY", "100.0")),
    )


def safe_float(value, default=0.0):
    try:
        result = float(value)
    except Exception:
        return float(default)
    return result if np.isfinite(result) else float(default)


def clamp_reported(value, default=0.0):
    return float(np.clip(safe_float(value, default), -REPORTED_LIMIT, REPORTED_LIMIT))


def finite_score(value):
    try:
        result = float(value)
    except Exception:
        return SCORE_FLOOR
    return result if np.isfinite(result) else SCORE_FLOOR


def sanitize_metrics(metrics):
    for key, value in list(metrics.items()):
        if isinstance(value, (int, float, np.integer, np.floating)):
            numeric = float(value)
            metrics[key] = numeric if np.isfinite(numeric) else (SCORE_FLOOR if key == "combined_score" else 0.0)
    return metrics


def generate_demand_points(n, seed):
    rng = np.random.default_rng(seed)
    assignments = rng.choice(len(CLUSTER_CENTERS), size=n, p=CLUSTER_WEIGHTS / CLUSTER_WEIGHTS.sum())
    points = CLUSTER_CENTERS[assignments] + rng.normal(0.0, CLUSTER_STD, size=(n, 2))
    return np.clip(points, 0.02, 0.98)


def run_with_timeout(program_path, timeout_seconds=30):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        script = f"""
import importlib.util, pickle, traceback
import numpy as np
try:
    spec = importlib.util.spec_from_file_location("program", {program_path!r})
    program = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(program)
    if hasattr(program, "run_facility_location"):
        demand_points, facilities, reported_score = program.run_facility_location()
    else:
        demand_points, facilities, reported_score = program.run_packing()
    with open({temp_file.name!r} + ".results", "wb") as f:
        pickle.dump({{"demand_points": demand_points, "facilities": facilities, "reported_score": reported_score}}, f)
except Exception as e:
    traceback.print_exc()
    with open({temp_file.name!r} + ".results", "wb") as f:
        pickle.dump({{"error": str(e)}}, f)
"""
        temp_file.write(script.encode())
        temp_file_path = temp_file.name
    results_path = f"{temp_file_path}.results"
    try:
        process = subprocess.Popen([sys.executable, temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            if process.returncode != 0:
                raise RuntimeError(stderr.decode(errors="replace")[-2000:] or stdout.decode(errors="replace")[-2000:])
            if not os.path.exists(results_path):
                raise RuntimeError("Results file not found")
            with open(results_path, "rb") as f:
                results = pickle.load(f)
            if "error" in results:
                raise RuntimeError(results["error"])
            return results["demand_points"], results["facilities"], results["reported_score"]
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise TimeoutError(f"Process timed out after {timeout_seconds} seconds")
    finally:
        for cleanup_path in (temp_file_path, results_path):
            try:
                os.unlink(cleanup_path)
            except OSError:
                pass


def _zero_metrics(eval_time, error=None):
    metrics = {
        "combined_score": -1e9,
        "mean_distance": 1e9,
        "max_distance": 1e9,
        "p90_distance": 1e9,
        "coverage_fraction": 0.0,
        "coverage_count": 0.0,
        "reported_score": 0.0,
        "validity": 0.0,
        "boundary_penalty": 0.0,
        "duplicate_facility_penalty": 0.0,
        "facility_count_error": 1.0,
        "point_mismatch": 1.0,
        "eval_time": float(eval_time),
    }
    if error is not None:
        metrics["error"] = str(error)
    return metrics


def point_mismatch(returned_points, canonical_points):
    try:
        returned = np.asarray(returned_points, dtype=float)
    except Exception:
        return 1.0
    if returned.shape != canonical_points.shape or not np.isfinite(returned).all():
        return 1.0
    return float(np.max(np.abs(returned - canonical_points)))


def normalize_facilities(facilities, k):
    facility_count_error = 0
    try:
        arr = np.asarray(facilities, dtype=float)
    except Exception:
        arr = np.full((0, 2), np.nan, dtype=float)
    if arr.ndim == 1 and arr.size == 2 * k:
        arr = arr.reshape((k, 2))
    if arr.ndim != 2 or arr.shape[1] != 2:
        arr = np.full((0, 2), np.nan, dtype=float)
    if len(arr) != k:
        facility_count_error = abs(len(arr) - k)
    if len(arr) < k:
        pad = np.full((k - len(arr), 2), 0.5, dtype=float)
        arr = np.vstack([arr, pad]) if len(arr) else pad
    elif len(arr) > k:
        arr = arr[:k]
    finite_mask = np.isfinite(arr)
    nonfinite_count = int(arr.size - np.count_nonzero(finite_mask))
    raw = np.nan_to_num(arr, nan=0.5, posinf=1.0, neginf=0.0)
    boundary_penalty = float(np.sum(np.maximum(0.0, -raw) + np.maximum(0.0, raw - 1.0)))
    safe = np.clip(raw, 0.0, 1.0)
    return safe, facility_count_error, nonfinite_count, boundary_penalty


def duplicate_facility_penalty(facilities, minimum_separation=0.035):
    penalty = 0.0
    for i in range(len(facilities)):
        for j in range(i + 1, len(facilities)):
            distance = float(np.linalg.norm(facilities[i] - facilities[j]))
            penalty += max(0.0, minimum_separation - distance) / minimum_separation
    return float(penalty)


def assignment_distances(points, facilities):
    distances = np.linalg.norm(points[:, None, :] - facilities[None, :, :], axis=2)
    return np.min(distances, axis=1)


def evaluate(program_path):
    n, k, seed, score_mode, coverage_radius, max_weight, diversity_weight, invalid_penalty = _config()
    start_time = time.time()
    try:
        returned_points, returned_facilities, reported_score = run_with_timeout(program_path, timeout_seconds=30)
        reported_score = clamp_reported(reported_score)
        canonical_points = generate_demand_points(n, seed)
        mismatch = point_mismatch(returned_points, canonical_points)
        facilities, facility_count_error, nonfinite_count, boundary_penalty = normalize_facilities(returned_facilities, k)
        distances = assignment_distances(canonical_points, facilities)
        mean_distance = safe_float(np.mean(distances), 1e9)
        max_distance = safe_float(np.max(distances), 1e9)
        p90_distance = safe_float(np.percentile(distances, 90), 1e9)
        coverage_count = int(np.count_nonzero(distances <= coverage_radius))
        coverage_fraction = safe_float(coverage_count / n)
        duplicate_penalty = duplicate_facility_penalty(facilities)
        invalid_indicator = 1.0 if (
            facility_count_error > 0
            or nonfinite_count > 0
            or boundary_penalty > 1e-9
            or mismatch > 1e-8
        ) else 0.0
        valid = invalid_indicator == 0.0
        invalid_cost = invalid_penalty * (invalid_indicator + boundary_penalty + float(facility_count_error) + float(nonfinite_count) + min(1.0, mismatch))

        if score_mode == "mean_plus_max_distance":
            combined_score = -(mean_distance + max_weight * max_distance) - diversity_weight * duplicate_penalty - invalid_cost
        elif score_mode == "negative_mean_distance":
            combined_score = -mean_distance - invalid_cost
        elif score_mode == "negative_max_distance":
            combined_score = -max_distance - invalid_cost
        elif score_mode == "soft_coverage":
            soft_coverage = safe_float(np.mean(np.exp(-((distances / coverage_radius) ** 2))))
            combined_score = soft_coverage - diversity_weight * duplicate_penalty - invalid_cost
        elif score_mode == "hard_coverage":
            combined_score = coverage_fraction if valid else 0.0
        elif score_mode == "intentionally_bad_reported_score":
            combined_score = reported_score
        else:
            raise ValueError(f"Unknown FACILITY_SCORE_MODE: {score_mode!r}")
        combined_score = finite_score(combined_score)
    except Exception as e:
        return _zero_metrics(time.time() - start_time, error=e)

    metrics = {
        "combined_score": float(combined_score),
        "mean_distance": mean_distance,
        "max_distance": max_distance,
        "p90_distance": p90_distance,
        "coverage_fraction": coverage_fraction,
        "coverage_count": float(coverage_count),
        "coverage_radius": float(coverage_radius),
        "reported_score": float(reported_score),
        "validity": 1.0 if valid else 0.0,
        "boundary_penalty": float(boundary_penalty),
        "duplicate_facility_penalty": float(duplicate_penalty),
        "facility_count_error": float(facility_count_error),
        "nonfinite_count": float(nonfinite_count),
        "point_mismatch": float(mismatch),
        "eval_time": float(time.time() - start_time),
    }
    print(
        f"Evaluation: mode={score_mode}, valid={valid}, mean={mean_distance:.6f}, "
        f"max={max_distance:.6f}, coverage={coverage_fraction:.3f}, score={combined_score:.6f}, "
        f"boundary={boundary_penalty:.4f}, duplicate={duplicate_penalty:.4f}"
    )
    return sanitize_metrics(metrics)
'''


CONFIG_TEMPLATE = r'''
max_iterations: {iterations}
checkpoint_interval: 1
log_level: "INFO"

llm:
  primary_model: "{model_alias}"
  primary_model_weight: 1.0
  api_base: "{api_base}"
  api_key: "ollama"
  temperature: {temperature}
  top_p: 0.95
  max_tokens: {max_tokens}
  timeout: 600

prompt:
  system_message: |
{system_message}
  num_top_programs: 3
  use_template_stochasticity: true

database:
  population_size: 12
  archive_size: 8
  num_islands: 1
  elite_selection_ratio: 0.3
  exploitation_ratio: 0.7

evaluator:
  timeout: 60
  cascade_evaluation: false
  parallel_evaluations: 1
  use_llm_feedback: false

diff_based_evolution: true
allow_full_rewrites: false
'''


def _style_prefix(prompt_style: str) -> str:
    if prompt_style == "conservative":
        return "    Make small, deterministic edits and preserve validation-friendly structure."
    if prompt_style == "creative":
        return "    Explore substantially different deterministic constructions while keeping the interface exact."
    return "    Balance useful exploration with simple deterministic Python code."


def _system_message(params: DashboardParams) -> str:
    prefix = _style_prefix(params.prompt_style)
    if params.problem_type == "circle_packing":
        lines = [
            prefix,
            f"    Improve run_packing() for packing {params.packing_n} circles in a unit square.",
            "    Preserve the interface exactly: return centers, radii, sum_radii.",
            "    Optimize both centers and radii; changing centers without recomputing radii usually will not improve the score.",
            "    Do not remove the imports or packing_size() helper above the EVOLVE-BLOCK.",
            "    A good strategy is to choose centers, compute the largest valid radii from those centers, and return the honest sum.",
            "    The starter program intentionally compresses centers toward the middle; improving CENTER_SPREAD or initial_centers should visibly move circles.",
            "    Valid geometry matters more than claiming a large value.",
        ]
    elif params.problem_type == "tsp":
        lines = [
            prefix,
            f"    Improve run_tsp() for a fixed Euclidean TSP instance with {params.tsp_n} cities.",
            "    Preserve the interface exactly: return cities, tour, reported_length.",
            "    The tour must be a permutation of 0..n-1.",
            "    Do not change the city generator; the evaluator recomputes canonical cities independently.",
            "    Minimize the actual closed tour length.",
        ]
    elif params.problem_type == "no_isosceles":
        lines = [
            prefix,
            f"    Improve run_no_isosceles() for the no-isosceles subset problem on a {params.noiso_n} x {params.noiso_n} grid.",
            "    Preserve the interface exactly: return grid_n, selected_points, reported_size.",
            "    Maximize selected points while avoiding every nondegenerate isosceles triangle among triples.",
            "    The evaluator recomputes the unique in-grid subset, so do not rely on reported_size.",
            "    The starter is intentionally weak: every other point on one row.",
        ]
    else:
        lines = [
            prefix,
            f"    Improve run_facility_location() for {params.facility_k} facilities serving {params.facility_n} fixed demand points.",
            "    Preserve the interface exactly: return demand_points, facilities, reported_score.",
            "    The evaluator recomputes canonical demand points from FACILITY_N and FACILITY_SEED, so do not change or fake the demand set.",
            "    Minimize actual assignment distances from demand points to their nearest facility.",
            "    Good strategies include farthest-first initialization, k-means++ style seeding, and several Lloyd refinement steps.",
            "    Keep every facility coordinate finite and inside the unit square.",
            "    Valid geometry and real distances matter more than reported_score.",
        ]
    return "\n".join(lines)


def active_score_mode(params: DashboardParams) -> str:
    if params.problem_type == "circle_packing":
        return params.score_mode
    if params.problem_type == "tsp":
        return params.tsp_score_mode
    if params.problem_type == "no_isosceles":
        return params.noiso_score_mode
    return params.facility_score_mode


def _format_score_preview(problem_type: str, env: dict[str, str], score_mode: str, body: str) -> str:
    header = [
        f"# Problem: {problem_type}",
        f"# Active score mode: {score_mode}",
        *(f"# {key}={value}" for key, value in env.items()),
    ]
    return "\n".join(header) + "\n\n" + textwrap.dedent(body).strip()


def score_function_preview(params: DashboardParams) -> str:
    """Return the evaluator branch used by the selected dashboard score mode."""
    if params.problem_type == "circle_packing":
        snippets = {
            "hard_valid_sum": """
                valid = validate_packing(centers, radii)
                actual_sum = float(np.sum(radii))

                combined_score = actual_sum if valid else 0.0
            """,
            "actual_sum_minus_penalty": """
                actual_sum = float(np.sum(radii))
                overlap_penalty, boundary_penalty = compute_penalties(centers, radii)

                combined_score = (
                    actual_sum
                    - 20.0 * overlap_penalty
                    - 20.0 * boundary_penalty
                )
            """,
            "upstream_target_ratio_n26": """
                REFERENCE_VALUE_N26 = 2.635
                valid = validate_packing(centers, radii)
                actual_sum = float(np.sum(radii))

                combined_score = (actual_sum / REFERENCE_VALUE_N26) if valid else 0.0
            """,
            "soft_penalty": """
                reported_sum = clamp_reported(program_returned_sum)
                overlap_penalty, boundary_penalty = compute_penalties(centers, radii)

                combined_score = reported_sum - 1.0 * overlap_penalty - 1.0 * boundary_penalty
            """,
            "intentionally_bad_reported_sum": """
                # Bad teaching example: trusts the value reported by generated code.
                reported_sum = clamp_reported(program_returned_sum)

                combined_score = reported_sum
            """,
        }
    elif params.problem_type == "tsp":
        snippets = {
            "negative_length": """
                valid = len(tour) == n and violation_count == 0
                actual_length = tour_length(canonical_cities, tour)

                combined_score = -actual_length if valid else -1e6 - 1000.0 * violation_count
            """,
            "soft_penalty": """
                reported_length = clamp_reported(program_returned_length)
                violation_count = missing_count + duplicate_count + out_of_range_count

                combined_score = -reported_length - 1000.0 * violation_count - city_mismatch
            """,
            "intentionally_bad_reported_length": """
                # Bad teaching example: trusts the length reported by generated code.
                reported_length = clamp_reported(program_returned_length)

                combined_score = -reported_length
            """,
        }
    elif params.problem_type == "no_isosceles":
        snippets = {
            "hard_valid_size": """
                valid = isosceles_count == 0 and invalid_point_count == 0

                combined_score = float(subset_size if valid else 0.0)
            """,
            "size_minus_penalty": """
                combined_score = float(
                    subset_size
                    - 1.5 * isosceles_count
                    - 10.0 * invalid_point_count
                )
            """,
            "intentionally_bad_reported_size": """
                # Bad teaching example: trusts the size reported by generated code.
                reported_size = clamp_reported(program_returned_size)

                combined_score = reported_size
            """,
        }
    else:
        snippets = {
            "mean_plus_max_distance": """
                combined_score = (
                    -(mean_distance + 0.35 * max_distance)
                    - 0.03 * duplicate_penalty
                    - invalid_cost
                )
            """,
            "negative_mean_distance": """
                combined_score = -mean_distance - invalid_cost
            """,
            "negative_max_distance": """
                combined_score = -max_distance - invalid_cost
            """,
            "soft_coverage": """
                soft_coverage = float(np.mean(np.exp(-((distances / 0.16) ** 2))))

                combined_score = soft_coverage - 0.03 * duplicate_penalty - invalid_cost
            """,
            "hard_coverage": """
                valid = invalid_indicator == 0.0

                combined_score = coverage_fraction if valid else 0.0
            """,
            "intentionally_bad_reported_score": """
                # Bad teaching example: trusts the score reported by generated code.
                reported_score = clamp_reported(program_returned_score)

                combined_score = reported_score
            """,
        }

    score_mode = active_score_mode(params)
    return _format_score_preview(
        params.problem_type,
        problem_environment(params),
        score_mode,
        snippets[score_mode],
    )


def problem_environment(params: DashboardParams) -> dict[str, str]:
    if params.problem_type == "circle_packing":
        return {"PACKING_N": str(params.packing_n), "SCORE_MODE": params.score_mode}
    if params.problem_type == "tsp":
        return {"TSP_N": str(params.tsp_n), "TSP_SEED": str(params.tsp_seed), "TSP_SCORE_MODE": params.tsp_score_mode}
    if params.problem_type == "no_isosceles":
        return {"NOISO_N": str(params.noiso_n), "NOISO_SCORE_MODE": params.noiso_score_mode}
    return {
        "FACILITY_N": str(params.facility_n),
        "FACILITY_K": str(params.facility_k),
        "FACILITY_SEED": str(params.facility_seed),
        "FACILITY_SCORE_MODE": params.facility_score_mode,
    }


def problem_label(params: DashboardParams) -> str:
    if params.problem_type == "circle_packing":
        return f"circle_n{params.packing_n}_{params.score_mode}"
    if params.problem_type == "tsp":
        return f"tsp_n{params.tsp_n}_seed{params.tsp_seed}_{params.tsp_score_mode}"
    if params.problem_type == "no_isosceles":
        return f"noiso_n{params.noiso_n}_{params.noiso_score_mode}"
    return f"facility_n{params.facility_n}_k{params.facility_k}_seed{params.facility_seed}_{params.facility_score_mode}"


def create_problem_files(root: Path | str, params: DashboardParams, model_alias: str, api_base: str) -> ProblemFiles:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if params.problem_type == "circle_packing":
        files = {
            "initial_program.py": CIRCLE_INITIAL_PROGRAM,
            "hacked_program.py": CIRCLE_HACKED_PROGRAM,
            "evaluator.py": CIRCLE_EVALUATOR,
        }
    elif params.problem_type == "tsp":
        files = {
            "initial_program.py": TSP_INITIAL_PROGRAM,
            "hacked_program.py": TSP_HACKED_PROGRAM,
            "evaluator.py": TSP_EVALUATOR,
        }
    elif params.problem_type == "no_isosceles":
        files = {
            "initial_program.py": NOISO_INITIAL_PROGRAM,
            "hacked_program.py": NOISO_HACKED_PROGRAM,
            "evaluator.py": NOISO_EVALUATOR,
        }
    else:
        files = {
            "initial_program.py": FACILITY_INITIAL_PROGRAM,
            "hacked_program.py": FACILITY_HACKED_PROGRAM,
            "evaluator.py": FACILITY_EVALUATOR,
        }

    for filename, content in files.items():
        (root / filename).write_text(textwrap.dedent(content).lstrip())

    system_message = _system_message(params)
    indented_message = "\n".join(f"    {line.strip()}" if line.strip() else "" for line in system_message.splitlines())
    config = CONFIG_TEMPLATE.format(
        iterations=params.iterations,
        model_alias=model_alias,
        api_base=api_base,
        temperature=params.temperature,
        max_tokens=params.max_tokens,
        system_message=indented_message,
    )
    (root / "config_tutorial.yaml").write_text(textwrap.dedent(config).lstrip())
    return ProblemFiles(
        directory=root,
        initial_program=root / "initial_program.py",
        hacked_program=root / "hacked_program.py",
        evaluator=root / "evaluator.py",
        config=root / "config_tutorial.yaml",
    )
