"""Store package (Task 2 interface, re-exported for package import).

Macht `store` zum echten Paket, damit `from store import create_task`
(Gateway) und `from store import store` (test_store.py, Submodul
`store/store.py`) im selben Prozess koexistieren.
"""
from .store import (
    init_db,
    create_task,
    set_status,
    start_run,
    append_log,
    get_logs,
    save_run_log_file,
    redact,
)

__all__ = [
    "init_db",
    "create_task",
    "set_status",
    "start_run",
    "append_log",
    "get_logs",
    "save_run_log_file",
    "redact",
]
