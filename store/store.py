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
