from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st

from tutorial_server.checkpoints import (
    best_source,
    checkpoint_history,
    execute_program,
    latest_stable_checkpoint,
    log_tail,
    score_column,
)
from tutorial_server.job_manager import DashboardSettings, JobManager, JobStatus, summarize_jobs
from tutorial_server.problems import (
    CIRCLE_N_OPTIONS,
    CIRCLE_SCORE_MODES,
    ITERATION_OPTIONS,
    MAX_TOKEN_OPTIONS,
    NOISO_N_OPTIONS,
    NOISO_SCORE_MODES,
    PROMPT_STYLES,
    TSP_N_OPTIONS,
    TSP_SCORE_MODES,
    DashboardParams,
    problem_environment,
)


st.set_page_config(page_title="OpenEvolve Tutorial", layout="wide")


@st.cache_resource
def get_manager() -> JobManager:
    return JobManager()


def health_check(settings: DashboardSettings) -> tuple[bool, str]:
    url = settings.api_base.rstrip("/") + "/models"
    try:
        response = requests.get(url, timeout=2)
        if response.ok:
            models = response.json().get("data", [])
            names = [model.get("id", "?") for model in models]
            return True, ", ".join(names) or "reachable"
        return False, response.text[-500:]
    except Exception as exc:
        return False, repr(exc)


def output_dir(job) -> Path:
    return job.run_dir / "openevolve_output"


def visualization_env(settings: DashboardSettings, params: DashboardParams) -> dict[str, str]:
    env = problem_environment(params)
    if settings.pydeps_path is not None:
        existing = os.environ.get("PYTHONPATH", "")
        parts = [str(settings.pydeps_path)]
        if existing:
            parts.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def plot_circle(data: dict, title: str):
    centers = np.asarray(data["centers"], dtype=float)
    radii = np.asarray(data["radii"], dtype=float)
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.set_aspect("equal")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, linewidth=2))
    for (x, y), r in zip(centers, radii):
        ax.add_patch(plt.Circle((x, y), r, fill=False, linewidth=1.3))
        ax.plot([x], [y], marker=".", markersize=3)
    ax.set_title(title)
    ax.grid(True, alpha=0.2)
    return fig


def plot_tsp(data: dict, title: str):
    cities = np.asarray(data["cities"], dtype=float)
    tour = np.asarray(data["tour"], dtype=int)
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.scatter(cities[:, 0], cities[:, 1], s=24)
    for idx, (x, y) in enumerate(cities):
        ax.text(x, y, str(idx), fontsize=7, ha="center", va="bottom")
    if len(tour) == len(cities) and np.all((0 <= tour) & (tour < len(cities))):
        ordered = cities[tour]
        closed = np.vstack([ordered, ordered[:1]])
        ax.plot(closed[:, 0], closed[:, 1], linewidth=1.4)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title)
    ax.grid(True, alpha=0.2)
    return fig


def plot_noiso(data: dict, title: str):
    grid_n = int(data["grid_n"])
    selected_points = np.asarray(data["selected_points"], dtype=int)
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    all_points = np.array([(x, y) for x in range(grid_n) for y in range(grid_n)], dtype=int)
    ax.scatter(all_points[:, 0], all_points[:, 1], s=18, color="#d0d0d0", label="grid")
    if selected_points.size:
        selected_points = selected_points.reshape((-1, 2))
        ax.scatter(selected_points[:, 0], selected_points[:, 1], s=48, color="#1f77b4", label="selected")
        for idx, (x, y) in enumerate(selected_points):
            ax.text(x, y + 0.08, str(idx), fontsize=7, ha="center", va="bottom")
    ax.set_xlim(-0.5, grid_n - 0.5)
    ax.set_ylim(-0.5, grid_n - 0.5)
    ax.set_xticks(range(grid_n))
    ax.set_yticks(range(grid_n))
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")
    ax.set_title(title)
    return fig


def plot_solution(problem_type: str, data: dict, title: str):
    if problem_type == "tsp":
        return plot_tsp(data, title)
    if problem_type == "no_isosceles":
        return plot_noiso(data, title)
    return plot_circle(data, title)


def render_submit_form(manager: JobManager):
    st.subheader("Submit Job")
    with st.form("submit-job", clear_on_submit=False):
        participant = st.text_input("Participant name or id", value="guest")
        problem_type = st.selectbox("Problem", ["circle_packing", "tsp", "no_isosceles"])

        common_left, common_mid, common_right = st.columns(3)
        with common_left:
            iterations = st.selectbox("Iterations", ITERATION_OPTIONS, index=ITERATION_OPTIONS.index(2))
            prompt_style = st.selectbox("Prompt style", PROMPT_STYLES, index=PROMPT_STYLES.index("balanced"))
        with common_mid:
            temperature = st.slider("Temperature", min_value=0.1, max_value=1.2, value=0.4, step=0.1)
            max_tokens = st.selectbox("Max tokens", MAX_TOKEN_OPTIONS, index=MAX_TOKEN_OPTIONS.index(1536))
        with common_right:
            visualization_timeout = st.number_input("Visualization timeout", min_value=5, max_value=300, value=90, step=5)

        packing_n = 16
        score_mode = "actual_sum_minus_penalty"
        tsp_n = 20
        tsp_seed = 0
        tsp_score_mode = "negative_length"
        noiso_n = 8
        noiso_score_mode = "size_minus_penalty"

        st.caption("Problem-specific options")
        if problem_type == "circle_packing":
            left, right = st.columns(2)
            with left:
                custom_n = st.checkbox("Custom circle count")
                if custom_n:
                    packing_n = st.number_input("PACKING_N", min_value=4, max_value=40, value=16, step=1)
                else:
                    packing_n = st.selectbox("PACKING_N", CIRCLE_N_OPTIONS, index=CIRCLE_N_OPTIONS.index(16))
            with right:
                score_mode = st.selectbox("Score mode", CIRCLE_SCORE_MODES, index=CIRCLE_SCORE_MODES.index("actual_sum_minus_penalty"))
        elif problem_type == "tsp":
            left, mid, right = st.columns(3)
            with left:
                custom_n = st.checkbox("Custom TSP city count")
                if custom_n:
                    tsp_n = st.number_input("TSP_N", min_value=5, max_value=80, value=20, step=1)
                else:
                    tsp_n = st.selectbox("TSP_N", TSP_N_OPTIONS, index=TSP_N_OPTIONS.index(20))
            with mid:
                tsp_seed = st.number_input("TSP_SEED", min_value=0, max_value=100000, value=0, step=1)
            with right:
                tsp_score_mode = st.selectbox("Score mode", TSP_SCORE_MODES, index=TSP_SCORE_MODES.index("negative_length"))
        else:
            left, right = st.columns(2)
            with left:
                custom_n = st.checkbox("Custom grid size")
                if custom_n:
                    noiso_n = st.number_input("NOISO_N", min_value=4, max_value=14, value=8, step=1)
                else:
                    noiso_n = st.selectbox("NOISO_N", NOISO_N_OPTIONS, index=NOISO_N_OPTIONS.index(8))
            with right:
                noiso_score_mode = st.selectbox("Score mode", NOISO_SCORE_MODES, index=NOISO_SCORE_MODES.index("size_minus_penalty"))

        submitted = st.form_submit_button("Start OpenEvolve")

    if submitted:
        params = DashboardParams(
            problem_type=problem_type,
            iterations=int(iterations),
            temperature=float(temperature),
            max_tokens=int(max_tokens),
            prompt_style=prompt_style,
            packing_n=int(packing_n),
            score_mode=score_mode,
            tsp_n=int(tsp_n),
            tsp_seed=int(tsp_seed),
            tsp_score_mode=tsp_score_mode,
            noiso_n=int(noiso_n),
            noiso_score_mode=noiso_score_mode,
            visualization_timeout=int(visualization_timeout),
        )
        try:
            job = manager.submit(participant, params)
            st.success(f"Queued job {job.id}")
        except Exception as exc:
            st.error(str(exc))


def render_job_list(manager: JobManager):
    jobs = manager.jobs()
    st.subheader("Jobs")
    if not jobs:
        st.info("No jobs submitted yet.")
        return None
    rows = summarize_jobs(jobs)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    labels = [f"{job.id} | {job.participant} | {job.params.problem_type} | {job.status.value}" for job in jobs]
    selected_label = st.selectbox("Inspect job", labels)
    selected_id = selected_label.split(" | ", 1)[0]
    return manager.get_job(selected_id)


def render_history(job):
    history = checkpoint_history(output_dir(job))
    if not history:
        st.info("No stable checkpoint yet. The first checkpoint appears after the first LLM generation and evaluation finish.")
        return
    df = pd.DataFrame(history)
    st.dataframe(df.tail(10), use_container_width=True, hide_index=True)
    column = score_column(job.params.problem_type, history)
    if column:
        plot_df = df[["current_iteration", column]].set_index("current_iteration")
        st.line_chart(plot_df)


def render_visualization(manager: JobManager, job):
    checkpoint = latest_stable_checkpoint(output_dir(job))
    if checkpoint is None:
        return
    env = visualization_env(manager.settings, job.params)
    try:
        data = execute_program(
            checkpoint.program_path,
            env=env,
            problem_type=job.params.problem_type,
            timeout=job.params.visualization_timeout,
        )
        fig = plot_solution(job.params.problem_type, data, f"Best {job.params.problem_type} at checkpoint {checkpoint.number}")
        st.pyplot(fig)
        plt.close(fig)
    except Exception as exc:
        st.warning(f"Could not render best_program.py: {exc}")


def render_job_detail(manager: JobManager, job):
    st.subheader("Selected Job")
    status_cols = st.columns(5)
    status_cols[0].metric("Status", job.status.value)
    status_cols[1].metric("Queue position", manager.queue_position(job.id) or "-")
    status_cols[2].metric("Iterations", job.params.iterations)
    status_cols[3].metric("Elapsed seconds", f"{job.elapsed_seconds:.1f}")
    status_cols[4].metric("Problem", job.params.problem_type)

    if job.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
        if st.button("Cancel selected job"):
            manager.cancel(job.id)
            st.rerun()

    st.caption(f"Run directory: {job.run_dir}")
    st.caption(f"OpenEvolve output: {output_dir(job)}")

    left, right = st.columns([1.05, 0.95])
    with left:
        render_history(job)
        render_visualization(manager, job)
    with right:
        st.markdown("**Recent subprocess output**")
        st.code("\n".join(job.recent_output[-30:]) or "(no stdout captured yet)", language="text")
        tail = log_tail(output_dir(job), limit=4000)
        with st.expander("OpenEvolve log tail", expanded=False):
            st.code(tail or "(no log file yet)", language="text")
        source = best_source(output_dir(job))
        with st.expander("Best source code", expanded=False):
            st.code(source or "(no stable best_program.py yet)", language="python")


def main():
    manager = get_manager()
    settings = manager.settings

    st.title("OpenEvolve Tutorial Dashboard")
    st.caption("Server fallback: OpenEvolve and Ollama run on the server; participants use only this browser UI.")

    if st.sidebar.button("Refresh now"):
        st.rerun()

    if st.sidebar.checkbox("Auto refresh", value=False, key="auto_refresh"):
        seconds = st.sidebar.slider("Refresh seconds", min_value=3, max_value=30, value=5)
        st.sidebar.caption("Keep this off while filling the submit form.")
        st.sidebar.markdown(f"<meta http-equiv='refresh' content='{seconds}'>", unsafe_allow_html=True)

    ok, payload = health_check(settings)
    st.sidebar.subheader("Server")
    st.sidebar.write("Ollama:", "OK" if ok else "Unavailable")
    st.sidebar.caption(payload)
    st.sidebar.write("Model:", settings.model)
    st.sidebar.write("Max active jobs:", settings.max_active_jobs)
    st.sidebar.write("Run root:", str(settings.run_root))
    st.sidebar.write("OpenEvolve command:", " ".join(settings.open_evolve_cmd))

    counts = manager.counts()
    count_cols = st.columns(5)
    for col, key in zip(count_cols, ["queued", "running", "completed", "failed", "cancelled"]):
        col.metric(key, counts.get(key, 0))

    form_col, jobs_col = st.columns([0.95, 1.25])
    with form_col:
        render_submit_form(manager)
    with jobs_col:
        selected_job = render_job_list(manager)

    if selected_job is not None:
        render_job_detail(manager, selected_job)


if __name__ == "__main__":
    main()
