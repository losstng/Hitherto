from backend.routers import notebook


def test_new_session_and_shutdown():
    resp = notebook.new_session()
    assert resp.success is True
    sid = resp.data["session_id"]
    assert sid in notebook.SESSIONS
    shutdown = notebook.shutdown_session(sid)
    assert shutdown.success is True

