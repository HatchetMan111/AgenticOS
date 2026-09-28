# agent-os-proxmox/tests/test_e2e.py
def test_all_suites_present():
    import pathlib
    for f in ["test_scaffold.py","test_store.py","test_gateway.py","test_runner.py","test_web.py","test_scheduler.py"]:
        assert pathlib.Path("agent-os-proxmox/tests/"+f).exists()
