"""
Buoi 8 - Bai tap muc do 3: chuong trinh Raspberry Pi.

Vong lap: dieu khien 3 LED chay duoi (khong lien quan nhiet do), doc DHT11,
POST ca 5 gia tri len HTTP Server (server/server.py), roi GET doc lai dung
ban ghi vua luu de in ra terminal va ghi vao file log.

QUAN TRONG: gia tri in ra terminal va ghi vao file log la gia tri DOC VE TU
SERVER (qua GET), khong phai bien cuc bo Pi vua dung de dieu khien LED. Lam
vong nhu vay moi chung minh duoc ca hai chieu API (GUI bang POST, DOC bang
GET) deu chay that - in bien cuc bo thi man hinh van dep y het ke ca khi
server/Atlas dang chet.

So do noi day (Grove Base Hat tren Raspberry Pi 4):
    DHT11     -> D5   (GPIO5)   nhiet do + do am
    LED do    -> D16  (GPIO16)  buoc 0 cua vong duoi
    LED vang  -> D22  (GPIO22)  buoc 1
    LED xanh  -> D24  (GPIO24)  buoc 2

Truoc khi chay, dien dia chi server va khoa API (giong het server/.env)
bang bien moi truong:

    export IOT_SERVER="http://<ip-may-chay-server>:8000"
    export IOT_API_KEY="khoa-giong-het-server/.env"
    python3 chuong_trinh_pi.py
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from time import sleep

import requests
from gpiozero import LED
from seeed_dht import DHT

# ---------------------------------------------------------------------------
# Cau hinh
# ---------------------------------------------------------------------------
SERVER_URL = os.environ.get("IOT_SERVER", "http://192.168.1.100:8000").rstrip("/") + "/du-lieu"
API_KEY = os.environ.get("IOT_API_KEY", "")
TEN_THIET_BI = os.environ.get("IOT_TEN_THIET_BI", os.uname().nodename)

CHAN_DHT = 5
CHAN_LED_DO = 16
CHAN_LED_VANG = 22
CHAN_LED_XANH = 24

NHIP_GIAY = 1  # dieu khien den + doc cam bien + gui + doc lai moi 1 giay

FILE_LOG = Path(__file__).with_name("nhat_ky.csv")
COT_LOG = ["id", "thoi_gian_gui", "ten_thiet_bi", "nhiet_do", "do_am", "led1", "led2", "led3"]

# ---------------------------------------------------------------------------
# Phan cung
# ---------------------------------------------------------------------------
cam_bien = DHT("11", CHAN_DHT)
den = (LED(CHAN_LED_DO), LED(CHAN_LED_VANG), LED(CHAN_LED_XANH))
TEN_DEN = ("DO", "VANG", "XANH")


def doc_cam_bien():
    try:
        do_am, nhiet_do = cam_bien.read()
        return float(nhiet_do), float(do_am)
    except Exception as loi:
        print("Loi doc DHT11:", loi)
        return None, None


def den_dang_sang(buoc):
    """Den duoi: moi buoc chi mot den sang, xoay vong qua 3 den."""
    vi_tri = buoc % len(den)
    return tuple(1 if i == vi_tri else 0 for i in range(len(den)))


def cap_nhat_den(trang_thai):
    for bong, bat in zip(den, trang_thai):
        bong.on() if bat else bong.off()


def gui_va_doc_lai(nhiet_do, do_am, led1, led2, led3):
    """POST du lieu len server, roi GET doc lai chinh ban ghi vua luu."""
    du_lieu = {
        "ten_thiet_bi": TEN_THIET_BI,
        "nhiet_do": nhiet_do,
        "do_am": do_am,
        "led1": led1,
        "led2": led2,
        "led3": led3,
    }
    header = {"X-API-Key": API_KEY}
    requests.post(SERVER_URL, json=du_lieu, headers=header, timeout=5).raise_for_status()

    phan_hoi = requests.get(SERVER_URL, params={"n": 1}, headers=header, timeout=5)
    phan_hoi.raise_for_status()
    ban_ghi = phan_hoi.json()["ban_ghi"]
    return ban_ghi[0] if ban_ghi else None


def mo_ta_den(ban_ghi):
    dang_sang = [TEN_DEN[i] for i in range(3) if ban_ghi.get(f"led{i + 1}")]
    return "+".join(dang_sang) if dang_sang else "TAT"


def gio_de_doc(chuoi_thoi_gian):
    """'2026-09-20T10:00:00+07:00' -> '2026-09-20 10:00:00'."""
    return str(chuoi_thoi_gian).replace("T", " ").split("+")[0].split(".")[0]


def in_ra_terminal(vong, ban_ghi):
    """In MOT dong ra terminal - toan bo gia tri lay tu ban_ghi (ket qua GET), khong
    dung bien cuc bo led1/led2/led3 ma Pi vua dung de dieu khien phan cung."""
    print(
        f"[{vong:4}] {mo_ta_den(ban_ghi):<4} | "
        f"[{gio_de_doc(ban_ghi['thoi_gian_gui'])}] {ban_ghi['ten_thiet_bi']:<12} "
        f"nhiet do {ban_ghi['nhiet_do']:>5} C | do am {ban_ghi['do_am']:>5} % | "
        f"LED(do,vang,xanh) {ban_ghi['led1']}{ban_ghi['led2']}{ban_ghi['led3']} | "
        f"ID {ban_ghi['id']}"
    )


def ghi_log(ban_ghi):
    """Ghi THEM mot dong vao file CSV - cung tu ban_ghi (ket qua GET), y het du
    lieu vua in ra terminal, khong phai gia tri cuc bo cua Pi."""
    can_tao_header = not FILE_LOG.exists() or FILE_LOG.stat().st_size == 0
    with FILE_LOG.open("a", newline="", encoding="utf-8") as tep:
        writer = csv.writer(tep)
        if can_tao_header:
            writer.writerow(COT_LOG)
        writer.writerow([ban_ghi.get(cot, "") for cot in COT_LOG])


def main():
    if not API_KEY:
        print("Thieu IOT_API_KEY")
        return
    print(f"Server: {SERVER_URL} | thiet bi: {TEN_THIET_BI} | nhip {NHIP_GIAY}s | log: {FILE_LOG}")

    vong = 0
    try:
        while True:
            vong += 1
            led1, led2, led3 = den_dang_sang(vong - 1)
            cap_nhat_den((led1, led2, led3))

            nhiet_do, do_am = doc_cam_bien()
            if nhiet_do is not None and do_am is not None:
                try:
                    ban_ghi = gui_va_doc_lai(nhiet_do, do_am, led1, led2, led3)
                    if ban_ghi:
                        in_ra_terminal(vong, ban_ghi)
                        ghi_log(ban_ghi)
                except requests.RequestException as loi:
                    print(f"[{vong:4}] Loi goi server:", loi)

            sleep(NHIP_GIAY)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
    finally:
        for bong in den:
            bong.off()


if __name__ == "__main__":
    main()
