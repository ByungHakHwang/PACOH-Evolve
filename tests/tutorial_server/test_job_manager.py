from pathlib import Path

import pytest

from tutorial_server.job_manager import DashboardSettings, JobManager, JobStatus
from tutorial_server.problems import DashboardParams


def make_manager(tmp_path):
    settings = DashboardSettings(
        run_root=tmp_path / "runs",
        open_evolve_cmd=("openevolve-run",),
        api_base="http://localhost:11434/v1",
        model="gpt-oss:20b",
        max_active_jobs=1,
        per_user_queued_jobs=1,
        pydeps_path=tmp_path / "pydeps",
    )
    return JobManager(settings=settings, autostart=False)


def test_submit_creates_queued_job_and_problem_files(tmp_path):
    manager = make_manager(tmp_path)
    params = DashboardParams(problem_type="circle_packing", packing_n=16, iterations=3)

    job = manager.submit("alice", params)

    assert job.status == JobStatus.QUEUED
    assert manager.queue_position(job.id) == 1
    assert job.problem_files.initial_program.exists()
    assert job.problem_files.evaluator.exists()
    assert job.problem_files.config.exists()


def test_build_command_contains_openevolve_arguments_and_problem_env(tmp_path):
    manager = make_manager(tmp_path)
    params = DashboardParams(problem_type="tsp", tsp_n=20, tsp_seed=7, tsp_score_mode="negative_length")
    job = manager.submit("bob", params)

    cmd, env = manager.build_command(job)

    assert cmd[0] == "openevolve-run"
    assert str(job.problem_files.initial_program) in cmd
    assert str(job.problem_files.evaluator) in cmd
    assert "--api-base" in cmd
    assert "http://localhost:11434/v1" in cmd
    assert "--primary-model" in cmd
    assert "gpt-oss:20b" in cmd
    assert env["TSP_N"] == "20"
    assert env["TSP_SEED"] == "7"
    assert env["OPENAI_API_KEY"] == "ollama"
    assert str(manager.settings.pydeps_path) in env["PYTHONPATH"]


def test_per_user_queued_job_limit_is_enforced(tmp_path):
    manager = make_manager(tmp_path)
    params = DashboardParams(problem_type="no_isosceles", noiso_n=8)

    manager.submit("alice", params)
    with pytest.raises(ValueError, match="already has a queued or running job"):
        manager.submit("alice", params)


def test_cancel_queued_job(tmp_path):
    manager = make_manager(tmp_path)
    job = manager.submit("alice", DashboardParams(problem_type="circle_packing"))

    assert manager.cancel(job.id)
    assert manager.get_job(job.id).status == JobStatus.CANCELLED


def test_cancel_running_job_does_not_wait_while_holding_lock(tmp_path, monkeypatch):
    manager = make_manager(tmp_path)
    job = manager.submit("alice", DashboardParams(problem_type="circle_packing"))

    class SlowProcess:
        pid = 123456

        def poll(self):
            return None

        def wait(self, timeout=None):
            raise AssertionError("cancel should not wait for process termination")

    with manager._condition:
        manager._pending.clear()
        job.status = JobStatus.RUNNING
        job.process = SlowProcess()

    signals = []
    monkeypatch.setattr("os.killpg", lambda pid, sig: signals.append((pid, sig)))

    assert manager.cancel(job.id)
    assert manager.get_job(job.id).status == JobStatus.CANCELLING
    assert signals
