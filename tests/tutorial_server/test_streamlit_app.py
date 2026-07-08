from pathlib import Path


def test_auto_refresh_is_opt_in_by_default():
    source = Path("tutorial/server/streamlit_app.py").read_text()

    assert 'st.sidebar.checkbox("Auto refresh", value=False' in source
