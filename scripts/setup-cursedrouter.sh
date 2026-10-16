#!/bin/bash
#
# setup-cursed-mitm.sh
#
# Idempotent bootstrap for the cursed-router MITM layer:
#   - ipset for "cert installed" client tracking
#   - a dedicated, rebuilt-every-run iptables chain for the redirect logic
#     (fixes the duplicate-rule bug from running -A commands by hand twice)
#   - python venv + mitmproxy + flask
#   - the addon/captive-portal scripts actually written to disk
#   - systemd units for mitm-pending (8080), mitm-active (8081), cursed-captive (80)
#
# Run AFTER setup-cursed-router.sh (hostapd+dnsmasq+NAT) has already worked.
#
# Usage:
#   sudo ./setup-cursed-mitm.sh [wlan-iface] [ap-ip] [final-upstream-proxy]
#
# Example:
#   sudo ./setup-cursed-mitm.sh wlan1 10.66.0.1 http://upstream-proxy-host:3128
#
set -euo pipefail

APIF="${1:-wlan1}"
AP_IP="${2:-10.66.0.1}"
FINAL_PROXY="${3:-}"   # leave empty to skip upstream chaining (mitm-active just acts as a normal MITM, no onward proxy)

BASE_DIR=/opt/cursed-router
VENV_DIR="$BASE_DIR/venv"
IPSET_NAME=cert_installed
CHAIN=CURSED_REDIRECT

log()  { printf '\033[1;36m[+]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run as root (sudo)"
ip link show "$APIF" >/dev/null 2>&1 || die "interface $APIF not found"

# ---------- packages ----------
log "Installing ipset, python3-venv, build deps"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ipset python3-venv python3-pip

# ---------- venv + mitmproxy ----------
mkdir -p "$BASE_DIR"
if [ ! -x "$VENV_DIR/bin/mitmdump" ]; then
    log "Creating venv and installing mitmproxy + flask (this takes a minute)"
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    "$VENV_DIR/bin/pip" install --quiet mitmproxy flask
else
    log "venv + mitmproxy already present, skipping install"
fi

# ---------- ipset ----------
# `-exist` only suppresses the "already exists" error when the existing
# set's parameters match exactly. If a set with this name exists but was
# created with different options (e.g. a `timeout` you added by hand
# earlier), `-exist` does NOT save you — ipset still refuses. So check
# existence explicitly instead of trusting that flag.
log "Ensuring ipset '$IPSET_NAME' exists (idempotent, param-mismatch safe)"
if ipset list -n 2>/dev/null | grep -qx "$IPSET_NAME"; then
    log "ipset '$IPSET_NAME' already exists, leaving it as-is (not recreating)"
else
    ipset create "$IPSET_NAME" hash:ip
fi

cat > /etc/systemd/system/ipset-restore.service <<EOF
[Unit]
Description=Restore ipsets for cursed-router
Before=network-pre.target
Wants=network-pre.target

[Service]
Type=oneshot
# plain shell, not ipset's own -exist: same param-mismatch problem applies
# at boot too, so check-then-create instead of relying on -exist here as well.
ExecStartPre=/bin/sh -c '/sbin/ipset list -n | grep -qx $IPSET_NAME || /sbin/ipset create $IPSET_NAME hash:ip'
ExecStart=/sbin/ipset restore -file /etc/ipset.conf -exist
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
ipset save "$IPSET_NAME" > /etc/ipset.conf

# ---------- addon scripts ----------
log "Writing mitmproxy addon scripts"

cat > "$BASE_DIR/mark_verified.py" <<'PYEOF'
# mark_verified.py — runs on the pre-cert (8080) mitmproxy instance.
# Watches for a client successfully fetching the CA cert from mitm.it's
# built-in onboarding app and promotes their IP into the "cert_installed"
# ipset, which the iptables CURSED_REDIRECT chain uses to route them to
# mitm-active (8081) on their next new connection.
import subprocess
from mitmproxy import ctx, http

IPSET_NAME = "cert_installed"

def response(flow: http.HTTPFlow) -> None:
    if flow.request.pretty_host == "mitm.it" and "/cert/" in flow.request.path:
        client_ip = flow.client_conn.peername[0]
        try:
            subprocess.run(["ipset", "add", IPSET_NAME, client_ip, "-exist"], check=True)
            ctx.log.info(f"[cursed-router] marked {client_ip} as cert-installed")
        except subprocess.CalledProcessError as e:
            ctx.log.warn(f"[cursed-router] failed to mark {client_ip}: {e}")
PYEOF

if [ ! -f "$BASE_DIR/addon.py" ]; then
    cat > "$BASE_DIR/addon.py" <<'PYEOF'
# addon.py — your content-mangling addon, loaded by mitm-active (8081).
# Empty/pass-through for now so the service has something valid to load;
# replace with your actual chaos (content injection, redirects, etc.)
from mitmproxy import http

def request(flow: http.HTTPFlow) -> None:
    pass

def response(flow: http.HTTPFlow) -> None:
    pass
PYEOF
else
    log "$BASE_DIR/addon.py already exists, leaving your edits alone"
fi

cat > "$BASE_DIR/captive.py" <<'PYEOF'
from flask import Flask
app = Flask(__name__)

@app.route("/<path:_>", methods=["GET"])
@app.route("/", methods=["GET"])
def portal(_=""):
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:40px">
      <h1>Welcome to cursed-router</h1>
      <p>To continue, install the network certificate:</p>
      <a href="http://mitm.it" style="font-size:1.4em">Install Certificate</a>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
PYEOF

# ---------- systemd units ----------
log "Writing systemd units"

cat > /etc/systemd/system/mitm-pending.service <<EOF
[Unit]
Description=cursed-router mitm (pre-cert onboarding)
After=network.target

[Service]
ExecStart=$VENV_DIR/bin/mitmdump --mode transparent --showhost --listen-port 8080 -s $BASE_DIR/mark_verified.py
Restart=on-failure
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF

if [ -n "$FINAL_PROXY" ]; then
    MITM_ACTIVE_EXEC="$VENV_DIR/bin/mitmdump --mode upstream:$FINAL_PROXY --showhost --listen-port 8081 -s $BASE_DIR/addon.py"
else
    warn "No upstream proxy given — mitm-active will run as a plain transparent MITM (no onward chaining)"
    MITM_ACTIVE_EXEC="$VENV_DIR/bin/mitmdump --mode transparent --showhost --listen-port 8081 -s $BASE_DIR/addon.py"
fi

cat > /etc/systemd/system/mitm-active.service <<EOF
[Unit]
Description=cursed-router mitm (post-cert)
After=network.target

[Service]
ExecStart=$MITM_ACTIVE_EXEC
Restart=on-failure
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/cursed-captive.service <<EOF
[Unit]
Description=cursed-router captive portal landing page
After=network.target

[Service]
ExecStart=$VENV_DIR/bin/python $BASE_DIR/captive.py
Restart=on-failure
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF

# ---------- iptables: rebuild a dedicated chain every run (idempotent) ----------
log "Rebuilding iptables redirect chain '$CHAIN' (safe to re-run, no duplicate rules)"

# create the chain if missing, flush it if it exists — this is what makes
# re-running this script safe, unlike bare `-A` commands typed by hand.
iptables -t nat -N "$CHAIN" 2>/dev/null || true
iptables -t nat -F "$CHAIN"

# don't intercept traffic destined for the router's own portal IP
iptables -t nat -A "$CHAIN" -d "$AP_IP" -j RETURN

# verified clients -> mitm-active (8081)
iptables -t nat -A "$CHAIN" -p tcp --dport 80  -m set --match-set "$IPSET_NAME" src -j REDIRECT --to-port 8081
iptables -t nat -A "$CHAIN" -p tcp --dport 443 -m set --match-set "$IPSET_NAME" src -j REDIRECT --to-port 8081

# everyone else -> mitm-pending (8080)
iptables -t nat -A "$CHAIN" -p tcp --dport 80  -j REDIRECT --to-port 8080
iptables -t nat -A "$CHAIN" -p tcp --dport 443 -j REDIRECT --to-port 8080

# hook the chain into PREROUTING for the AP interface, exactly once
if ! iptables -t nat -C PREROUTING -i "$APIF" -j "$CHAIN" 2>/dev/null; then
    iptables -t nat -I PREROUTING 1 -i "$APIF" -j "$CHAIN"
fi

# ---------- persist iptables ----------
if command -v netfilter-persistent >/dev/null 2>&1; then
    log "Saving iptables rules"
    netfilter-persistent save
else
    apt-get install -y -qq iptables-persistent netfilter-persistent
    netfilter-persistent save
fi

# ---------- start everything ----------
log "Enabling and (re)starting services"
systemctl daemon-reload
systemctl enable --now ipset-restore mitm-pending mitm-active cursed-captive >/dev/null

sleep 2
for svc in mitm-pending mitm-active cursed-captive; do
    if systemctl is-active --quiet "$svc"; then
        log "$svc is up"
    else
        warn "$svc FAILED — check: journalctl -u $svc -n 50 --no-pager"
    fi
done

cat <<EOF

----------------------------------------------------------------
Done.

  Pending (pre-cert) proxy:  127.0.0.1:8080  <- $AP_IP:80/443 for unverified clients
  Active (post-cert) proxy:  127.0.0.1:8081  <- $AP_IP:80/443 for verified clients
  Captive portal page:       $AP_IP:80 (direct, not redirected)
  ipset:                     $IPSET_NAME (ipset list $IPSET_NAME to view)
  iptables chain:            $CHAIN (re-run this script anytime to rebuild cleanly)

Edit these and re-run this script to apply changes without duplicating rules:
  $BASE_DIR/addon.py          — your content-mangling logic (mitm-active)
  $BASE_DIR/mark_verified.py  — cert-install detection logic (mitm-pending)
  $BASE_DIR/captive.py        — the onboarding landing page

Debug:
  journalctl -u mitm-pending -f
  journalctl -u mitm-active -f
  journalctl -u cursed-captive -f
  ipset list $IPSET_NAME
  iptables -t nat -L $CHAIN -n -v --line-numbers
----------------------------------------------------------------
EOF