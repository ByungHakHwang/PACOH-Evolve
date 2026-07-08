import importlib.util
import os
from pathlib import Path

import numpy as np
import pytest

from tutorial_server.problems import DashboardParams, ITERATION_OPTIONS, create_problem_files, problem_environment, score_function_preview


def load_evaluator(path: Path):
    spec = importlib.util.spec_from_file_location("tutorial_evaluator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_program(path: Path):
    spec = importlib.util.spec_from_file_location("tutorial_program", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_env(monkeypatch, updates):
    for key, value in updates.items():
        monkeypatch.setenv(key, value)


def assert_finite_metrics(metrics):
    for key, value in metrics.items():
        if isinstance(value, float):
            assert np.isfinite(value), (key, value, metrics)


def test_tutorial_iteration_options_allow_20_but_not_50():
    assert ITERATION_OPTIONS == (1, 2, 3, 5, 10, 20)


@pytest.mark.parametrize(
    "params_factory,validity_key,bad_metric",
    [
        (
            lambda: DashboardParams(problem_type="circle_packing", packing_n=10, score_mode="actual_sum_minus_penalty"),
            "validity",
            "overlap_penalty",
        ),
        (
            lambda: DashboardParams(problem_type="tsp", tsp_n=12, tsp_seed=3, tsp_score_mode="negative_length"),
            "validity",
            "duplicate_count",
        ),
        (
            lambda: DashboardParams(problem_type="no_isosceles", noiso_n=6, noiso_score_mode="size_minus_penalty"),
            "validity",
            "isosceles_count",
        ),
        (
            lambda: DashboardParams(
                problem_type="facility_location",
                facility_n=30,
                facility_k=4,
                facility_seed=2,
                facility_score_mode="mean_plus_max_distance",
            ),
            "validity",
            "boundary_penalty",
        ),
    ],
)
def test_problem_files_evaluate_seed_and_hacked_programs(tmp_path, monkeypatch, params_factory, validity_key, bad_metric):
    params = params_factory()
    files = create_problem_files(
        tmp_path,
        params,
        model_alias="gpt-oss:20b",
        api_base="http://localhost:11434/v1",
    )
    assert files.initial_program.exists()
    assert files.hacked_program.exists()
    assert files.evaluator.exists()
    assert files.config.exists()
    assert "cascade_evaluation: false" in files.config.read_text()
    assert "checkpoint_interval: 1" in files.config.read_text()

    apply_env(monkeypatch, problem_environment(params))
    evaluator = load_evaluator(files.evaluator)

    seed_metrics = evaluator.evaluate(str(files.initial_program))
    hacked_metrics = evaluator.evaluate(str(files.hacked_program))

    assert "combined_score" in seed_metrics
    assert seed_metrics[validity_key] == 1.0
    if params.problem_type == "tsp":
        assert hacked_metrics["validity"] == 1.0
        assert hacked_metrics["reported_length"] == -999.0
    else:
        assert hacked_metrics[validity_key] == 0.0 or hacked_metrics[bad_metric] > 0


def test_circle_packing_config_uses_raw_score_language(tmp_path):
    params = DashboardParams(problem_type="circle_packing", packing_n=26, score_mode="actual_sum_minus_penalty")
    files = create_problem_files(tmp_path, params, model_alias="gpt-oss:20b", api_base="http://localhost:11434/v1")
    config = files.config.read_text()

    assert "2.635" not in config
    assert "Optimize both centers and radii" in config
    assert 'primary_model: "gpt-oss:20b"' in config
    assert "diff_based_evolution: true" in config
    assert "allow_full_rewrites: false" in config


def test_circle_packing_seed_rewards_visible_center_spread(tmp_path, monkeypatch):
    params = DashboardParams(problem_type="circle_packing", packing_n=10, score_mode="actual_sum_minus_penalty")
    files = create_problem_files(tmp_path, params, model_alias="gpt-oss:20b", api_base="http://localhost:11434/v1")
    source = files.initial_program.read_text()
    prelude, evolve_block = source.split("# EVOLVE-BLOCK-START", 1)

    assert "WEAK_RADIUS_SCALE" not in source
    assert "import os" in prelude
    assert "import numpy as np" in prelude
    assert "os.environ" not in evolve_block
    assert "CENTER_SPREAD" in evolve_block

    apply_env(monkeypatch, problem_environment(params))
    program = load_program(files.initial_program)
    centers, radii, seed_sum = program.run_packing()
    wider_centers = program.initial_centers(params.packing_n, spread=0.70)
    wider_radii = program.compute_max_radii(wider_centers)

    center_motion = ((wider_centers - centers) ** 2).sum(axis=1) ** 0.5

    assert float(center_motion.max()) > 0.05
    assert float(wider_radii.sum()) > float(seed_sum) * 1.15
    assert float(seed_sum) == pytest.approx(float(radii.sum()))

    evaluator = load_evaluator(files.evaluator)
    seed_metrics = evaluator.evaluate(str(files.initial_program))
    assert seed_metrics["center_spread"] > 0.0
    assert seed_metrics["max_center_spread"] >= seed_metrics["center_spread"]


def test_facility_location_seed_has_clear_refinement_path(tmp_path, monkeypatch):
    params = DashboardParams(
        problem_type="facility_location",
        facility_n=50,
        facility_k=5,
        facility_seed=4,
        facility_score_mode="mean_plus_max_distance",
    )
    files = create_problem_files(tmp_path, params, model_alias="gpt-oss:20b", api_base="http://localhost:11434/v1")
    source = files.initial_program.read_text()

    assert "run_facility_location" in source
    assert "LLOYD_STEPS = 0" in source
    assert "lloyd_refine" in source

    apply_env(monkeypatch, problem_environment(params))
    program = load_program(files.initial_program)
    demand_points, facilities, reported_score = program.run_facility_location()
    refined = program.lloyd_refine(demand_points, facilities, steps=8)

    seed_distances = program.assignment_distances(demand_points, facilities)
    refined_distances = program.assignment_distances(demand_points, refined)
    facility_motion = np.linalg.norm(refined - facilities, axis=1)

    assert demand_points.shape == (params.facility_n, 2)
    assert facilities.shape == (params.facility_k, 2)
    assert float(facility_motion.max()) > 0.05
    assert float(refined_distances.mean()) < float(seed_distances.mean()) * 0.85
    assert float(reported_score) == pytest.approx(-float(seed_distances.mean()))

    evaluator = load_evaluator(files.evaluator)
    seed_metrics = evaluator.evaluate(str(files.initial_program))
    assert seed_metrics["validity"] == 1.0
    assert seed_metrics["mean_distance"] > 0.0
    assert seed_metrics["max_distance"] >= seed_metrics["mean_distance"]
    assert 0.0 <= seed_metrics["coverage_fraction"] <= 1.0


def test_problem_environment_contains_only_selected_problem_keys():
    params = DashboardParams(problem_type="tsp", tsp_n=30, tsp_seed=11, tsp_score_mode="soft_penalty")

    assert problem_environment(params) == {
        "TSP_N": "30",
        "TSP_SEED": "11",
        "TSP_SCORE_MODE": "soft_penalty",
    }


@pytest.mark.parametrize(
    "params,expected_header,expected_code,forbidden_code",
    [
        (
            DashboardParams(problem_type="circle_packing", packing_n=16, score_mode="actual_sum_minus_penalty"),
            "# SCORE_MODE=actual_sum_minus_penalty",
            "- 20.0 * overlap_penalty",
            "reported_sum = clamp_reported",
        ),
        (
            DashboardParams(problem_type="tsp", tsp_n=20, tsp_seed=5, tsp_score_mode="negative_length"),
            "# TSP_SCORE_MODE=negative_length",
            "-actual_length if valid else -1e6 - 1000.0 * violation_count",
            "reported_length = clamp_reported",
        ),
        (
            DashboardParams(problem_type="no_isosceles", noiso_n=8, noiso_score_mode="size_minus_penalty"),
            "# NOISO_SCORE_MODE=size_minus_penalty",
            "subset_size",
            "reported_size = clamp_reported",
        ),
        (
            DashboardParams(
                problem_type="facility_location",
                facility_n=50,
                facility_k=5,
                facility_seed=2,
                facility_score_mode="soft_coverage",
            ),
            "# FACILITY_SCORE_MODE=soft_coverage",
            "soft_coverage = float(np.mean",
            "reported_score = clamp_reported",
        ),
    ],
)
def test_score_function_preview_matches_selected_mode(params, expected_header, expected_code, forbidden_code):
    preview = score_function_preview(params)

    assert preview.startswith(f"# Problem: {params.problem_type}")
    assert expected_header in preview
    assert expected_code in preview
    assert forbidden_code not in preview


def test_facility_location_environment_contains_only_facility_keys():
    params = DashboardParams(
        problem_type="facility_location",
        facility_n=80,
        facility_k=6,
        facility_seed=13,
        facility_score_mode="soft_coverage",
    )

    assert problem_environment(params) == {
        "FACILITY_N": "80",
        "FACILITY_K": "6",
        "FACILITY_SEED": "13",
        "FACILITY_SCORE_MODE": "soft_coverage",
    }


def test_generated_evaluators_return_finite_worst_score_for_bad_outputs(tmp_path, monkeypatch):
    cases = [
        (
            DashboardParams(problem_type="circle_packing", packing_n=4, score_mode="actual_sum_minus_penalty"),
            """
import numpy as np
def run_packing():
    return np.full((4, 2), 0.5), np.full(4, np.inf), 1e309
""",
        ),
        (
            DashboardParams(problem_type="tsp", tsp_n=8, tsp_seed=2, tsp_score_mode="negative_length"),
            """
def run_tsp():
    return [[0.0, 0.0]], None, "bad"
""",
        ),
        (
            DashboardParams(problem_type="no_isosceles", noiso_n=6, noiso_score_mode="size_minus_penalty"),
            """
def run_no_isosceles():
    return "bad", object(), "bad"
""",
        ),
        (
            DashboardParams(
                problem_type="facility_location",
                facility_n=30,
                facility_k=4,
                facility_seed=1,
                facility_score_mode="mean_plus_max_distance",
            ),
            """
def run_facility_location():
    return [[0.0, 0.0]], [[float("inf"), 0.5]], "bad"
""",
        ),
    ]
    for index, (params, source) in enumerate(cases):
        files = create_problem_files(
            tmp_path / f"case_{index}",
            params,
            model_alias="gpt-oss:20b",
            api_base="http://localhost:11434/v1",
        )
        bad_program = files.directory / "bad_program.py"
        bad_program.write_text(source)
        apply_env(monkeypatch, problem_environment(params))
        evaluator = load_evaluator(files.evaluator)

        metrics = evaluator.evaluate(str(bad_program))

        assert metrics["combined_score"] < 0.0
        assert metrics["validity"] == 0.0
        assert_finite_metrics(metrics)


def test_reported_score_hacks_are_clamped_to_finite_values(tmp_path, monkeypatch):
    cases = [
        (
            DashboardParams(problem_type="circle_packing", packing_n=4, score_mode="intentionally_bad_reported_sum"),
            """
import numpy as np
def run_packing():
    centers = np.asarray([[0.2, 0.2], [0.8, 0.2], [0.2, 0.8], [0.8, 0.8]])
    radii = np.full(4, 0.1)
    return centers, radii, 1e308
""",
            "reported_sum",
        ),
        (
            DashboardParams(problem_type="tsp", tsp_n=8, tsp_seed=2, tsp_score_mode="intentionally_bad_reported_length"),
            """
import numpy as np
def run_tsp():
    rng = np.random.default_rng(2)
    return rng.random((8, 2)), np.arange(8), -1e308
""",
            "reported_length",
        ),
        (
            DashboardParams(problem_type="no_isosceles", noiso_n=6, noiso_score_mode="intentionally_bad_reported_size"),
            """
import numpy as np
def run_no_isosceles():
    return 6, np.asarray([[0, 0], [1, 0], [2, 0]]), 1e308
""",
            "reported_size",
        ),
        (
            DashboardParams(
                problem_type="facility_location",
                facility_n=30,
                facility_k=4,
                facility_seed=1,
                facility_score_mode="intentionally_bad_reported_score",
            ),
            """
import numpy as np
CLUSTER_CENTERS = np.asarray([[0.18, 0.22], [0.28, 0.78], [0.52, 0.50], [0.74, 0.24], [0.82, 0.78], [0.50, 0.86]])
CLUSTER_WEIGHTS = np.asarray([0.18, 0.16, 0.24, 0.14, 0.18, 0.10])
def run_facility_location():
    rng = np.random.default_rng(1)
    assignments = rng.choice(len(CLUSTER_CENTERS), size=30, p=CLUSTER_WEIGHTS / CLUSTER_WEIGHTS.sum())
    points = np.clip(CLUSTER_CENTERS[assignments] + rng.normal(0.0, 0.065, size=(30, 2)), 0.02, 0.98)
    return points, np.asarray([[0.2, 0.2], [0.3, 0.8], [0.7, 0.2], [0.8, 0.8]]), 1e308
""",
            "reported_score",
        ),
    ]
    for index, (params, source, reported_key) in enumerate(cases):
        files = create_problem_files(
            tmp_path / f"reported_{index}",
            params,
            model_alias="gpt-oss:20b",
            api_base="http://localhost:11434/v1",
        )
        program = files.directory / "reported_program.py"
        program.write_text(source)
        apply_env(monkeypatch, problem_environment(params))
        evaluator = load_evaluator(files.evaluator)

        metrics = evaluator.evaluate(str(program))

        assert abs(metrics[reported_key]) <= 1_000_000.0
        assert abs(metrics["combined_score"]) <= 1_000_000.0
        assert_finite_metrics(metrics)
