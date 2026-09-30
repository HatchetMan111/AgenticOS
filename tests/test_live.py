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
