from backend.routers import notebook


def test_new_session_and_shutdown():
    resp = notebook.new_session()
    assert resp.success is True
    sid = resp.data["session_id"]
    assert sid in notebook.SESSIONS
    shutdown = notebook.shutdown_session(sid)
    assert shutdown.success is True


def test_list_endpoint():
    resp = notebook.new_session()
    assert resp.success is True
    sid = resp.data["session_id"]

    # save empty notebook to create file
    notebook.save_notebook(sid, notebook.NotebookPayload(notebook={"cells": []}))
    lst = notebook.list_notebooks()
    assert lst.success is True
    assert sid in lst.data

    notebook.shutdown_session(sid)

