# agent-os-proxmox/tests/test_live.py
import os, tempfile
from store import store
def _db():
    d = tempfile.mkdtemp(); p = os.path.join(d, "t.db"); store.init_db(p); return p
def test_list_and_claim():
    db = _db()
    a = store.create_task("A", "mock", "hi", db=db)
    b = store.create_task("B", "mock", "ho", db=db)
    ts = store.list_tasks(db=db)
    assert [t["id"] for t in ts] == [b, a]
    assert store.claim_next(db=db) == a  # älteste zuerst
    assert store.claim_next(db=db) == b
    assert store.claim_next(db=db) is None
    d = store.task_detail(a, db=db)
    assert d["status"] == "running" and isinstance(d["run_ids"], list)
def test_run_files_lists(tmp_path):
    f = store.save_run_log_file(1, "hello", memdir=str(tmp_path))
    rows = store.list_run_files(memdir=str(tmp_path))
    assert len(rows) == 1 and rows[0]["preview"].startswith("hello")

def test_read_api(tmp_path, monkeypatch):
    import os
    import pathlib
    gw_path = str(pathlib.Path("agent-os-proxmox/gateway/app.py").resolve())
    monkeypatch.chdir(tmp_path)
    os.makedirs("data", exist_ok=True)
    from store import store as _st
    _st.init_db("data/app.db")
    import importlib.util
    spec = importlib.util.spec_from_file_location("gw2", gw_path)
    gw = importlib.util.module_from_spec(spec); spec.loader.exec_module(gw)
    from fastapi.testclient import TestClient
    c = TestClient(gw.app)
    assert c.get("/tasks").status_code == 401  # ohne Auth
    a = ("admin", "change-me")
    assert isinstance(c.get("/tasks", auth=a).json(), list)
    assert c.get("/tasks/999999", auth=a).status_code == 404
    assert c.get("/runs/999999/logs", auth=a).status_code == 404
    assert isinstance(c.get("/memory", auth=a).json(), list)
