from fastapi.testclient import TestClient
import importlib.util
spec = importlib.util.spec_from_file_location("gw", "agent-os-proxmox/gateway/app.py")
gw = importlib.util.module_from_spec(spec); spec.loader.exec_module(gw)
c = TestClient(gw.app)
def test_health(): assert c.get("/health").json() == {"ok": True}
def test_empty_prompt_rejected():
    r = c.post("/tasks", json={"title":"t","agent":"mock","prompt":"  "}, auth=("admin","change-me"))
    assert r.status_code == 422
def test_bad_agent_rejected():
    r = c.post("/tasks", json={"title":"t","agent":"foo","prompt":"hi"}, auth=("admin","change-me"))
    assert r.status_code == 400
