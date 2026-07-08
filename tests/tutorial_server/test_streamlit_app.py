from pathlib import Path


def test_auto_refresh_is_opt_in_by_default():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    assert 'st.sidebar.checkbox("Auto refresh", value=False' in source


def test_problem_choice_controls_submit_form_contents():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    form_index = source.index('with st.form("submit-job"')
    participant_index = source.index('st.text_input("Participant name or id"')
    problem_index = source.index('st.selectbox("Problem"')

    assert participant_index < form_index
    assert problem_index < form_index
    assert '"facility_location"' in source


def test_manual_size_labels_name_the_parameter():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    assert 'st.checkbox("Enter PACKING_N manually")' in source
    assert 'st.checkbox("Enter TSP_N manually")' in source
    assert 'st.checkbox("Enter NOISO_N manually")' in source
    assert 'st.checkbox("Enter FACILITY_N manually")' in source
    assert 'st.checkbox("Enter FACILITY_K manually")' in source
    assert "Custom circle count" not in source
    assert "Custom TSP city count" not in source
    assert "Custom grid size" not in source


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
