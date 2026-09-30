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
def test_installer_head():
    t = _read("install/agentic-os.sh")
    assert t.startswith("#!/usr/bin/env bash\nset -euo pipefail")
    for v in ['APP="agentic-os"', 'HOSTNAME="agentic-os"', "CPU=2", "RAM=2048", "DISK=8"]:
        assert v in t
def test_installer_nextid_and_retry():
    t = _read("install/agentic-os.sh")
    assert "pvesh get /cluster/nextid" in t
    assert "RETRY" in t  # ID-Race: genau 1 Retry, dann Abbruch
def test_installer_create_flags():
    t = _read("install/agentic-os.sh")
    assert "--unprivileged 1" in t and "--onboot 1" in t and "ip=dhcp" in t
def test_installer_bash_syntax():
    import subprocess
    r = subprocess.run(["bash", "-n", "agent-os-proxmox/install/agentic-os.sh"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
def test_setup_blocks():
    t = _read("install/agentic-os.sh")
    for b in ["setup_base", "setup_python", "setup_repo", "setup_units", "setup_nginx", "setup_firewall"]:
        assert b in t
    assert "python3 -m venv /opt/agentic-os/venv" in t
    assert "systemctl enable --now" in t
    assert "Restart=always" in t or "daemon-reload" in t
def test_pip_failure_aborts():
    t = _read("install/agentic-os.sh")
    assert "pip install" in t and "set -e" in t  # via set -euo pipefail: pip-Fail bricht Block ab
def test_main_verify_update():
    t = _read("install/agentic-os.sh")
    assert "systemctl is-active" in t
    assert "localhost:8080" in t and "localhost:8000" in t and "localhost:8001" in t
    assert "update_container" in t  # Re-Run = Update, kein Doppel-CT
    assert "--debug" in t or 'DEBUG="1"' in t or 'DEBUG:-0' in t
    assert "pct destroy" in t  # Deinstall-Hinweis
def test_repo_url_full():
    t = _read("install/agentic-os.sh")
    assert 'REPO="https://github.com/HatchetMan111/AgenticOS.git"' in t
def test_sources_from_host_checkout():
    t = _read("install/agentic-os.sh")
    assert "fetch_sources" in t
    assert 'SRC_DIR="/tmp/agentic-os-install"' in t
    assert 'git clone --depth 1 --branch "$BRANCH" "$REPO" "$SRC_DIR"' in t
    assert "$SRC_DIR/install/systemd/agentic-os-$u.service" in t
    assert "$SRC_DIR/install/nginx/agentic-os.conf" in t
    assert "/dev/stdin" not in t
    assert "mktemp" not in t
def test_clone_target_no_src():
    t = _read("install/agentic-os.sh")
    assert "/opt/agentic-os/src" not in t
    assert "git clone --branch $BRANCH $REPO /opt/agentic-os" in t
    assert "git -C /opt/agentic-os pull --ff-only" in t
    for p in ["gateway/requirements.txt", "scheduler/requirements.txt", "runner/requirements.txt"]:
        assert f"/opt/agentic-os/{p}" in t
    assert "ln -sfn /opt/agentic-os/src/web" not in t
def test_verify_honest():
    t = _read("install/agentic-os.sh")
    assert "http://localhost:8080/api/health" in t
    assert "test -f /opt/agentic-os/runner/worker_daemon.py" in t
    assert "runner-Check skipped" in t
    assert 'curl -sf "http://${ip}:8080/"' in t
def test_branch_is_master():
    t = _read("install/agentic-os.sh")
    assert 'BRANCH="master"' in t
def test_readme_raw_url_uses_master():
    t = _read("README.md")
    assert "/main/install/" not in t
    assert "https://raw.githubusercontent.com/HatchetMan111/AgenticOS/master/install/agentic-os.sh" in t
