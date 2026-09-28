# agent-os-proxmox/tests/test_runner.py
import os
from runner import worker
from store import store as _store
def test_mock_run_isolated_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("data", exist_ok=True)
    _store.init_db("data/app.db")
    tid = worker.submit("T","mock","hello")
    rid = worker.execute(tid)
    assert worker.task_status(tid) in ("review","done")
    assert worker.run_logs(rid) != ""
