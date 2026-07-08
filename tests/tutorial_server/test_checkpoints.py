import json
import os
import time
from pathlib import Path

from tutorial_server.checkpoints import (
    checkpoint_history,
    execute_program,
    latest_stable_checkpoint,
    stable_checkpoints,
)
from tutorial_server.problems import DashboardParams, create_problem_files, problem_environment


def write_checkpoint(run_dir: Path, number: int, metrics: dict):
    checkpoint_dir = run_dir / "checkpoints" / f"checkpoint_{number}"
    checkpoint_dir.mkdir(parents=True)
    (checkpoint_dir / "best_program.py").write_text("def run_packing():\n    return [], [], 0.0\n")
    (checkpoint_dir / "best_program_info.json").write_text(
        json.dumps({"iteration": number - 1, "current_iteration": number, "metrics": metrics})
    )
    return checkpoint_dir


def test_stable_checkpoints_and_history_are_sorted(tmp_path):
    run_dir = tmp_path / "run"
    write_checkpoint(run_dir, 2, {"combined_score": 2.0, "validity": 1.0})
    write_checkpoint(run_dir, 1, {"combined_score": 1.0, "validity": 1.0})

    checkpoints = stable_checkpoints(run_dir, min_age_seconds=0)
    assert [item.number for item in checkpoints] == [1, 2]
    assert latest_stable_checkpoint(run_dir, min_age_seconds=0).number == 2

    history = checkpoint_history(run_dir)
    assert [row["checkpoint"] for row in history] == [1, 2]
    assert [row["combined_score"] for row in history] == [1.0, 2.0]


def test_stable_checkpoints_ignore_files_that_are_too_new(tmp_path):
    run_dir = tmp_path / "run"
    write_checkpoint(run_dir, 1, {"combined_score": 1.0})

    assert stable_checkpoints(run_dir, min_age_seconds=9999) == []


def test_execute_program_supports_all_problem_interfaces(tmp_path):
    cases = [
        DashboardParams(problem_type="circle_packing", packing_n=10),
        DashboardParams(problem_type="tsp", tsp_n=12, tsp_seed=5),
        DashboardParams(problem_type="no_isosceles", noiso_n=6),
        DashboardParams(problem_type="facility_location", facility_n=30, facility_k=4, facility_seed=7),
    ]
    for params in cases:
        problem_root = tmp_path / params.problem_type
        files = create_problem_files(problem_root, params, model_alias="gpt-oss:20b", api_base="http://localhost:11434/v1")
        env = os.environ.copy()
        env.update(problem_environment(params))

        data = execute_program(files.initial_program, env=env, problem_type=params.problem_type, timeout=10)

        if params.problem_type == "circle_packing":
            assert len(data["centers"]) == params.packing_n
            assert len(data["radii"]) == params.packing_n
        elif params.problem_type == "tsp":
            assert len(data["cities"]) == params.tsp_n
            assert len(data["tour"]) == params.tsp_n
        elif params.problem_type == "no_isosceles":
            assert data["grid_n"] == params.noiso_n
            assert len(data["selected_points"]) > 0
        else:
            assert len(data["demand_points"]) == params.facility_n
            assert len(data["facilities"]) == params.facility_k
