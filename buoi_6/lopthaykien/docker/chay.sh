#!/usr/bin/env bash
# ===========================================================================
# Dung Web (CT1) va IN RA URL THAT de mo dashboard.
#
# VI SAO CAN SCRIPT NAY: Node-RED khoi dong chi in
#     "Server now running at http://127.0.0.1:1880/"
# ma 127.0.0.1 la dia chi BEN TRONG container - mo tren laptop khong vao duoc.
# Container khong the tu biet IP cua Raspberry Pi, phai lay tu ben ngoai roi
# truyen vao (xem bien HOST_IP_* trong docker-compose.yml).
#
#     ./chay.sh          dung va in URL
#     ./chay.sh --url    chi in URL, khong dung lai container
# ===========================================================================
set -uo pipefail
cd "$(dirname "$0")"

# --- Lay IP that cua Pi ---------------------------------------------------
# Tailscale: on dinh, vao duoc tu moi mang. Uu tien dua len dau.
HOST_IP_TAILSCALE="$(tailscale ip -4 2>/dev/null | head -1)"
HOST_DNS_TAILSCALE="$(tailscale status --json 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)"
# LAN: chi dung khi cung Wi-Fi voi Pi, va CO THE DOI khi router cap lai DHCP.
# Loai bo dai 100.x cua Tailscale de khong lay nham.
HOST_IP_LAN="$(hostname -I | tr ' ' '\n' | grep -vE '^(100\.|127\.)' | head -1)"
export HOST_IP_TAILSCALE HOST_IP_LAN HOST_DNS_TAILSCALE

CONG=1880

if [ "${1:-}" != "--url" ]; then
    echo "Dang dung container..."
    docker compose up -d || exit 1

    # Cho healthcheck chuyen sang "healthy" thay vi doan bang sleep co dinh.
    printf "Cho Node-RED san sang"
    for _ in $(seq 1 40); do
        tt="$(docker inspect -f '{{.State.Health.Status}}' iot_buoi6_web 2>/dev/null)"
        [ "$tt" = "healthy" ] && break
        printf "."
        sleep 2
    done
    echo
fi

tt="$(docker inspect -f '{{.State.Status}} ({{.State.Health.Status}})' iot_buoi6_web 2>/dev/null || echo 'chua chay')"

echo
echo "════════════════════════════════════════════════════════════════"
echo "  CT1 - GIAO DIEN WEB        container: $tt"
echo "════════════════════════════════════════════════════════════════"
[ -n "$HOST_IP_TAILSCALE" ] && \
  echo "  Tailscale (moi mang) ->  http://$HOST_IP_TAILSCALE:$CONG/ui"
[ -n "$HOST_DNS_TAILSCALE" ] && \
  echo "  Ten mien Tailscale   ->  http://$HOST_DNS_TAILSCALE:$CONG/ui"
[ -n "$HOST_IP_LAN" ] && \
  echo "  LAN (cung Wi-Fi)     ->  http://$HOST_IP_LAN:$CONG/ui"
echo "  ----------------------------------------------------------"
[ -n "$HOST_IP_TAILSCALE" ] && \
  echo "  Editor sua flow      ->  http://$HOST_IP_TAILSCALE:$CONG"
echo "════════════════════════════════════════════════════════════════"
echo
echo "  Xem log CT1 : docker compose logs -f"
echo "  Xem log CT2-5: tail -f ~/iot_buoi6/logs/*.log"
echo
