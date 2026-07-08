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
