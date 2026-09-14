#!/usr/bin/env bash
# ===========================================================================
# XEM TAT CA 5 CHUONG TRINH DANG CHAY  -  minh chung "task manager" cua de bai
#
#     ~/iot_buoi6/raspberry/trang_thai.sh
#
# De bai Luu y 3: "Trong video minh chung ro cac buoc chung minh chuong trinh
# da tu hoat dong (code, minh chung logfile, du lieu duoc gui len tu dong,
# task manager, ...)". Script nay gom het vao mot man hinh.
# ===========================================================================
set -uo pipefail
X='\033[0m'; D='\033[1m'; L='\033[32m'; V='\033[33m'; R='\033[31m'

printf "\n${D}╔══════════════════════════════════════════════════════════════════╗${X}\n"
printf   "${D}║  IOT BUOI 6 - MUC 15 DIEM   ·   %s   ║${X}\n" "$(date '+%d/%m/%Y %H:%M:%S')"
printf   "${D}╚══════════════════════════════════════════════════════════════════╝${X}\n"

printf "\n${D}── CT1 · GIAO DIEN WEB (Docker) ───────────────────────────────────${X}\n"
if docker ps --format '{{.Names}}' | grep -q iot_buoi6_web; then
    # Khong nhet ma mau vao --format: Docker in nguyen chuoi "\033[32m" ra
    # man hinh chu khong dien giai. Lay du lieu ra roi printf rieng.
    read -r ten img tt <<< "$(docker ps --filter name=iot_buoi6_web \
        --format '{{.Names}}|{{.Image}}|{{.Status}}' | tr '|' ' ')"
    printf "   ${L}●${X} %s   image=%s   %s\n" \
        "$(docker ps --filter name=iot_buoi6_web --format '{{.Names}}')" \
        "$(docker ps --filter name=iot_buoi6_web --format '{{.Image}}')" \
        "$(docker ps --filter name=iot_buoi6_web --format '{{.Status}}')"
    printf "     cong: %s\n" "$(docker port iot_buoi6_web | tr '\n' ' ')"
    printf "     tu khoi dong: docker=%s  policy=%s\n" \
        "$(systemctl is-enabled docker 2>/dev/null)" \
        "$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' iot_buoi6_web)"
else
    printf "   ${R}●${X} container iot_buoi6_web KHONG CHAY\n"
fi

printf "\n${D}── CT2-CT5 · CHUONG TRINH PYTHON (systemd) ────────────────────────${X}\n"
printf "   %-18s %-9s %-9s %-8s %-9s %s\n" "SERVICE" "TRANG THAI" "TU CHAY" "PID" "CHAY DUOC" "RESTART"
for s in iot-ct2-cambien iot-ct3-led iot-ct4-relay iot-ct5-lcd; do
    tt=$(systemctl is-active "$s" 2>/dev/null)
    pid=$(systemctl show -p MainPID --value "$s")
    [ "$tt" = active ] && cham="${L}●${X}" || cham="${R}●${X}"
    [ "$pid" = 0 ] && { pid='-'; song='-'; } || song=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
    printf "   $cham %-16s %-9s %-9s %-8s %-9s %s\n" \
        "$s" "$tt" "$(systemctl is-enabled "$s" 2>/dev/null)" "$pid" "${song:--}" \
        "$(systemctl show -p NRestarts --value "$s")"
done

printf "\n${D}── TIEN TRINH THAT (ps) ───────────────────────────────────────────${X}\n"
ps -eo pid,etime,pcpu,pmem,cmd --sort=pid | grep "[c]t[2345]_" \
  | awk '{printf "   PID %-7s chay %-10s CPU %-5s RAM %-5s %s\n", $1,$2,$3,$4,$NF}' \
  || printf "   ${R}khong thay tien trinh nao${X}\n"

printf "\n${D}── HAI LOGFILE ────────────────────────────────────────────────────${X}\n"
for f in "$HOME"/iot_buoi6/logs/*.log; do
    [ -e "$f" ] || continue
    printf "   %-26s %6s dong   sua cuoi %s\n" \
        "$(basename "$f")" "$(wc -l < "$f")" "$(date -r "$f" '+%H:%M:%S')"
done

printf "\n${D}── DU LIEU LEN SERVER (CT2) ───────────────────────────────────────${X}\n"
journalctl -u iot-ct2-cambien --since "3 min ago" --no-pager -o cat 2>/dev/null \
  | grep "DA GUI" | tail -3 | sed 's/^/   /' \
  || printf "   (chua co lan gui nao trong 3 phut qua)\n"

printf "\n${D}── WEB ────────────────────────────────────────────────────────────${X}\n"
ip=$(tailscale ip -4 2>/dev/null | head -1)
printf "   http://%s:1880/ui   (HTTP %s)\n" "$ip" \
    "$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:1880/ui/")"
echo
