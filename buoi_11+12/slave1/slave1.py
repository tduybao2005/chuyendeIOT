"""
Buoi 11+12 - SLAVE 1 (pi4-tdbao): DHT11 + bien tro + khoang cach + LED1/LED2.

Moi 1 giay: doc 3 cam bien vao cua so trung binh; doc trang thai LED1/LED2
va publish ngay len buoi11/slave1/trang_thai. Du 20 mau -> publish 1 goi
trung binh len buoi11/slave1/trung_binh. Subscribe buoi11/dieu_khien
(master publish, retain) de bat/tat LED1, LED2.

Cam day (Grove Base Hat):
    DHT11        -> D5   (GPIO5)
    Khoang cach  -> D16  (GPIO16)
    LED 1        -> D18  (GPIO18)
    LED 2        -> D22  (GPIO22)
    Bien tro     -> A0   (ADC kenh 0)

Chay (cung thu muc voi trung_binh.py):
    IOT_MQTT_HOST=192.168.44.179 python3 slave1.py
"""

import json
import os
import time

import paho.mqtt.client as mqtt
from gpiozero import LED
from grove.adc import ADC
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger
from seeed_dht import DHT

from trung_binh import CuaSoTrungBinh

MQTT_HOST = os.environ.get("IOT_MQTT_HOST", "192.168.44.179")
MQTT_PORT = int(os.environ.get("IOT_MQTT_PORT", "1883"))
TRUNG_BINH = "buoi11/slave1/trung_binh"
TRANG_THAI = "buoi11/slave1/trang_thai"
DIEU_KHIEN = "buoi11/dieu_khien"

dht = DHT("11", 5)
sieu_am = GroveUltrasonicRanger(16)
adc = ADC(0x08)
led = {"led1": LED(18), "led2": LED(22)}


def doc_dht():
    try:
        do_am, nhiet_do = dht.read()
        do_am, nhiet_do = float(do_am), float(nhiet_do)
    except Exception as loi:
        print("Loi doc DHT11:", loi)
        return None, None
    # DHT11 do 0-50 C, 20-95 %; ngoai khoang (vd 0/0 khi chua doc duoc lan nao) = doc hong
    if not (0 <= nhiet_do <= 50 and 20 <= do_am <= 95):
        return None, None
    return nhiet_do, do_am


def doc_bien_tro():
    try:
        return round(adc.read_voltage(0) / 1000, 3)  # mV -> V (0-3.3)
    except Exception as loi:
        print("Loi doc bien tro:", loi)
        return None


def doc_khoang_cach():
    # KHONG goi get_distance(): ham do lap VO HAN khi khong co tieng vong (rut
    # cam bien / vat qua xa). _get_distance() do 1 lan, het gio thi tra None.
    for _ in range(3):
        try:
            kc = sieu_am._get_distance()
        except Exception:
            kc = None
        if kc is not None and 2 <= kc <= 400:
            return round(kc, 1)
    return None


def on_connect(client, userdata, connect_flags, reason_code, properties=None):
    print("Da ket noi MQTT:", reason_code)
    client.subscribe(DIEU_KHIEN, qos=1)


def on_message(client, userdata, msg):
    try:
        lenh = json.loads(msg.payload)
        for ten, bong in led.items():
            if ten in lenh:
                bong.on() if lenh[ten] else bong.off()
    except Exception as loi:
        print("Lenh hong:", loi, msg.payload)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="slave1-buoi11")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect_async(MQTT_HOST, MQTT_PORT)  # broker chua len cung khong chet, tu ket noi lai
    client.loop_start()
    print(f"Slave 1 -> MQTT {MQTT_HOST}:{MQTT_PORT}")

    cua_so = CuaSoTrungBinh()
    nhip = time.monotonic()
    try:
        while True:
            nhiet_do, do_am = doc_dht()
            mau = {"nhiet_do": nhiet_do, "do_am": do_am, "bien_tro": doc_bien_tro(), "khoang_cach": doc_khoang_cach()}
            trang_thai = {ten: int(bong.is_lit) for ten, bong in led.items()}
            client.publish(TRANG_THAI, json.dumps(trang_thai), qos=1)
            trung_binh = cua_so.them(mau)
            if trung_binh:
                client.publish(TRUNG_BINH, json.dumps(trung_binh), qos=1)
                print("[GUI TRUNG BINH 20s]", trung_binh)
            print(mau, trang_thai)

            nhip += 1
            con_lai = nhip - time.monotonic()
            if con_lai > 0:
                time.sleep(con_lai)
            else:
                nhip = time.monotonic()  # DHT doc lai lau hon 1 s -> khong don nhip bu
    except KeyboardInterrupt:
        print("\nDa dung slave 1.")
    finally:
        for bong in led.values():
            bong.off()
        client.loop_stop()


if __name__ == "__main__":
    main()
