# agent-os-proxmox/tests/test_runner.py
from runner import worker
def test_mock_run_isolated_logs(tmp_path):
    tid = worker.submit("T","mock","hello")
    rid = worker.execute(tid)
    assert worker.task_status(tid) in ("review","done")
    assert worker.run_logs(rid) != ""
