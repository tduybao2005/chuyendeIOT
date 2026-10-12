"""
Buoi 11+12 - GATEWAY (pi4-tdbao): cau noi MQTT (master) <-> UDP (slave 2).

- Subscribe buoi11/dieu_khien -> gui lenh led3/buzzer/relay/light/alarm cho
  slave 2 qua UDP (cong 5005) ngay khi co lenh moi, va NHAC LAI moi 1 giay:
  UDP co the mat goi, lenh la TRANG THAI (0/1) nen gui lap lai khong sao.
- Nhan UDP tu slave 2 (cong 5006) {"loai": "trang_thai"|"trung_binh", ...}
  -> publish len buoi11/slave2/<loai> cho master.

Chay:
    IOT_MQTT_HOST=192.168.44.179 IOT_SLAVE2_HOST=192.168.44.176 python3 gateway.py
"""

import json
import os
import socket
import threading
from time import sleep

import paho.mqtt.client as mqtt

MQTT_HOST = os.environ.get("IOT_MQTT_HOST", "192.168.44.179")
MQTT_PORT = int(os.environ.get("IOT_MQTT_PORT", "1883"))
SLAVE2_HOST = os.environ.get("IOT_SLAVE2_HOST", "192.168.44.176")
CONG_SLAVE2 = 5005  # slave 2 nghe lenh
CONG_GATEWAY = 5006  # gateway nghe du lieu slave 2
DIEU_KHIEN = "buoi11/dieu_khien"
LENH_SLAVE2 = ("led3", "buzzer", "relay", "light", "alarm")
LOAI_HOP_LE = ("trang_thai", "trung_binh")

lenh = {}  # rong cho toi khi master gui lenh dau tien
khoa = threading.Lock()
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind(("0.0.0.0", CONG_GATEWAY))


def gui_lenh():
    with khoa:
        if not lenh:
            return
        goi = json.dumps(lenh).encode()
    try:
        udp.sendto(goi, (SLAVE2_HOST, CONG_SLAVE2))
    except OSError as loi:
        print("Khong gui duoc UDP toi slave 2:", loi)


def on_connect(client, userdata, connect_flags, reason_code, properties=None):
    print("Da ket noi MQTT:", reason_code)
    client.subscribe(DIEU_KHIEN, qos=1)


def on_message(client, userdata, msg):
    try:
        du_lieu = json.loads(msg.payload)
        with khoa:
            lenh.update({ten: int(du_lieu[ten]) for ten in LENH_SLAVE2 if ten in du_lieu})
    except Exception as loi:
        print("Lenh hong:", loi, msg.payload)
        return
    gui_lenh()
    print("Lenh moi cho slave 2:", lenh)


def vong_nhac_lenh():
    while True:
        gui_lenh()
        sleep(1)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="gateway-buoi11")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect_async(MQTT_HOST, MQTT_PORT)
    client.loop_start()
    threading.Thread(target=vong_nhac_lenh, daemon=True).start()
    print(f"Gateway: MQTT {MQTT_HOST}:{MQTT_PORT} | slave 2 {SLAVE2_HOST}:{CONG_SLAVE2} | nghe UDP :{CONG_GATEWAY}")
    try:
        while True:
            goi, dia_chi = udp.recvfrom(2048)
            try:
                du_lieu = json.loads(goi)
                loai = du_lieu.pop("loai")
                if loai not in LOAI_HOP_LE:
                    raise ValueError(f"loai la: {loai}")
            except Exception as loi:
                print("Goi UDP hong tu", dia_chi, loi)
                continue
            client.publish(f"buoi11/slave2/{loai}", json.dumps(du_lieu), qos=1)
            print(f"[slave2 -> {loai}]", du_lieu)
    except KeyboardInterrupt:
        print("\nDa dung gateway.")
    finally:
        client.loop_stop()


if __name__ == "__main__":
    main()
