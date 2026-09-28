import sys; sys.path.insert(0, "agent-os-proxmox")
from store import store, init_db
try: init_db("data/app.db")
except Exception: pass
from runner.adapters import run, AdapterMissing
def submit(title, agent, prompt): return store.create_task(title, agent, prompt)
def task_status(tid):
    import sqlite3
    c = sqlite3.connect("data/app.db"); r = c.execute("SELECT status FROM tasks WHERE id=?",(tid,)).fetchone(); return r[0]
def run_logs(rid): return store.get_logs(rid)
def execute(task_id):
    import sqlite3
    c = sqlite3.connect("data/app.db")
    title, agent, prompt = c.execute("SELECT title,agent,prompt FROM tasks WHERE id=?",(task_id,)).fetchone()
    store.set_status(task_id, "running")
    rid = store.start_run(task_id, agent)
    try:
        res = run(agent, prompt)
        store.append_log(rid, res[:2000]); store.save_run_log_file(rid, res)
        store.set_status(task_id, "review")
    except AdapterMissing as e:
        store.append_log(rid, f"FAILED: {e}"); store.set_status(task_id, "failed")
    return rid
