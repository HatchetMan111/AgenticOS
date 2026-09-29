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
REPO="HatchetMan111/AgenticOS.git"
BRANCH="main"
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
