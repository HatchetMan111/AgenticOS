import os, re, sqlite3, datetime
SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")
VALID = {"inbox","running","review","done","failed"}
REDACT = re.compile(r"(sk-[A-Za-z0-9_-]{4,}|api_key\s*=\s*\S+)", re.I)

def _c(db): return sqlite3.connect(db)
def init_db(db):
    with _c(db) as c: c.executescript(open(SCHEMA).read())
def create_task(title, agent, prompt, db="data/app.db"):
    if not (prompt or "").strip(): raise ValueError("empty prompt")
    with _c(db) as c:
        cur = c.execute("INSERT INTO tasks(title,agent,prompt,status) VALUES(?,?,?,?)",(title,agent,prompt,"inbox"))
        return cur.lastrowid
def set_status(task_id, status, db="data/app.db"):
    assert status in VALID, f"bad status {status}"
    with _c(db) as c: c.execute("UPDATE tasks SET status=? WHERE id=?",(status,task_id))
def start_run(task_id, agent, db="data/app.db"):
    with _c(db) as c:
        cur = c.execute("INSERT INTO runs(task_id,agent,status) VALUES(?,?,?)",(task_id,agent,"running"))
        return cur.lastrowid
def redact(line): return REDACT.sub("***", line)
def append_log(run_id, line, db="data/app.db"):
    with _c(db) as c: c.execute("INSERT INTO logs(run_id,line) VALUES(?,?)",(run_id, redact(line)))
def get_logs(run_id, db="data/app.db"):
    with _c(db) as c:
        return "\n".join(r[0] for r in c.execute("SELECT line FROM logs WHERE run_id=? ORDER BY id",(run_id,)))
def save_run_log_file(run_id, text, memdir="memory/runs"):
    os.makedirs(memdir, exist_ok=True)
    p = os.path.join(memdir, f"{datetime.date.today()}-{run_id}.md")
    open(p,"w").write(redact(text))
    return p
def list_tasks(limit=100, db="data/app.db"):
    with _c(db) as c:
        return [{"id": r[0], "title": r[1], "agent": r[2], "status": r[3]}
                for r in c.execute("SELECT id,title,agent,status FROM tasks ORDER BY id DESC LIMIT ?", (limit,))]
def task_detail(task_id, db="data/app.db"):
    with _c(db) as c:
        r = c.execute("SELECT id,title,agent,prompt,status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not r: return None
        runs = [x[0] for x in c.execute("SELECT id FROM runs WHERE task_id=? ORDER BY id", (task_id,))]
        return {"id": r[0], "title": r[1], "agent": r[2], "prompt": r[3], "status": r[4], "run_ids": runs}
def claim_next(db="data/app.db"):
    with _c(db) as c:
        r = c.execute("SELECT id FROM tasks WHERE status='inbox' ORDER BY id LIMIT 1").fetchone()
        if not r: return None
        c.execute("UPDATE tasks SET status='running' WHERE id=? AND status='inbox'", (r[0],))
        return r[0] if c.total_changes else None
def list_run_files(memdir="memory/runs"):
    import glob
    rows = []
    for p in sorted(glob.glob(os.path.join(memdir, "*.md"))):
        txt = open(p).read()
        rows.append({"name": os.path.basename(p), "preview": redact(txt)[:200]})
    return rows
