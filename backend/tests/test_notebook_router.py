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


def test_rename_and_delete():
    resp = notebook.new_session()
    assert resp.success is True
    sid = resp.data["session_id"]
    notebook.save_notebook(sid, notebook.NotebookPayload(notebook={"cells": []}))

    rename = notebook.rename_file(sid, notebook.RenamePayload(new_name="test1"))
    assert rename.success is True
    assert not (notebook.NOTEBOOK_DIR / f"{sid}.ipynb").exists()
    assert (notebook.NOTEBOOK_DIR / "test1.ipynb").exists()

    delete = notebook.delete_file("test1")
    assert delete.success is True
    assert not (notebook.NOTEBOOK_DIR / "test1.ipynb").exists()

    notebook.shutdown_session(sid)


def test_variable_filtering():
    resp = notebook.new_session()
    assert resp.success is True
    sid = resp.data["session_id"]

    # define a variable inside the session
    notebook.execute_cell(sid, notebook.ExecutePayload(cellId="c1", code="pd = 1"))
    vars_resp = notebook.get_variables(sid)
    assert vars_resp.success is True
    data = vars_resp.data
    assert data == {"pd": "1"}

    notebook.shutdown_session(sid)

