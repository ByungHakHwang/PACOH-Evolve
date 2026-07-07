import importlib.util
import os
from pathlib import Path

import pytest

from tutorial_server.problems import DashboardParams, create_problem_files, problem_environment


def load_evaluator(path: Path):
    spec = importlib.util.spec_from_file_location("tutorial_evaluator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_env(monkeypatch, updates):
    for key, value in updates.items():
        monkeypatch.setenv(key, value)


@pytest.mark.parametrize(
    "params,validity_key,bad_metric",
    [
        (
            DashboardParams(problem_type="circle_packing", packing_n=10, score_mode="actual_sum_minus_penalty"),
            "validity",
            "overlap_penalty",
        ),
        (
            DashboardParams(problem_type="tsp", tsp_n=12, tsp_seed=3, tsp_score_mode="negative_length"),
            "validity",
            "duplicate_count",
        ),
        (
            DashboardParams(problem_type="no_isosceles", noiso_n=6, noiso_score_mode="size_minus_penalty"),
            "validity",
            "isosceles_count",
        ),
    ],
)
def test_problem_files_evaluate_seed_and_hacked_programs(tmp_path, monkeypatch, params, validity_key, bad_metric):
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
    assert hacked_metrics[validity_key] == 0.0 or hacked_metrics[bad_metric] > 0


def test_circle_packing_config_uses_raw_score_language(tmp_path):
    params = DashboardParams(problem_type="circle_packing", packing_n=26, score_mode="actual_sum_minus_penalty")
    files = create_problem_files(tmp_path, params, model_alias="gpt-oss:20b", api_base="http://localhost:11434/v1")
    config = files.config.read_text()

    assert "2.635" not in config
    assert "Optimize both centers and radii" in config
    assert 'primary_model: "gpt-oss:20b"' in config


def test_problem_environment_contains_only_selected_problem_keys():
    params = DashboardParams(problem_type="tsp", tsp_n=30, tsp_seed=11, tsp_score_mode="soft_penalty")

    assert problem_environment(params) == {
        "TSP_N": "30",
        "TSP_SEED": "11",
        "TSP_SCORE_MODE": "soft_penalty",
    }
