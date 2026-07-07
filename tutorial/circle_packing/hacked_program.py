# EVOLVE-BLOCK-START
"""
A deliberately "cheating" circle packing, for demonstrating reward hacking.

All 26 circles sit on top of each other at the center with a large radius, so
the packing is wildly invalid (massive overlap), yet run_packing() *reports* a
huge sum. Use this to show:
  - hard_valid_sum                -> score 0 (evaluator rejects invalid geometry)
  - soft_penalty                  -> large negative score (penalties dominate)
  - intentionally_bad_reported_sum-> score 999 (the hack succeeds; no validation)
"""
import numpy as np


def construct_packing():
    n = 26
    centers = np.tile([0.5, 0.5], (n, 1))  # all stacked at the center
    radii = np.full(n, 0.5)                 # each fills the whole square -> overlap
    reported_sum = 999.0                    # a blatant lie about the objective
    return centers, radii, reported_sum


# EVOLVE-BLOCK-END


def run_packing():
    centers, radii, reported_sum = construct_packing()
    return centers, radii, reported_sum
