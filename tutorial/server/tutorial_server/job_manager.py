from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterable

from .problems import DashboardParams, ProblemFiles, create_problem_files, problem_environment, problem_label


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CANCELLING = "cancelling"


@dataclass(frozen=True)
class DashboardSettings:
    run_root: Path
    open_evolve_cmd: tuple[str, ...]
    api_base: str = "http://localhost:11434/v1"
    model: str = "gpt-oss:20b"
    max_active_jobs: int = 3
    per_user_queued_jobs: int = 1
    openai_api_key: str = "ollama"
    pydeps_path: Path | None = None

    @classmethod
    def from_env(cls) -> "DashboardSettings":
        default_cmd = "/opt/openevolve/bin/openevolve-run" if Path("/opt/openevolve/bin/openevolve-run").exists() else "openevolve-run"
        cmd_text = os.environ.get("OPENEVOLVE_CMD", default_cmd)
        pydeps = os.environ.get("OPENEVOLVE_PYDEPS")
        return cls(
            run_root=Path(os.environ.get("OPENEVOLVE_RUN_ROOT", str(Path.home() / "openevolve_tutorial_runs"))),
            open_evolve_cmd=tuple(shlex.split(cmd_text)),
            api_base=os.environ.get("OPENEVOLVE_API_BASE", "http://localhost:11434/v1"),
            model=os.environ.get("OPENEVOLVE_MODEL", "gpt-oss:20b"),
            max_active_jobs=int(os.environ.get("OPENEVOLVE_MAX_ACTIVE_JOBS", "3")),
            per_user_queued_jobs=int(os.environ.get("OPENEVOLVE_PER_USER_QUEUED_JOBS", "1")),
            openai_api_key=os.environ.get("OPENAI_API_KEY", "ollama"),
            pydeps_path=Path(pydeps) if pydeps else None,
        )


@dataclass
class Job:
    id: str
    participant: str
    params: DashboardParams
    run_dir: Path
    problem_files: ProblemFiles
    status: JobStatus = JobStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    ended_at: float | None = None
    returncode: int | None = None
    error: str = ""
    recent_output: list[str] = field(default_factory=list)
    process: subprocess.Popen | None = field(default=None, repr=False, compare=False)

    @property
    def metadata_path(self) -> Path:
        return self.run_dir / "job_metadata.json"

    @property
    def elapsed_seconds(self) -> float:
        start = self.started_at or self.created_at
        end = self.ended_at or time.time()
        return max(0.0, end - start)


def safe_slug(value: str, fallback: str = "participant") -> str:
    chars = []
    for char in value.strip().lower():
        if char.isalnum():
            chars.append(char)
        elif char in ("-", "_", ".", " "):
            chars.append("-")
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:40] or fallback


class JobManager:
    def __init__(self, settings: DashboardSettings | None = None, autostart: bool = True):
        self.settings = settings or DashboardSettings.from_env()
        self.settings.run_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._jobs: dict[str, Job] = {}
        self._pending: deque[str] = deque()
        self._workers: list[threading.Thread] = []
        if autostart:
            for index in range(max(1, self.settings.max_active_jobs)):
                worker = threading.Thread(target=self._worker_loop, name=f"openevolve-worker-{index+1}", daemon=True)
                worker.start()
                self._workers.append(worker)

    def submit(self, participant: str, params: DashboardParams) -> Job:
        participant_slug = safe_slug(participant)
        with self._condition:
            active_for_user = [
                job
                for job in self._jobs.values()
                if safe_slug(job.participant) == participant_slug and job.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.CANCELLING}
            ]
            if len(active_for_user) >= self.settings.per_user_queued_jobs:
                raise ValueError(f"{participant_slug} already has a queued or running job")

            job_id = uuid.uuid4().hex[:10]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = self.settings.run_root / f"{participant_slug}_{problem_label(params)}_{timestamp}_{job_id}"
            problem_dir = run_dir / "problem"
            problem_files = create_problem_files(problem_dir, params, model_alias=self.settings.model, api_base=self.settings.api_base)
            job = Job(
                id=job_id,
                participant=participant_slug,
                params=params,
                run_dir=run_dir,
                problem_files=problem_files,
            )
            self._jobs[job_id] = job
            self._pending.append(job_id)
            self._write_metadata_unlocked(job)
            self._condition.notify()
            return job

    def get_job(self, job_id: str) -> Job:
        with self._lock:
            return self._jobs[job_id]

    def jobs(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    def queue_position(self, job_id: str) -> int | None:
        with self._lock:
            try:
                return list(self._pending).index(job_id) + 1
            except ValueError:
                return None

    def counts(self) -> dict[str, int]:
        with self._lock:
            return {status.value: sum(1 for job in self._jobs.values() if job.status == status) for status in JobStatus}

    def cancel(self, job_id: str) -> bool:
        with self._condition:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.status == JobStatus.QUEUED:
                self._pending = deque(item for item in self._pending if item != job_id)
                job.status = JobStatus.CANCELLED
                job.ended_at = time.time()
                self._write_metadata_unlocked(job)
                self._condition.notify_all()
                return True
            if job.status == JobStatus.RUNNING and job.process is not None:
                job.status = JobStatus.CANCELLING
                self._terminate_process(job.process)
                self._write_metadata_unlocked(job)
                return True
            return False

    def build_command(self, job: Job) -> tuple[list[str], dict[str, str]]:
        cmd = [
            *self.settings.open_evolve_cmd,
            str(job.problem_files.initial_program),
            str(job.problem_files.evaluator),
            "--config",
            str(job.problem_files.config),
            "--iterations",
            str(job.params.iterations),
            "--output",
            str(job.run_dir / "openevolve_output"),
            "--api-base",
            self.settings.api_base,
            "--primary-model",
            self.settings.model,
            "--log-level",
            "INFO",
        ]
        env = os.environ.copy()
        env.update(problem_environment(job.params))
        env["OPENAI_API_KEY"] = self.settings.openai_api_key
        if self.settings.pydeps_path is not None:
            existing = env.get("PYTHONPATH", "")
            parts = [str(self.settings.pydeps_path)]
            if existing:
                parts.append(existing)
            env["PYTHONPATH"] = os.pathsep.join(parts)
        return cmd, env

    def _worker_loop(self):
        while True:
            with self._condition:
                while not self._pending:
                    self._condition.wait()
                job_id = self._pending.popleft()
                job = self._jobs.get(job_id)
            if job is None:
                continue
            self._run_job(job)

    def _run_job(self, job: Job):
        with self._condition:
            if job.status == JobStatus.CANCELLED:
                return
            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            self._write_metadata_unlocked(job)
            self._condition.notify_all()

        cmd, env = self.build_command(job)
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                start_new_session=True,
            )
        except Exception as exc:
            with self._condition:
                job.status = JobStatus.FAILED
                job.error = str(exc)
                job.ended_at = time.time()
                self._write_metadata_unlocked(job)
                self._condition.notify_all()
            return

        with self._condition:
            job.process = process
            self._write_metadata_unlocked(job)

        assert process.stdout is not None
        for line in iter(process.stdout.readline, ""):
            with self._condition:
                job.recent_output.append(line.rstrip())
                job.recent_output = job.recent_output[-80:]
                self._write_metadata_unlocked(job)
        process.stdout.close()
        returncode = process.wait()

        with self._condition:
            job.returncode = returncode
            job.ended_at = time.time()
            job.process = None
            if job.status == JobStatus.CANCELLING:
                job.status = JobStatus.CANCELLED
            elif returncode == 0:
                job.status = JobStatus.COMPLETED
            else:
                job.status = JobStatus.FAILED
                job.error = f"OpenEvolve exited with code {returncode}"
            self._write_metadata_unlocked(job)
            self._condition.notify_all()

    def _write_metadata_unlocked(self, job: Job):
        job.run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": job.id,
            "participant": job.participant,
            "status": job.status.value,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "ended_at": job.ended_at,
            "returncode": job.returncode,
            "error": job.error,
            "run_dir": str(job.run_dir),
            "openevolve_output_dir": str(job.run_dir / "openevolve_output"),
            "problem_dir": str(job.problem_files.directory),
            "params": asdict(job.params),
            "recent_output": job.recent_output[-80:],
        }
        job.metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    @staticmethod
    def _terminate_process(process: subprocess.Popen):
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
        except ProcessLookupError:
            return
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=10)


def summarize_jobs(jobs: Iterable[Job]) -> list[dict[str, object]]:
    rows = []
    for job in jobs:
        rows.append(
            {
                "id": job.id,
                "participant": job.participant,
                "problem": job.params.problem_type,
                "score_mode": problem_label(job.params),
                "status": job.status.value,
                "iterations": job.params.iterations,
                "elapsed_s": round(job.elapsed_seconds, 1),
                "run_dir": str(job.run_dir),
            }
        )
    return rows
