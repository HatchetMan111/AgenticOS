# agent-os-proxmox/tests/test_web.py
import pathlib
def test_web_has_panels():
    h = pathlib.Path("agent-os-proxmox/web/index.html").read_text()
    for s in ["chat","kanban","memory","cron","inbox","running","review","done","failed"]:
        assert s in h.lower()
