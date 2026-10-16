#!/bin/bash
#
# setup-cursed-router.sh
#
# Bootstraps hostapd + dnsmasq (DHCP+DNS) on a dedicated wireless interface,
# based on the existing /etc/hostapd/hostapd.conf + wpa_psk_ppsk layout seen
# on this box. Idempotent-ish: safe to re-run.
#
# Usage:
#   sudo ./setup-cursed-router.sh [wlan-iface] [ap-ip/cidr]
#
# Example:
#   sudo ./setup-cursed-router.sh wlan1 10.66.0.1/24
#
set -euo pipefail

# ---------- config ----------
IFACE="${1:-wlan1}"
AP_CIDR="${2:-10.66.0.1/24}"
AP_IP="${AP_CIDR%/*}"
AP_PREFIX="${AP_CIDR#*/}"
SSID="${SSID:-cursed-router}"
CHANNEL="${CHANNEL:-6}"
COUNTRY="${COUNTRY:-NL}"
UPLINK_IFACE="${UPLINK_IFACE:-}"   # e.g. eth0 — leave empty to skip NAT/forwarding setup

HOSTAPD_DIR=/etc/hostapd
HOSTAPD_CONF="$HOSTAPD_DIR/hostapd.conf"
PSK_FILE="$HOSTAPD_DIR/wpa_psk_ppsk"
DNSMASQ_CONF=/etc/dnsmasq.d/cursed-router.conf

log()  { printf '\033[1;36m[+]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run as root (sudo)"

# ---------- sanity checks ----------
ip link show "$IFACE" >/dev/null 2>&1 || die "interface $IFACE not found. Available: $(ls /sys/class/net)"

# ---------- packages ----------
log "Installing hostapd + dnsmasq + iproute2/iptables-persistent"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq hostapd dnsmasq iproute2 iptables netfilter-persistent iptables-persistent

# hostapd's default unit refuses to start unless unmasked (Debian ships it
# masked because normally it's driven by ifupdown hooks, not systemd)
systemctl unmask hostapd 2>/dev/null || true
systemctl stop hostapd dnsmasq 2>/dev/null || true

# ---------- rfkill ----------
if command -v rfkill >/dev/null 2>&1; then
    rfkill unblock wifi || true
fi

# ---------- interface: static IP, bring down any DHCP client on it ----------
log "Configuring static IP $AP_CIDR on $IFACE"
ip link set "$IFACE" down
ip addr flush dev "$IFACE"
ip link set "$IFACE" up
ip addr add "$AP_CIDR" dev "$IFACE"

# Persist across reboots via /etc/network/interfaces.d if ifupdown is in use
if [ -d /etc/network/interfaces.d ]; then
    cat > /etc/network/interfaces.d/"$IFACE" <<EOF
auto $IFACE
iface $IFACE inet static
    address $AP_IP
    netmask $(python3 -c "import ipaddress; print(ipaddress.ip_network('0.0.0.0/$AP_PREFIX').netmask)")
EOF
fi

# ---------- hostapd.conf ----------
mkdir -p "$HOSTAPD_DIR"
log "Writing $HOSTAPD_CONF"
cat > "$HOSTAPD_CONF" <<EOF
interface=$IFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
ieee80211n=1
wmm_enabled=1
country_code=$COUNTRY

wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_psk_file=$PSK_FILE
auth_algs=1
macaddr_acl=0
ignore_broadcast_ssid=0

# ap_isolate=0 so devices can see each other (casting/discovery demo);
# real segmentation, if you need it, belongs in firewall rules, not here.
ap_isolate=0

ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
EOF

# ---------- PSK file (multi-password / "magic word" support) ----------
if [ ! -f "$PSK_FILE" ]; then
    log "Writing default $PSK_FILE (wildcard MAC -> multiple accepted passphrases)"
    cat > "$PSK_FILE" <<'EOF'
# /etc/hostapd/wpa_psk_ppsk
# format: <mac or wildcard 00:00:00:00:00:00>  <passphrase, 8-63 chars>
# wildcard MAC = any client may use this passphrase to join.
# hostapd does NOT let you "accept any password" — each phrase here is a
# distinct valid PSK. Add as many magic words as you want.
00:00:00:00:00:00    password1
00:00:00:00:00:00    password2
00:00:00:00:00:00    password3
EOF
else
    log "$PSK_FILE already exists, leaving it alone"
fi
chmod 600 "$PSK_FILE"

# point default config at this interface for the debian init script hook
echo "DAEMON_CONF=\"$HOSTAPD_CONF\"" > /etc/default/hostapd

# ---------- dnsmasq (DHCP + DNS) ----------
log "Writing $DNSMASQ_CONF"
mkdir -p /etc/dnsmasq.d
RANGE_START="${AP_IP%.*}.50"
RANGE_END="${AP_IP%.*}.250"
cat > "$DNSMASQ_CONF" <<EOF
# Scope dnsmasq to just the AP interface so it doesn't fight any other
# DHCP/DNS server on the box.
interface=$IFACE
bind-interfaces
except-interface=lo

# DHCP
dhcp-range=$RANGE_START,$RANGE_END,255.255.255.0,12h
dhcp-option=3,$AP_IP      # gateway
dhcp-option=6,$AP_IP      # DNS server (us)

# DNS
domain-needed
bogus-priv
no-resolv
server=1.1.1.1
server=9.9.9.9
log-queries
log-dhcp

# --- cursed-router hooks ---
# Uncomment to force ALL DNS through you (captive-portal / mitm trigger):
# address=/#/$AP_IP
#
# Redirect a specific domain somewhere weird:
# address=/example.com/$AP_IP
EOF

# make sure system resolved/dnsmasq don't fight over port 53
if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
    warn "systemd-resolved is active and may hold port 53; disabling DNSStubListener"
    mkdir -p /etc/systemd/resolved.conf.d
    cat > /etc/systemd/resolved.conf.d/no-stub.conf <<'EOF'
[Resolve]
DNSStubListener=no
EOF
    systemctl restart systemd-resolved
fi

# ---------- forwarding / NAT (optional, only if an uplink iface given) ----------
log "Enabling IPv4 forwarding"
sysctl -w net.ipv4.ip_forward=1 >/dev/null
if ! grep -q '^net.ipv4.ip_forward=1' /etc/sysctl.conf 2>/dev/null; then
    echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
fi

if [ -n "$UPLINK_IFACE" ]; then
    log "Setting up NAT: $IFACE -> $UPLINK_IFACE"
    iptables -t nat -C POSTROUTING -o "$UPLINK_IFACE" -j MASQUERADE 2>/dev/null \
        || iptables -t nat -A POSTROUTING -o "$UPLINK_IFACE" -j MASQUERADE
    iptables -C FORWARD -i "$IFACE" -o "$UPLINK_IFACE" -j ACCEPT 2>/dev/null \
        || iptables -A FORWARD -i "$IFACE" -o "$UPLINK_IFACE" -j ACCEPT
    iptables -C FORWARD -i "$UPLINK_IFACE" -o "$IFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null \
        || iptables -A FORWARD -i "$UPLINK_IFACE" -o "$IFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT
    netfilter-persistent save
else
    warn "No UPLINK_IFACE set — AP will have no internet, just a local L2/L3 network."
    warn "Re-run as: sudo UPLINK_IFACE=eth0 $0 $IFACE $AP_CIDR"
fi

# ---------- start services ----------
log "Enabling + starting dnsmasq"
systemctl enable dnsmasq >/dev/null
systemctl restart dnsmasq

log "Enabling + starting hostapd"
systemctl enable hostapd >/dev/null
systemctl restart hostapd

sleep 1
if systemctl is-active --quiet hostapd; then
    log "hostapd is up. SSID '$SSID' broadcasting on $IFACE (chan $CHANNEL)"
else
    warn "hostapd failed to start — check: journalctl -u hostapd -n 50"
fi

if systemctl is-active --quiet dnsmasq; then
    log "dnsmasq is up. DHCP range $RANGE_START - $RANGE_END"
else
    warn "dnsmasq failed to start — check: journalctl -u dnsmasq -n 50"
fi

cat <<EOF

----------------------------------------------------------------
Done.

  Interface:   $IFACE
  AP IP:       $AP_IP
  SSID:        $SSID
  PSK file:    $PSK_FILE  (edit to add/remove magic passwords)
  dnsmasq cfg: $DNSMASQ_CONF  (edit for DNS hijack rules)

Useful commands:
  hostapd_cli -i $IFACE reload        # reload after editing hostapd.conf or PSK file
  systemctl restart dnsmasq           # reload after editing dnsmasq.d/*.conf
  journalctl -u hostapd -f            # watch AP logs / auth attempts
  journalctl -u dnsmasq -f            # watch DHCP/DNS logs
----------------------------------------------------------------
EOF