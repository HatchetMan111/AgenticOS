# agent-os-proxmox/tests/test_web.py
import pathlib
def test_web_has_panels():
    h = pathlib.Path("agent-os-proxmox/web/index.html").read_text()
    for s in ["chat","kanban","memory","cron","inbox","running","review","done","failed"]:
        assert s in h.lower()
def test_web_is_live():
    import pathlib
    h = pathlib.Path("agent-os-proxmox/web/index.html").read_text().lower()
    js = pathlib.Path("agent-os-proxmox/web/app.js").read_text()
    assert "platzhalter" not in h
    for s in ["kanban", "detail", "memory", "cron", "statusline"]:
        assert s in h
    assert "setInterval" in js and "/tasks" in js and "/runs/" in js and "/memory" in js
    assert "alert(" not in js
