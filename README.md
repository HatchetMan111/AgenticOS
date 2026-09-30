# Agentic-OS auf Proxmox LXC – Einzeiler-Installation

Agentic-OS ist ein generelles Agent-OS-Command-Center (Chat + Kanban + Memory +
Cron-Übersicht) mit 6 KI-Agenten-Adaptern (Claude Code, Hermes, OpenClaw, Codex,
Ollama, OpenCode) plus Mock. Es läuft **vollständig lokal** in einem
unprivilegierten LXC-Container, **nativ** (Python-venv, kein Docker):
Dashboard auf Port **8080**, Gateway-API auf Port **8000**, Scheduler auf Port
**8001**, je als systemd-Service mit `Restart=always`, Container mit `onboot: 1`.

| Eigenschaft | Wert |
|---|---|
| App-Name / Hostname | `agentic-os` |
| Zweck | Agent-OS-Command-Center: Tasks per Chat an KI-Agenten geben, Kanban-Status live, Memory-Files + SQLite |
| Tech-Stack | Python/FastAPI + Uvicorn (nativ im venv), SQLite + Markdown-Files, nginx |
| GitHub-Repo | `https://github.com/HatchetMan111/AgenticOS` (App-Code + Installer in einem Repo) |
| Web UI | `http://<LXC-IP>:8080` (Dashboard, bind `0.0.0.0`) |
| API / Scheduler | `http://<LXC-IP>:8000/health`, `http://<LXC-IP>:8001/jobs` |
| Dashboard-Login | `admin` / `change-me` (ändern: `/etc/agentic-os/env` im Container, dann `systemctl restart agentic-os-gateway`) |
| Standard-Ressourcen | 2 vCPU / 2048 MB RAM / 8 GB Disk |
| CT-ID | immer die **nächste freie ID** (`pvesh get /cluster/nextid`) |
| Template | `debian-12-standard` (wird geladen falls fehlend) |

## 1. Installation (Einzeiler, auf dem Proxmox-Host als root)

Einfach kopieren und auf dem Proxmox-Host als `root` einfügen
(Community-Scripts-Stil, keine weitere Datei nötig):

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/HatchetMan111/AgenticOS/master/install/agentic-os.sh)"
```

Nur `--debug` wird unterstützt (`= bash -x`, maximale Fehlermeldungskette):

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/HatchetMan111/AgenticOS/master/install/agentic-os.sh)" --debug
```

Das Skript (`set -euo pipefail`, idempotent):
1. prüft Host/Tools, nimmt die nächste freie CT-ID, lädt das
   `debian-12-standard`-Template falls nötig,
2. erstellt den LXC `agentic-os` (`onboot: 1`, unprivilegiert, DHCP),
3. installiert im Container Python-venv unter `/opt/agentic-os`, klont das Repo,
   installiert Deps, legt die 3 systemd-Units an (`systemctl enable --now`),
   richtet nginx auf `:8080` ein und öffnet die Firewall für 8080,
4. verifiziert `systemctl is-active` (gateway, scheduler, nginx) + HTTP-Checks
   auf `localhost:8080/8000/8001` + Host-Check auf die CT-IP und gibt die finale
   URL aus.

Erwartete Schlussausgabe (Beispiel):

```text
OK: Basis
OK: Units
FERTIG: http://192.168.1.100:8080 (CT 100, Hostname agentic-os)
```

## 2. Reboot-Test (Reboot-sicher belegen)

```bash
CT=100
pct reboot $CT
sleep 60
pct exec $CT -- systemctl is-active agentic-os-gateway agentic-os-scheduler nginx   # muss: active
curl -fs http://$(pct exec $CT -- hostname -I | awk '{print $1}'):8080/ >/dev/null && echo DASHBOARD-OK
pct config $CT | grep -i onboot              # muss: onboot: 1
```

## 3. Update (idempotent – einfach erneut laufen lassen)

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/HatchetMan111/AgenticOS/master/install/agentic-os.sh)"
# Hostname existiert -> Update-Pfad: git pull + pip install + Units/nginx neu pushen + restart. Kein neuer CT.
```

Manuell im Container:

```bash
pct enter 100
cd /opt/agentic-os && git pull --ff-only
/opt/agentic-os/venv/bin/pip install -r gateway/requirements.txt -r scheduler/requirements.txt
systemctl restart agentic-os-gateway agentic-os-scheduler && systemctl status agentic-os-gateway --no-pager --full
curl -fs http://127.0.0.1:8000/health && curl -fs http://127.0.0.1:8001/jobs
```

## 4. Deinstallation

```bash
pct stop 100 && pct destroy 100
```

## 5. Debugging (komplette Fehlermeldungskette)

- Jeder Lauf loggt **stdout+stderr vollständig** nach `/tmp/agentic-os-install.log`.
- Bei Fehlern druckt das Skript: Stufe, Befehl, Exit-Code, die letzten 50
  Log-Zeilen — niemals nur die letzte Zeile. Re-run mit Trace (`--debug`).
- Im Container weiter eingrenzen:

```bash
pct exec 100 -- systemctl status agentic-os-gateway --no-pager --full
pct exec 100 -- journalctl -u agentic-os-gateway --no-pager -n 100
pct exec 100 -- nginx -t
pct exec 100 -- curl -fs http://127.0.0.1:8000/health && echo GATEWAY-OK
tail -n 200 /tmp/agentic-os-install.log   # auf dem Host
```

## 6. Dateien in diesem Repo

```text
AgenticOS/                          # App-Code + Proxmox-Installer in einem Repo
├── install/agentic-os.sh            # Proxmox-Install-Script (Community-Scripts-konform, Variablen oben)
├── install/systemd/agentic-os-*.service  # 3 Units (gateway/runner/scheduler, Restart=always)
├── install/nginx/agentic-os.conf   # nginx: statisch web/ + /api/ -> :8000
├── gateway/ runner/ scheduler/     # FastAPI-Dienste
├── web/                             # Dashboard (Chat/Kanban/Memory/Cron)
├── store/                           # SQLite + Markdown-Files
├── tests/                           # pytest-Suite (inkl. Installer-Asserts)
├── compose.yml                      # Alternative: Docker-Betrieb
├── proxmox-lxc-setup.sh             # Alternative: manuelles LXC-Setup mit Docker
└── README.md                        # diese Datei
```

## 7. Hinweise

- **Nativ statt Docker:** Der Installer nutzt bewusst kein Docker
  (`compose.yml` bleibt als Alternative). Python läuft im venv
  `/opt/agentic-os`, Daten (DB + Memory) unter `/var/lib/agentic-os`
  (Units setzen `PYTHONPATH`/`WorkingDirectory` entsprechend).
- **DHCP-Hinweis:** Ändert sich die Container-IP, Installer erneut laufen
  lassen (Update-Pfad). Für stabile URLs DHCP-Reservierung einrichten.
- **Scheduler:** `:8001/jobs` zeigt geplante Jobs (MVP: Übersicht + manueller
  Trigger, kein Autopilot).
- **Runner:** Die `agentic-os-runner`-Unit aktiviert sich, sobald der
  Worker-Daemon im Repo vorhanden ist (bis dahin Warnung statt Abbruch).
- **LXC statt VM:** Kein Kernel-/GPU-Bedarf — unprivilegierter LXC reicht.

## 8. App-Nutzung (nach der Installation)

- Dashboard öffnen (`http://<LXC-IP>:8080`), mit `admin` / `change-me` einloggen,
  Task per Chat an einen Agenten geben, Kanban-Karte wandert
  `inbox → running → review`. Ergebnisse landen als Markdown-Run-Log plus DB-Eintrag.
- Adapter (CLI/API im Container nachinstallieren bzw. Keys in
  `/etc/agentic-os/env` legen, danach Unit neu starten):
  - `claude-code`: CLI `claude`, fehlt CLI → `AdapterMissing` mit Namen.
  - `hermes`: CLI `hermes`, fehlt CLI → `AdapterMissing` mit Namen.
  - `openclaw`: API via `OPENCLAW_URL`, ohne URL → `AdapterMissing`.
  - `codex`: CLI `codex`, fehlt CLI → `AdapterMissing` mit Namen (API via `CODEX_API_KEY`).
  - `ollama`: API via `OLLAMA_HOST`/`OLLAMA_MODEL`, Fehler → `AdapterMissing`.
  - `opencode`: CLI `opencode`, fehlt CLI → `AdapterMissing` mit Namen.
  - `mock`: Stub, gibt immer `mock-ok: ...` zurück (sofort nutzbar, ideal zum Testen).
- Abnahme-Checkliste:
  - [ ] Dashboard `:8080` erreichbar, Login ok
  - [ ] API `:8000/health` → `{"ok": true}`
  - [ ] Chat legt Task an, Kanban zeigt Status
  - [ ] Je Adapter 1 manueller Task (mock sofort, Rest nach CLI/API-Setup)
  - [ ] Memory-File unter `memory/runs` + DB-Eintrag nach Run vorhanden
  - [ ] Proxmox-Snapshot vor Updates dokumentiert
