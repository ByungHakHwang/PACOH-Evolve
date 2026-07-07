"""
Tutorial evaluator for circle packing (n=26), RAW-score version.

Differences from the upstream example evaluator
------------------------------------------------
1. `combined_score` is the RAW objective (sum of radii), NOT normalized by the
   AlphaEvolve reference value 2.635. This makes the tutorial message honest:
   "we maximize the sum of radii; 2.635 is a reference, not a proven optimum."

2. There is a SINGLE scoring path: `evaluate()`. The cascade stage functions
   (`evaluate_stage1` / `evaluate_stage2`) are intentionally REMOVED.

   Why this matters (verified against OpenEvolve 0.3.0):
   - When `cascade_evaluation: true`, the engine calls `evaluate_stage1/2` and
     BYPASSES `evaluate()` (openevolve/evaluator.py:163-165, 388-389).
   - Thresholds are compared directly against `combined_score`, un-normalized
     (openevolve/evaluator.py:689).
   So a raw-score change placed only in `evaluate()` would silently have no
   effect under cascade. By removing the stage functions, even if someone flips
   `cascade_evaluation: true`, the engine falls back to `_direct_evaluate` ->
   `evaluate()` (openevolve/evaluator.py:388-389). Use `cascade_evaluation: false`
   in config_tutorial.yaml regardless.

Score modes (select via the SCORE_MODE environment variable)
------------------------------------------------------------
- hard_valid_sum (default):
      combined_score = actual_sum        if the packing is geometrically valid
                     = 0.0               otherwise
  The honest objective. Invalid geometry scores 0 no matter how large the sum.

- soft_penalty:
      combined_score = reported_sum
                       - OVERLAP_WEIGHT  * overlap_penalty
                       - BOUNDARY_WEIGHT * boundary_penalty
  Trusts the program's *reported* sum but subtracts continuous penalties for
  overlaps and out-of-square parts. Shows that a badly-shaped reward is gameable
  and can even go negative.

- intentionally_bad_reported_sum:
      combined_score = reported_sum      (NO validation at all)
  The "reward hacking" demo: a program can simply return an inflated third value
  and win. Illustrates exactly why you need an independent, honest evaluator.

The number of circles is read from PACKING_N (default 26) so the same file can be
reused for the Intermediate tier; the geometric checks are already n-agnostic.
"""

import numpy as np
import os
import pickle
import subprocess
import sys
import tempfile
import time
import traceback


class TimeoutError(Exception):
    pass


def _config():
    """Read tutorial knobs from the environment (dashboard sets these per job)."""
    n = int(os.environ.get("PACKING_N", "26"))
    score_mode = os.environ.get("SCORE_MODE", "hard_valid_sum")
    overlap_weight = float(os.environ.get("OVERLAP_WEIGHT", "1.0"))
    boundary_weight = float(os.environ.get("BOUNDARY_WEIGHT", "1.0"))
    return n, score_mode, overlap_weight, boundary_weight


# AlphaEvolve reported value for n=26. Reference ONLY (not a proven optimum,
# and only meaningful when n == 26). Never used for selection.
REFERENCE_VALUE_N26 = 2.635


def validate_packing(centers, radii):
    """
    Validate that circles don't overlap and are inside the unit square.

    Returns True if valid, False otherwise.
    """
    n = centers.shape[0]

    if np.isnan(centers).any() or np.isnan(radii).any():
        print("NaN values detected in centers/radii")
        return False

    for i in range(n):
        if radii[i] < 0:
            print(f"Circle {i} has negative radius {radii[i]}")
            return False

    for i in range(n):
        x, y = centers[i]
        r = radii[i]
        if x - r < -1e-6 or x + r > 1 + 1e-6 or y - r < -1e-6 or y + r > 1 + 1e-6:
            print(f"Circle {i} at ({x}, {y}) r={r} is outside the unit square")
            return False

    for i in range(n):
        for j in range(i + 1, n):
            dist = np.sqrt(np.sum((centers[i] - centers[j]) ** 2))
            if dist < radii[i] + radii[j] - 1e-6:
                print(f"Circles {i} and {j} overlap: dist={dist}, r1+r2={radii[i] + radii[j]}")
                return False

    return True


def compute_penalties(centers, radii):
    """
    Continuous (non-binary) constraint violations, used by the soft_penalty mode.

    overlap_penalty : total linear overlap depth summed over all circle pairs.
    boundary_penalty: total distance by which circles poke outside the unit square
                      (a negative radius or an out-of-[0,1] center inflates this).
    """
    n = centers.shape[0]
    overlap_penalty = 0.0
    boundary_penalty = 0.0

    # NaN-safe: treat NaN as a large violation so the reward never rewards it.
    if np.isnan(centers).any() or np.isnan(radii).any():
        return 1e6, 1e6

    for i in range(n):
        x, y = centers[i]
        r = radii[i]
        # Distance from center to the nearest wall; negative if the center is
        # already outside the square. A circle is inside iff r <= wall_dist.
        wall_dist = min(x, y, 1 - x, 1 - y)
        boundary_penalty += max(0.0, r - wall_dist)
        # A negative radius is itself a violation.
        boundary_penalty += max(0.0, -r)

    for i in range(n):
        for j in range(i + 1, n):
            dist = np.sqrt(np.sum((centers[i] - centers[j]) ** 2))
            overlap_penalty += max(0.0, (radii[i] + radii[j]) - dist)

    return float(overlap_penalty), float(boundary_penalty)


def run_with_timeout(program_path, timeout_seconds=30):
    """
    Run `run_packing()` from program_path in a fresh subprocess with a timeout.

    Returns (centers, radii, reported_sum). The third value is whatever the
    program CLAIMS its sum is (may be a lie -- that's the point of some modes).
    """
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        script = f"""
import sys, os, pickle, traceback
import numpy as np
sys.path.insert(0, os.path.dirname({program_path!r}))
try:
    import importlib.util
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
        process = subprocess.Popen(
            [sys.executable, temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            if process.returncode != 0:
                if stderr:
                    print(f"Subprocess stderr: {stderr.decode()}")
                raise RuntimeError(f"Process exited with code {process.returncode}")
            if not os.path.exists(results_path):
                raise RuntimeError("Results file not found")
            with open(results_path, "rb") as f:
                results = pickle.load(f)
            if "error" in results:
                raise RuntimeError(f"Program execution failed: {results['error']}")
            return results["centers"], results["radii"], results["sum_radii"]
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise TimeoutError(f"Process timed out after {timeout_seconds} seconds")
    finally:
        for p in (temp_file_path, results_path):
            if os.path.exists(p):
                os.unlink(p)


def _zero_metrics(eval_time, error=None):
    # Numeric-only metrics (plus an optional 'error' string on failure, matching
    # the upstream example). The active score_mode is logged, not returned, so a
    # full evolution run never carries a non-numeric feature.
    m = {
        "combined_score": 0.0,
        "sum_radii": 0.0,
        "reported_sum": 0.0,
        "validity": 0.0,
        "overlap_penalty": 0.0,
        "boundary_penalty": 0.0,
        "eval_time": float(eval_time),
    }
    if error is not None:
        m["error"] = str(error)
    return m


def evaluate(program_path):
    """Single scoring path (no cascade stages). Returns a metrics dict."""
    n, score_mode, overlap_weight, boundary_weight = _config()
    start_time = time.time()

    try:
        centers, radii, reported_sum = run_with_timeout(program_path, timeout_seconds=30)
    except Exception as e:
        print(f"Evaluation failed to run program: {e}")
        return _zero_metrics(time.time() - start_time, error=e)

    centers = np.asarray(centers, dtype=float)
    radii = np.asarray(radii, dtype=float)

    # Shape check. A wrong shape means we cannot score geometry at all.
    if centers.shape != (n, 2) or radii.shape != (n,):
        print(f"Invalid shapes: centers={centers.shape}, radii={radii.shape}, expected n={n}")
        m = _zero_metrics(time.time() - start_time, error="invalid shapes")
        # intentionally_bad still rewards the reported value even here.
        if score_mode == "intentionally_bad_reported_sum":
            m["reported_sum"] = float(reported_sum)
            m["combined_score"] = float(reported_sum)
        return m

    valid = validate_packing(centers, radii)
    actual_sum = float(np.sum(radii))
    overlap_penalty, boundary_penalty = compute_penalties(centers, radii)
    eval_time = time.time() - start_time

    if score_mode == "hard_valid_sum":
        combined_score = actual_sum if valid else 0.0

    elif score_mode == "soft_penalty":
        combined_score = (
            float(reported_sum)
            - overlap_weight * overlap_penalty
            - boundary_weight * boundary_penalty
        )

    elif score_mode == "intentionally_bad_reported_sum":
        # No validation on purpose: trust whatever the program reports.
        combined_score = float(reported_sum)

    else:
        raise ValueError(f"Unknown SCORE_MODE: {score_mode!r}")

    metrics = {
        "combined_score": float(combined_score),
        "sum_radii": float(actual_sum),        # honest, recomputed from radii
        "reported_sum": float(reported_sum),   # what the program claimed
        "validity": 1.0 if valid else 0.0,
        "overlap_penalty": float(overlap_penalty),
        "boundary_penalty": float(boundary_penalty),
        "eval_time": float(eval_time),
    }
    # Reference ratio is display-only and meaningful only for n == 26.
    if n == 26:
        metrics["reference_ratio"] = float(actual_sum / REFERENCE_VALUE_N26)

    print(
        f"Evaluation: mode={score_mode}, valid={valid}, actual_sum={actual_sum:.6f}, "
        f"reported_sum={float(reported_sum):.6f}, combined_score={combined_score:.6f}, "
        f"overlap={overlap_penalty:.4f}, boundary={boundary_penalty:.4f}, time={eval_time:.2f}s"
    )
    return metrics


if __name__ == "__main__":
    # Quick manual check: python evaluator.py <program.py>
    path = sys.argv[1] if len(sys.argv) > 1 else "initial_program.py"
    import json

    print(json.dumps(evaluate(path), indent=2))
