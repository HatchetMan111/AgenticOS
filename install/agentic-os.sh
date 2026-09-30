#!/usr/bin/env bash
set -euo pipefail
# Agentic-OS Proxmox LXC Installer - Teil 1: Kopf, Preflight, ID, Create, Wait

APP="agentic-os"
HOSTNAME="agentic-os"
CPU=2
RAM=2048
DISK=8
TEMPLATE="debian-12-standard"
STORAGE="local-lvm"
TEMPLATE_STORE="local"
BRIDGE="vmbr0"
DEBUG=0
REPO="https://github.com/HatchetMan111/AgenticOS.git"
BRANCH="master"
SRC_DIR="/tmp/agentic-os-install"
LOG="/tmp/agentic-os-install.log"

if [ "${DEBUG}" = "1" ]; then
  set -x
fi

fail() {
  echo "FAIL: $*" >&2
  return 1
}

step() {
  local name="$1"
  shift
  echo "### ${name}" >>"${LOG}" 2>&1
  if "$@" >>"${LOG}" 2>&1; then
    echo "OK: ${name}"
    return 0
  fi
  local rc=$?
  tail -n 50 "${LOG}" >&2 || true
  return "${rc}"
}

preflight() {
  command -v pct >/dev/null 2>&1 || fail "pct fehlt"
  command -v pvesh >/dev/null 2>&1 || fail "pvesh fehlt"
  local tpl
  tpl="$(pveam list "${TEMPLATE_STORE}" 2>/dev/null | grep -o "${TEMPLATE}[^ ]*\\.tar\\.zst" | head -n 1 || true)"
  if [ -z "${tpl}" ]; then
    step "pveam update" pveam update
    step "pveam download" pveam download "${TEMPLATE_STORE}" "${TEMPLATE}_12.7-1_amd64.tar.zst"
    tpl="${TEMPLATE}_12.7-1_amd64.tar.zst"
  fi
  echo "${TEMPLATE_STORE}:vztmpl/${tpl}" > /tmp/agentic-os.tpl
}

fetch_sources() {
  step "Checkout vorbereiten" rm -rf "$SRC_DIR" || fail "checkout cleanup failed"
  step "Quellen klonen" git clone --depth 1 --branch "$BRANCH" "$REPO" "$SRC_DIR" || fail "git clone failed"
}

existing_ct() {
  pct list | awk 'NR>1 && $4 == "'"${HOSTNAME}"'" {print $1}'
}

next_id() {
  pvesh get /cluster/nextid | tr -d '" '"'"' \n'
}

create_container() {
  local id tmpl
  id="$(next_id)"
  tmpl="$(cat /tmp/agentic-os.tpl)"
  # ID-Race: genau 1 RETRY mit frischer ID, dann Abbruch
  if ! pct create "${id}" "${tmpl}" \
    --hostname "${HOSTNAME}" \
    --cores "${CPU}" \
    --memory "${RAM}" \
    --rootfs "${STORAGE}:${DISK}" \
    --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp" \
    --ostype debian \
    --unprivileged 1 \
    --onboot 1 \
    --start 0; then
    id="$(next_id)"
    pct create "${id}" "${tmpl}" \
      --hostname "${HOSTNAME}" \
      --cores "${CPU}" \
      --memory "${RAM}" \
      --rootfs "${STORAGE}:${DISK}" \
      --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp" \
      --ostype debian \
      --unprivileged 1 \
      --onboot 1 \
      --start 0 || fail "pct create failed (nach RETRY)"
  fi
  echo "${id}" > /tmp/agentic-os.ctid
}

wait_for_ip() {
  local id i ip
  id="$(cat /tmp/agentic-os.ctid)"
  i=0
  while [ "${i}" -lt 24 ]; do
    ip="$(pct exec "${id}" -- hostname -I 2>/dev/null | awk '{print $1}' || true)"
    if [ -n "${ip}" ]; then
      echo "${ip}"
      return 0
    fi
    sleep 5
    i=$((i + 1))
  done
  fail "keine IP nach 24x5s (Container ${id} bleibt stehen)"
}

CT_EXEC() { pct exec "$CTID" -- bash -s; }  # liest Heredoc von stdin, Fehler via set -e

setup_base() {
  CT_EXEC <<'EOF'
set -euo pipefail
apt-get update && apt-get install -y python3-venv python3-pip nginx curl sqlite3 git
mkdir -p /var/lib/agentic-os /etc/agentic-os
EOF
}
setup_python() {
  CT_EXEC <<'EOF'
set -euo pipefail
python3 -m venv /opt/agentic-os/venv
/opt/agentic-os/venv/bin/pip install --upgrade pip
EOF
}
setup_repo() {
  CT_EXEC <<EOF
set -euo pipefail
# /opt/agentic-os existiert bereits (venv aus setup_python): Platz fuer Clone schaffen, venv danach neu
if [ -d /opt/agentic-os/.git ]; then git -C /opt/agentic-os pull --ff-only; else rm -rf /opt/agentic-os/venv; git clone --branch $BRANCH $REPO /opt/agentic-os; python3 -m venv /opt/agentic-os/venv; fi
/opt/agentic-os/venv/bin/pip install -r /opt/agentic-os/gateway/requirements.txt -r /opt/agentic-os/scheduler/requirements.txt -r /opt/agentic-os/runner/requirements.txt
EOF
}
setup_units() {
  for u in gateway runner scheduler; do
    pct push "$CTID" "$SRC_DIR/install/systemd/agentic-os-$u.service" "/etc/systemd/system/agentic-os-$u.service"
  done
  CT_EXEC <<'EOF'
set -euo pipefail
[ -f /opt/agentic-os/runner/worker_daemon.py ] || echo "WARN: worker_daemon fehlt, runner-Unit bleibt inaktiv bis Folgerelease"
systemctl daemon-reload
systemctl enable --now agentic-os-gateway agentic-os-scheduler
[ -f /opt/agentic-os/runner/worker_daemon.py ] && systemctl enable --now agentic-os-runner || true
EOF
}
setup_nginx() {
  pct push "$CTID" "$SRC_DIR/install/nginx/agentic-os.conf" /etc/nginx/sites-enabled/agentic-os
  CT_EXEC <<'EOF'
set -euo pipefail
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl enable nginx && systemctl restart nginx
EOF
}
setup_firewall() {
  local node; node=$(hostname)
  pvesh set "/nodes/$node/lxc/$CTID/firewall/options" --enable 1 >>"$LOG" 2>&1 || true
  pvesh create "/nodes/$node/lxc/$CTID/firewall/rules" --action ACCEPT --type in --dport 8080 --proto tcp --comment "agentic-os dashboard" >>"$LOG" 2>&1 || true
}
setup_container() {
  step "Basis" setup_base
  step "Python venv" setup_python
  step "Repo + Deps" setup_repo
  step "Units" setup_units
  step "nginx" setup_nginx
  step "Firewall" setup_firewall
}

update_container() {
  CTID="$1"
  CT_EXEC <<'EOF'
set -euo pipefail
git -C /opt/agentic-os pull --ff-only
/opt/agentic-os/venv/bin/pip install -r /opt/agentic-os/gateway/requirements.txt -r /opt/agentic-os/scheduler/requirements.txt -r /opt/agentic-os/runner/requirements.txt
EOF
  for u in gateway runner scheduler; do
    pct push "$CTID" "$SRC_DIR/install/systemd/agentic-os-$u.service" "/etc/systemd/system/agentic-os-$u.service"
  done
  pct push "$CTID" "$SRC_DIR/install/nginx/agentic-os.conf" /etc/nginx/sites-enabled/agentic-os
  CT_EXEC <<'EOF'
set -euo pipefail
[ -f /opt/agentic-os/runner/worker_daemon.py ] || echo "WARN: worker_daemon fehlt, runner-Unit bleibt inaktiv bis Folgerelease"
systemctl daemon-reload
systemctl enable --now agentic-os-gateway agentic-os-scheduler
[ -f /opt/agentic-os/runner/worker_daemon.py ] && systemctl enable --now agentic-os-runner || true
EOF
  pct exec "$CTID" -- systemctl restart nginx || true
  verify
}

verify() {
  pct exec "$CTID" -- systemctl is-active agentic-os-gateway || fail "gateway inaktiv"
  pct exec "$CTID" -- systemctl is-active agentic-os-scheduler || fail "scheduler inaktiv"
  pct exec "$CTID" -- systemctl is-active nginx || fail "nginx inaktiv"
  if pct exec "$CTID" -- test -f /opt/agentic-os/runner/worker_daemon.py; then
    pct exec "$CTID" -- systemctl is-active agentic-os-runner || fail "runner inaktiv"
  else
    echo "WARN: worker_daemon fehlt im CT, runner-Check skipped"
  fi
  pct exec "$CTID" -- bash -c 'curl -fsS http://localhost:8080/api/health' || fail "verify 8080 fail"
  pct exec "$CTID" -- bash -c 'curl -fsS http://localhost:8000/health' || fail "verify 8000 fail"
  pct exec "$CTID" -- bash -c 'curl -fsS http://localhost:8001/jobs' || fail "verify 8001 fail"
  local ip
  ip="$(pct exec "$CTID" -- hostname -I | awk '{print $1}')"
  curl -sf "http://${ip}:8080/" || fail "host-seitiger 8080-Check fail"
  echo "FERTIG: http://${ip}:8080"
}

main() {
  if [ "${1:-}" = "--debug" ]; then
    DEBUG="1"
    set -x
  fi
  local existing
  preflight
  fetch_sources
  existing="$(existing_ct || true)"
  if [ -n "${existing}" ]; then
    update_container "${existing}"
    return 0
  fi
  create_container
  CTID="$(cat /tmp/agentic-os.ctid)"
  pct start "$CTID"
  wait_for_ip
  setup_container
  verify
  # Deinstall-Hinweis: pct destroy <ctid> (CT bleibt bei FAIL stehen)
}

main "$@"
