from streamlit.testing.v1 import AppTest

def test_offline_ui_flow(monkeypatch, tmp_path):
    monkeypatch.setenv('FIXOPS_HISTORY_PATH', str(tmp_path / 'history.sqlite3'))
    at = AppTest.from_file('../app.py', default_timeout=30).run()
    assert not at.exception
    at.sidebar.selectbox[0].select('tfidf').run()
    at.text_area[0].input('HTTP 500 internal server error')
    at.button[0].click().run()
    assert not at.exception
    assert len(at.success) == 1
    assert any('RB-001' in e.label for e in at.expander)
    at.text_area[0].input('Write a wedding poem')
    at.button[0].click().run()
    assert not at.exception
    assert any('Insufficient' in w.value for w in at.warning)
