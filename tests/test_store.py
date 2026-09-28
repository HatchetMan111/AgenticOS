# agent-os-proxmox/tests/test_store.py
import os, tempfile
from store import store

def test_create_and_status_and_redaction(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("data", exist_ok=True)
    store.init_db("data/app.db")
    d = tempfile.mkdtemp()
    db = os.path.join(d, "app.db")
    store.init_db(db)
    tid = store.create_task("T1", "mock", "hello sk-SECRET123")
    assert tid == 1
    store.set_status(tid, "running")
    rid = store.start_run(tid, "mock")
    store.append_log(rid, "key sk-SECRET123 sichtbar?")
    logs = store.get_logs(rid)
    assert "SECRET123" not in logs and "***" in logs
    p = store.save_run_log_file(rid, "ok")
    assert os.path.exists(p)
