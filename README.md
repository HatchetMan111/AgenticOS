# Agent OS Proxmox MVP
Setup: `bash proxmox-lxc-setup.sh`. Dashboard: :8080, API: :8000.
Adapter claude-code: CLI `claude`, fehlt CLI -> `AdapterMissing` mit Namen.
Adapter hermes: CLI `hermes`, fehlt CLI -> `AdapterMissing` mit Namen.
Adapter openclaw: Stub (`openclaw-stub: ...`), API via `OPENCLAW_URL`.
Adapter codex: CLI `codex`, fehlt CLI -> `AdapterMissing` mit Namen (API via `CODEX_API_KEY`).
Adapter ollama: API via `OLLAMA_HOST`/`OLLAMA_MODEL`, Fehler -> `AdapterMissing`.
Adapter opencode: CLI `opencode`, fehlt CLI -> `AdapterMissing` mit Namen.
Adapter mock: Stub, gibt immer `mock-ok: ...` zurueck.
