# tests/test_installer.py
import pathlib
ROOT = pathlib.Path("agent-os-proxmox")
def _read(p): return (ROOT / p).read_text()
def test_units_exist_and_restart():
    for u in ["gateway", "runner", "scheduler"]:
        t = _read(f"install/systemd/agentic-os-{u}.service")
        assert "Restart=always" in t
        assert "After=network-online.target" in t
        assert "PYTHONPATH=/opt/agentic-os" in t
        assert "WorkingDirectory=/var/lib/agentic-os" in t
def test_gateway_binds_all():
    t = _read("install/systemd/agentic-os-gateway.service")
    assert "--host 0.0.0.0" in t and "--port 8000" in t
def test_nginx_proxies():
    t = _read("install/nginx/agentic-os.conf")
    assert "listen 8080" in t and "proxy_pass http://127.0.0.1:8000" in t
