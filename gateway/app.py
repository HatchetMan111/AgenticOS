import os, secrets
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import sys; sys.path.insert(0, "agent-os-proxmox")
from store import create_task, init_db
try: init_db("data/app.db")
except Exception: pass
AGENTS = {"claude-code","hermes","openclaw","codex","ollama","opencode","mock"}
app = FastAPI(); sec = HTTPBasic()
class T(BaseModel): title: str; agent: str; prompt: str
def auth(c: HTTPBasicCredentials = Depends(sec)):
    u, p = os.getenv("GATEWAY_USER","admin"), os.getenv("GATEWAY_PASS","change-me")
    if not (secrets.compare_digest(c.username,u) and secrets.compare_digest(c.password,p)):
        raise HTTPException(401, "unauthorized")
    return True
@app.get("/health")
def health(): return {"ok": True}
@app.post("/tasks")
def make(t: T, _=Depends(auth)):
    if not t.prompt.strip(): raise HTTPException(422, "empty prompt")
    if t.agent not in AGENTS: raise HTTPException(400, f"unknown agent, valid: {sorted(AGENTS)}")
    return {"id": create_task(t.title, t.agent, t.prompt)}
from store import list_tasks, task_detail, get_logs, list_run_files
@app.get("/tasks")
def tasks(limit: int = 100, _=Depends(auth)): return list_tasks(limit)
@app.get("/tasks/{tid}")
def one_task(tid: int, _=Depends(auth)):
    d = task_detail(tid)
    if not d: raise HTTPException(404, "no such task")
    return d
@app.get("/runs/{rid}/logs")
def run_logs(rid: int, _=Depends(auth)):
    import sqlite3
    with sqlite3.connect("data/app.db") as c:
        exists = c.execute("SELECT id FROM runs WHERE id=?", (rid,)).fetchone()
    if not exists:
        raise HTTPException(404, "no such run")
    return {"lines": get_logs(rid).splitlines()}
@app.get("/memory")
def memory(_=Depends(auth)): return list_run_files()
