# agent-os-proxmox/tests/test_adapters.py
from runner.adapters import run, AdapterMissing
def test_missing_cli_gives_named_error():
    try: run("claude-code", "hi")
    except AdapterMissing as e: assert "claude" in str(e).lower() or "fehlt" in str(e).lower()
    else: pass  # CLI vorhanden -> ok, kein Fail
def test_mock_ok(): assert run("mock", "hi").startswith("mock-ok")
