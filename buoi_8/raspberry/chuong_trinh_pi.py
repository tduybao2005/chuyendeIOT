"""
Buoi 8 - Bai tap muc do 3: chuong trinh Raspberry Pi.

Doc DHT11 (nhiet do, do am), bat 3 LED theo nguong nhiet do, roi gui ca 5
gia tri do len HTTP Server (server/server.py) va doc lai ban ghi vua luu de
in ra terminal - chung minh duong di GUI va duong DOC toi Database deu chay
duoc that.

So do noi day (Grove Base Hat tren Raspberry Pi 4):
    DHT11     -> D5   (GPIO5)   nhiet do + do am
    LED do    -> D16  (GPIO16)  sang khi nhiet do >= NGUONG_NONG (NONG)
    LED vang  -> D22  (GPIO22)  sang khi NGUONG_AM <= nhiet do < NGUONG_NONG (AM)
    LED xanh  -> D24  (GPIO24)  sang khi nhiet do < NGUONG_AM (MAT)

Truoc khi chay, dien dia chi server va khoa API (giong het server/.env)
bang bien moi truong:

    export IOT_SERVER="http://<ip-may-chay-server>:8000"
    export IOT_API_KEY="khoa-giong-het-server/.env"
    python3 chuong_trinh_pi.py
"""

import os
from datetime import datetime
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

NGUONG_AM = 28  # do C - duoi nguong nay la MAT (LED xanh)
NGUONG_NONG = 32  # do C - tu nguong nay tro len la NONG (LED do)

NHIP_GIAY = 5  # doc cam bien + gui + doc lai moi 5 giay

# ---------------------------------------------------------------------------
# Phan cung
# ---------------------------------------------------------------------------
cam_bien = DHT("11", CHAN_DHT)
led_do = LED(CHAN_LED_DO)
led_vang = LED(CHAN_LED_VANG)
led_xanh = LED(CHAN_LED_XANH)


def doc_cam_bien():
    try:
        do_am, nhiet_do = cam_bien.read()
        return float(nhiet_do), float(do_am)
    except Exception as loi:
        print("Loi doc DHT11:", loi)
        return None, None


def cap_nhat_led(nhiet_do):
    """Bat/tat 3 LED theo nguong nhiet do, tra ve trang thai (0/1) de gui len server."""
    nong = nhiet_do is not None and nhiet_do >= NGUONG_NONG
    am = nhiet_do is not None and NGUONG_AM <= nhiet_do < NGUONG_NONG
    mat = nhiet_do is not None and nhiet_do < NGUONG_AM
    led_do.on() if nong else led_do.off()
    led_vang.on() if am else led_vang.off()
    led_xanh.on() if mat else led_xanh.off()
    return int(nong), int(am), int(mat)


def gui_va_doc_lai(nhiet_do, do_am, led1, led2, led3):
    """POST du lieu len server, roi GET doc lai ban ghi vua luu."""
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


def main():
    if not API_KEY:
        print("Thieu IOT_API_KEY")
        return
    print(f"Server: {SERVER_URL} | thiet bi: {TEN_THIET_BI} | nhip {NHIP_GIAY}s")

    try:
        while True:
            nhiet_do, do_am = doc_cam_bien()
            led1, led2, led3 = cap_nhat_led(nhiet_do)

            if nhiet_do is not None and do_am is not None:
                gio = datetime.now().strftime("%H:%M:%S")
                try:
                    ban_ghi = gui_va_doc_lai(nhiet_do, do_am, led1, led2, led3)
                    print(
                        f"[{gio}] gui {nhiet_do} C, {do_am}% LED(do,vang,xanh)="
                        f"{led1}{led2}{led3} -> server tra ve: {ban_ghi}"
                    )
                except requests.RequestException as loi:
                    print(f"[{gio}] Loi goi server:", loi)

            sleep(NHIP_GIAY)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
    finally:
        led_do.off()
        led_vang.off()
        led_xanh.off()


if __name__ == "__main__":
    main()
