# agent-os-proxmox/runner/worker_daemon.py
import sys, time, traceback
sys.path.insert(0, "agent-os-proxmox")
from store import store
def run_once():
    try:
        tid = store.claim_next()
    except Exception:
        traceback.print_exc(); return None
    if tid is None: return None
    try:
        from runner import worker
        worker.execute(tid)
    except Exception:
        traceback.print_exc()
        try: store.set_status(tid, "failed")
        except Exception: traceback.print_exc()
    return tid
def main_loop(interval=5, limit=None):
    n = 0; rounds = 0
    while True:
        if run_once() is not None: n += 1
        rounds += 1
        if limit is not None and rounds >= limit: return n
        time.sleep(interval)
if __name__ == "__main__":
    main_loop()
