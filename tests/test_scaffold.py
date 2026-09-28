# agent-os-proxmox/tests/test_scaffold.py
import pathlib, yaml

def test_compose_has_five_services():
    p = pathlib.Path("agent-os-proxmox/compose.yml")
    assert p.exists(), "compose.yml fehlt"
    data = yaml.safe_load(p.read_text())
    svcs = set(data.get("services", {}).keys())
    assert {"gateway", "web", "runner", "scheduler"} <= svcs

def test_env_example_has_required_keys():
    txt = pathlib.Path("agent-os-proxmox/.env.example").read_text()
    for k in ["GATEWAY_USER=", "GATEWAY_PASS=", "OLLAMA_MODEL="]:
        assert k in txt
