"""
Buoi 9 - Bai tap muc do 3: chuong trinh Raspberry Pi (MQTT).

Moi chu ky: dieu khien 3 LED chay duoi, doc DHT11, PUBLISH ca "tung du
lieu" (5 tin nhan rieng, moi tin 1 truong) lan "toan bo du lieu" (1 tin
nhan gom du 5 truong) len broker MQTT - doi dinh dang json/form-urlencoded
xen ke moi chu ky de bai qua het ca 4 to hop {tung,toanbo}x{json,form}.

Dong thoi SUBSCRIBE san 4 topic "doc" (tung/toanbo x json/form) - moi khi
co du lieu moi (do server phat lai sau khi luu Database), on_message() in
ra terminal. Day la dữ liệu THAT SU doc duoc tu server (qua broker), khong
phai bien cuc bo Pi vua dung de dieu khien phan cung.

So do noi day (Grove Base Hat tren Raspberry Pi 4) - giong buoi 8:
    DHT11     -> D5   (GPIO5)   nhiet do + do am
    LED do    -> D16  (GPIO16)  buoc 0 cua vong duoi
    LED vang  -> D22  (GPIO22)  buoc 1
    LED xanh  -> D24  (GPIO24)  buoc 2

Truoc khi chay, dien dia chi broker (may chay server buoi_9):

    export IOT_MQTT_HOST="<ip-may-chay-server>"
    python3 chuong_trinh_pi.py
"""

import json
import os
from time import sleep
from urllib.parse import parse_qsl, urlencode

import paho.mqtt.client as mqtt
from gpiozero import LED
from seeed_dht import DHT

# ---------------------------------------------------------------------------
# Cau hinh
# ---------------------------------------------------------------------------
MQTT_HOST = os.environ.get("IOT_MQTT_HOST", "192.168.1.100")
MQTT_PORT = int(os.environ.get("IOT_MQTT_PORT", "1883"))
TEN_THIET_BI = os.environ.get("IOT_TEN_THIET_BI", os.uname().nodename)

CHAN_DHT = 5
CHAN_LED_DO = 16
CHAN_LED_VANG = 22
CHAN_LED_XANH = 24

NHIP_GIAY = 1  # dieu khien den + doc cam bien + gui moi 1 giay

# 8 topic = {gui, doc} x {tung, toanbo} x {json, form} - giong het server.py
GUI_TUNG = {"json": "buoi9/gui/tung/json", "form": "buoi9/gui/tung/form"}
GUI_TOANBO = {"json": "buoi9/gui/toanbo/json", "form": "buoi9/gui/toanbo/form"}
DOC_TOPICS = (
    "buoi9/doc/tung/json",
    "buoi9/doc/tung/form",
    "buoi9/doc/toanbo/json",
    "buoi9/doc/toanbo/form",
)

# ---------------------------------------------------------------------------
# Phan cung
# ---------------------------------------------------------------------------
cam_bien = DHT("11", CHAN_DHT)
den = (LED(CHAN_LED_DO), LED(CHAN_LED_VANG), LED(CHAN_LED_XANH))


def doc_cam_bien():
    try:
        do_am, nhiet_do = cam_bien.read()
        return float(nhiet_do), float(do_am)
    except Exception as loi:
        print("Loi doc DHT11:", loi)
        return None, None


def den_dang_sang(buoc):
    vi_tri = buoc % len(den)
    return tuple(1 if i == vi_tri else 0 for i in range(len(den)))


def cap_nhat_den(trang_thai):
    for bong, bat in zip(den, trang_thai):
        bong.on() if bat else bong.off()


# ---------------------------------------------------------------------------
# Ma hoa / giai ma json va form-urlencoded (giong het server.py)
# ---------------------------------------------------------------------------
def ma_hoa(du_lieu, dinh_dang):
    if dinh_dang == "json":
        return json.dumps(du_lieu)
    return urlencode(du_lieu)


def giai_ma(payload, dinh_dang):
    chuoi = payload.decode("utf-8")
    if dinh_dang == "json":
        return json.loads(chuoi)
    return dict(parse_qsl(chuoi))


# ---------------------------------------------------------------------------
# Subscribe cac topic "doc" - in ra du lieu THAT SU doc ve tu server
# ---------------------------------------------------------------------------
def on_connect(client, userdata, connect_flags, reason_code, properties=None):
    print("Da ket noi broker MQTT, ma:", reason_code)
    for topic in DOC_TOPICS:
        client.subscribe(topic, qos=1)


def on_message(client, userdata, msg):
    dinh_dang = "json" if msg.topic.endswith("/json") else "form"
    try:
        du_lieu = giai_ma(msg.payload, dinh_dang)
    except Exception as loi:
        print(f"[doc] {msg.topic}: khong giai ma duoc ({loi})")
        return
    print(f"[doc] {msg.topic}: {du_lieu}")


# ---------------------------------------------------------------------------
# Vong lap chinh - publish "tung" (5 tin) + "toan bo" (1 tin) moi chu ky
# ---------------------------------------------------------------------------
def gui_tung(client, dinh_dang, nhiet_do, do_am, led1, led2, led3):
    cac_truong = {"nhiet_do": nhiet_do, "do_am": do_am, "led1": led1, "led2": led2, "led3": led3}
    for ten_truong, gia_tri in cac_truong.items():
        goi_tin = {"ten_thiet_bi": TEN_THIET_BI, "ten_truong": ten_truong, "gia_tri": gia_tri}
        client.publish(GUI_TUNG[dinh_dang], ma_hoa(goi_tin, dinh_dang), qos=1)


def gui_toanbo(client, dinh_dang, nhiet_do, do_am, led1, led2, led3):
    goi_tin = {
        "ten_thiet_bi": TEN_THIET_BI,
        "nhiet_do": nhiet_do,
        "do_am": do_am,
        "led1": led1,
        "led2": led2,
        "led3": led3,
    }
    client.publish(GUI_TOANBO[dinh_dang], ma_hoa(goi_tin, dinh_dang), qos=1)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=TEN_THIET_BI)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_start()  # luong nen: nhan tin nhan "doc" chay song song vong lap gui

    print(f"Broker: {MQTT_HOST}:{MQTT_PORT} | thiet bi: {TEN_THIET_BI} | nhip {NHIP_GIAY}s")

    vong = 0
    try:
        while True:
            vong += 1
            led1, led2, led3 = den_dang_sang(vong - 1)
            cap_nhat_den((led1, led2, led3))

            nhiet_do, do_am = doc_cam_bien()
            if nhiet_do is not None and do_am is not None:
                # Xen ke json/form moi chu ky - qua 2 chu ky la gui du ca 4
                # to hop {tung,toanbo} x {json,form}.
                dinh_dang = "json" if vong % 2 else "form"
                gui_tung(client, dinh_dang, nhiet_do, do_am, led1, led2, led3)
                gui_toanbo(client, dinh_dang, nhiet_do, do_am, led1, led2, led3)
                print(
                    f"[{vong:4}] gui ({dinh_dang}) {nhiet_do} C, {do_am}% "
                    f"LED(do,vang,xanh)={led1}{led2}{led3}"
                )

            sleep(NHIP_GIAY)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
    finally:
        client.loop_stop()
        for bong in den:
            bong.off()


if __name__ == "__main__":
    main()
