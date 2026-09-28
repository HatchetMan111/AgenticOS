from fastapi import FastAPI
app = FastAPI()
JOBS = [{"id":"oracle-daily","cron":"0 7 * * *","desc":"Trend-Scan (MVP manuell)"}]
@app.get("/jobs")
def jobs(): return JOBS
@app.post("/jobs/{jid}/trigger")
def trigger(jid: str): return {"job": jid, "note": "MVP: manueller Trigger, kein Auto-Run"}
