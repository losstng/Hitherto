from backend.routers import notebook


def test_new_session_and_shutdown():
    resp = notebook.new_session()
    assert resp.success is True
    sid = resp.data["session_id"]
    assert sid in notebook.SESSIONS
    shutdown = notebook.shutdown_session(sid)
    assert shutdown.success is True


def test_list_and_save_file():
    resp1 = notebook.new_session()
    sid1 = resp1.data["session_id"]
    notebook.save_notebook(sid1, notebook.NotebookPayload(notebook={"cells": []}))
    notebook.shutdown_session(sid1)

    resp2 = notebook.new_session()
    sid2 = resp2.data["session_id"]
    notebook.save_file(sid2, notebook.NotebookPayload(notebook={"cells": []}))
    notebook.shutdown_session(sid2)

    lst = notebook.list_notebooks()
    assert lst.success is True
    names = lst.data
    assert names[0] == sid2
    assert names[1] == sid1


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



def test_load_invalid_json(tmp_path):
    bad = notebook.NOTEBOOK_DIR / "bad.ipynb"
    bad.write_text("not json")
    resp = notebook.load_file("bad")
    assert resp.success is True
    assert resp.data is None
    bad.unlink()

    empty = notebook.NOTEBOOK_DIR / "empty.ipynb"
    empty.write_text("")
    resp2 = notebook.load_file("empty")
    assert resp2.success is True
    assert resp2.data is None
    empty.unlink()


