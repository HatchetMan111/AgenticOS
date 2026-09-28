# agent-os-proxmox/tests/test_scheduler.py
import importlib.util
spec = importlib.util.spec_from_file_location("sched", "agent-os-proxmox/scheduler/app.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from fastapi.testclient import TestClient
c = TestClient(m.app)
def test_jobs_list(): assert isinstance(c.get("/jobs").json(), list)
