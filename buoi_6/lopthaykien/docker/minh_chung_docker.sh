#!/usr/bin/env bash
# ===========================================================================
# MINH CHUNG: giao dien Web dang chay TRONG DOCKER, khong phai chuong trinh khac
#
# De bai cho +2 diem neu dung Docker, nen phai chung minh duoc rang cai web o
# cong 1880 THUC SU do container phuc vu - khong phai mot Node-RED cai san tren
# may, cung khong phai cua bai khac.
#
#     ./minh_chung_docker.sh          chay 5 buoc kiem tra (khong dung web)
#     ./minh_chung_docker.sh --tat    chay them buoc 6: TAT container cho web
#                                     chet han roi bat lai - bang chung manh nhat
# ===========================================================================
set -uo pipefail
cd "$(dirname "$0")"
TEN=iot_buoi6_web
CONG=1880
IP=$(tailscale ip -4 2>/dev/null | head -1 || echo 127.0.0.1)

gach() { printf '\n\033[1m%s\033[0m\n' "══ $1 ══"; }

gach "1. AI DANG GIU CONG $CONG?"
# Neu la "docker-proxy" thi cong do do Docker chuyen tiep vao container.
# Neu la "node-red" hay "node" thi day la Node-RED cai thang len may - KHONG
# phai Docker, se khong duoc +2 diem.
sudo ss -tlnp | grep ":$CONG" | sed 's/^/   /'

gach "2. TREN MAY CO NODE-RED NAO KHAC KHONG?"
printf '   lenh node-red tren host : %s\n' "$(command -v node-red || echo 'KHONG CO')"
# systemctl is-active voi unit KHONG TON TAI van in "inactive" ra stdout roi
# moi tra ma loi -> dung "|| echo" se in ca hai dong, lem. Phai hoi unit co ton
# tai khong TRUOC.
if systemctl cat nodered.service >/dev/null 2>&1; then
    trang_thai_nodered="$(systemctl is-active nodered)"
else
    trang_thai_nodered="KHONG TON TAI tren host"
fi
printf '   service nodered        : %s\n' "$trang_thai_nodered"
echo "   -> khong co ban cai nao ngoai Docker"

gach "3. CONTAINER ANH XA CONG NHU THE NAO?"
docker port "$TEN" | sed 's/^/   /'

gach "4. TIEN TRINH NODE-RED NAM BEN TRONG CONTAINER"
docker top "$TEN" | tail -2 | awk '{printf "   PID %-8s %s\n", $2, $8}'

gach "5. FLOW TRONG CONTAINER CO DUNG LA CUA BAI NAY?"
printf '   ten tab   : %s\n' "$(docker exec "$TEN" grep -o 'Buoi 6 - muc 15 diem' /data/flows.json | head -1)"
printf '   ma bam trong container : %s\n' "$(docker exec "$TEN" sha256sum /data/flows.json | cut -c1-16)"
printf '   ma bam tren dia Pi     : %s\n' "$(sha256sum ../node-red-data/flows.json | cut -c1-16)"
echo "   -> hai ma bam trung nhau = container dang chay DUNG file flow cua minh"

if [ "${1:-}" = "--tat" ]; then
    gach "6. TAT CONTAINER -> WEB PHAI CHET"
    # curl khi khong ket noi duoc VUA in "000" ra stdout VUA tra ma loi, nen
    # "|| echo ..." se in ca hai -> phai bat ma vao bien roi moi dien giai.
    thu_web() {
        local ma
        ma=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://$IP:$CONG/ui/" 2>/dev/null)
        case "$ma" in
            200) echo "HTTP 200  (web song)" ;;
            000|"") echo "KHONG KET NOI DUOC  (web chet)" ;;
            *) echo "HTTP $ma" ;;
        esac
    }
    echo "   truoc khi tat : $(thu_web)"
    docker stop "$TEN" >/dev/null
    echo "   da tat container..."
    echo "   sau khi tat   : $(thu_web)"
    echo "   -> web chet theo container = web DO CONTAINER phuc vu"

    gach "7. BAT LAI"
    ./chay.sh
fi
