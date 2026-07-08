from pathlib import Path


def test_auto_refresh_is_opt_in_by_default():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    assert 'st.sidebar.checkbox("Auto refresh", value=False' in source
    assert "meta http-equiv" not in source
    assert "st_autorefresh" in source


def test_participant_id_is_not_shared_guest_default():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    assert 'st.text_input("Participant name or id", value=""' in source
    assert 'value="guest"' not in source
    assert "Please enter a participant id" in source


def test_problem_choice_controls_submit_form_contents():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    form_index = source.index('with st.form("submit-job"')
    participant_index = source.index('st.text_input("Participant name or id"')
    problem_index = source.index('st.selectbox("Problem"')

    assert participant_index < form_index
    assert problem_index < form_index
    assert '"facility_location"' in source


def test_manual_size_mode_is_not_exposed():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    for forbidden in [
        "manually",
        "custom_",
        "Custom circle count",
        "Custom TSP city count",
        "Custom grid size",
        'st.number_input("PACKING_N"',
        'st.number_input("TSP_N"',
        'st.number_input("NOISO_N"',
        'st.number_input("FACILITY_N"',
        'st.number_input("FACILITY_K"',
    ]:
        assert forbidden not in source


def test_facility_location_controls_are_available():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    assert "FACILITY_N_OPTIONS" in source
    assert "FACILITY_K_OPTIONS" in source
    assert "FACILITY_SCORE_MODES" in source
    assert 'st.number_input("FACILITY_SEED"' in source
    assert "facility_score_mode" in source


def test_recent_subprocess_output_is_brief():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    assert "job.recent_output[-8:]" in source
    assert "job.recent_output[-30:]" not in source


def test_selected_score_function_is_shown_below_best_source():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    best_source_index = source.index('st.expander("Best source code"')
    score_function_index = source.index('st.expander("Selected score function"')

    assert "score_function_preview" in source
    assert best_source_index < score_function_index
