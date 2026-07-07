"""
LLM-free verification for the tutorial evaluator + config.

Run with the OpenEvolve venv python:
    openevolve/.venv/bin/python tutorial/circle_packing/verify_evaluator.py

It checks the parts that had the Critical bug, WITHOUT needing Ollama:
  1. Scoring logic across the 3 score modes on a good seed and a cheating program.
  2. config_tutorial.yaml parses, cascade is OFF, and api_key propagates to models.
  3. The REAL OpenEvolve Evaluator path (config -> Evaluator -> _direct_evaluate ->
     our evaluate()) returns the RAW sum as combined_score (proves the fix end to
     end, minus the LLM mutation half).
"""
import asyncio
import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INITIAL = HERE / "initial_program.py"
HACKED = HERE / "hacked_program.py"
EVALUATOR = HERE / "evaluator.py"
CONFIG = HERE / "config_tutorial.yaml"

FAILS = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def load_evaluator():
    spec = importlib.util.spec_from_file_location("tutorial_evaluator", EVALUATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def score(ev, program_path, score_mode, **env):
    os.environ["SCORE_MODE"] = score_mode
    for k, v in env.items():
        os.environ[k] = str(v)
    return ev.evaluate(str(program_path))


def part1_scoring_logic():
    print("\n[1] Scoring logic (no LLM)")
    ev = load_evaluator()

    # --- The good seed under hard_valid_sum ---
    # NOTE: the seed's raw sum is ~0.96 (a low baseline, lots of headroom to
    # evolve toward the 2.635 reference). The 2.49996 in the doc's section 10 was
    # an EVOLVED result, not the seed.
    m = score(ev, INITIAL, "hard_valid_sum")
    raw = m["sum_radii"]
    print(f"      seed baseline raw sum_radii = {raw:.6f} (evolution target ~2.635)")
    check("seed is valid", m["validity"] == 1.0, f"validity={m['validity']}")
    check(
        "hard_valid_sum: combined_score == raw sum_radii (the RAW objective)",
        abs(m["combined_score"] - raw) < 1e-9,
        f"combined_score={m['combined_score']:.6f}, sum_radii={raw:.6f}",
    )
    # The whole point of the fix: the score is the raw sum, NOT sum/2.635.
    check(
        "NOT normalized (combined_score != sum/2.635)",
        abs(m["combined_score"] - raw / 2.635) > 1e-6,
        f"raw={m['combined_score']:.6f} vs normalized={raw / 2.635:.6f}",
    )
    check(
        "seed baseline is a plausible raw value (0.5..2.7)",
        0.5 < m["combined_score"] < 2.7,
        f"combined_score={m['combined_score']:.6f}",
    )

    # --- The cheating program under each mode ---
    h_hard = score(ev, HACKED, "hard_valid_sum")
    check(
        "hacked + hard_valid_sum -> score 0 (invalid geometry rejected)",
        h_hard["combined_score"] == 0.0 and h_hard["validity"] == 0.0,
        f"combined_score={h_hard['combined_score']}, validity={h_hard['validity']}",
    )

    h_bad = score(ev, HACKED, "intentionally_bad_reported_sum")
    check(
        "hacked + intentionally_bad -> score == reported lie (999)",
        abs(h_bad["combined_score"] - 999.0) < 1e-6,
        f"combined_score={h_bad['combined_score']}",
    )

    # soft_penalty subtracts continuous penalties but still TRUSTS reported_sum,
    # so with modest weights the 999 lie is only partly clawed back (999 - 325 =
    # 674). Teaching point: a soft, reported-value-based reward is still gameable;
    # only the validity gate (hard_valid_sum) fully rejects the cheat.
    h_soft = score(ev, HACKED, "soft_penalty")
    check(
        "hacked + soft_penalty -> penalized below the pure-lie score (999)",
        h_soft["combined_score"] < h_bad["combined_score"],
        f"soft={h_soft['combined_score']:.3f} < bad={h_bad['combined_score']:.3f}, "
        f"overlap={h_soft['overlap_penalty']:.2f}",
    )
    check(
        "soft_penalty is still gamed with weight 1.0 (stays high)",
        h_soft["combined_score"] > 100.0,
        f"combined_score={h_soft['combined_score']:.3f} (illustrates a weak reward)",
    )

    # soft_penalty on the VALID seed ~= reported_sum (penalties ~0).
    s_soft = score(ev, INITIAL, "soft_penalty")
    check(
        "soft_penalty on valid seed ~= reported_sum (no penalties)",
        abs(s_soft["combined_score"] - s_soft["reported_sum"]) < 1e-6,
        f"combined_score={s_soft['combined_score']:.6f}, reported={s_soft['reported_sum']:.6f}",
    )

    # --- returned metrics are numeric-only (safe for a full evolution run) ---
    nonnumeric = [k for k, v in m.items() if not isinstance(v, (int, float))]
    check("valid-run metrics are numeric-only", nonnumeric == [], f"offenders={nonnumeric}")


def part2_config():
    print("\n[2] config_tutorial.yaml parsing + routing")
    from openevolve.config import load_config

    cfg = load_config(str(CONFIG))
    check("cascade_evaluation is OFF", cfg.evaluator.cascade_evaluation is False,
          f"cascade_evaluation={cfg.evaluator.cascade_evaluation}")
    check("parallel_evaluations == 1", cfg.evaluator.parallel_evaluations == 1)
    check("num_islands == 1", cfg.database.num_islands == 1)

    models = cfg.llm.models
    check("exactly one LLM model (no zero-weight secondary)", len(models) == 1,
          f"models={[m.name for m in models]}")
    if models:
        mdl = models[0]
        check("model name is gpt-oss:20b", mdl.name == "gpt-oss:20b", f"name={mdl.name}")
        check("api_base propagated to model", mdl.api_base == "http://localhost:11434/v1",
              f"api_base={mdl.api_base}")
        check("api_key 'ollama' propagated to model (no env dependency)",
              mdl.api_key == "ollama", f"api_key={mdl.api_key!r}")


def part3_real_evaluator():
    print("\n[3] REAL OpenEvolve Evaluator path (config -> Evaluator -> evaluate())")
    from openevolve.config import load_config
    from openevolve.evaluator import Evaluator

    os.environ["SCORE_MODE"] = "hard_valid_sum"
    cfg = load_config(str(CONFIG))
    evaluator = Evaluator(cfg.evaluator, str(EVALUATOR), llm_ensemble=None)

    initial_code = INITIAL.read_text()
    metrics = asyncio.run(evaluator.evaluate_program(initial_code, program_id="verify"))

    check("engine returned a combined_score", "combined_score" in metrics)
    check("engine returned validity == 1.0", metrics.get("validity") == 1.0,
          f"validity={metrics.get('validity')}")
    csr = metrics.get("combined_score", 0.0)
    sr = metrics.get("sum_radii", 0.0)
    check(
        "engine combined_score == raw sum_radii (cascade OFF really uses evaluate())",
        abs(csr - sr) < 1e-9 and csr > 0.0,
        f"combined_score={csr:.6f}, sum_radii={sr:.6f}",
    )
    check(
        "engine did NOT normalize by 2.635 (proves stage funcs not used)",
        abs(csr - sr / 2.635) > 1e-6,
        f"raw={csr:.6f} vs normalized={sr / 2.635:.6f}",
    )


def main():
    print("=" * 68)
    print("Tutorial evaluator/config verification (LLM-free)")
    print("=" * 68)
    part1_scoring_logic()
    part2_config()
    part3_real_evaluator()

    print("\n" + "=" * 68)
    if FAILS:
        print(f"RESULT: FAILED ({len(FAILS)} check(s)): {', '.join(FAILS)}")
        sys.exit(1)
    print("RESULT: ALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
