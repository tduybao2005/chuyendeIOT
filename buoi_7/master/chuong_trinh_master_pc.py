"""
Buoi 7 - Bai tap muc do 3 (10 diem)
"Raspberry Master" - chay tren MAY TINH (thay the Raspberry theo de bai:
"co the thay the bang may tinh").

De bai (Master):
    - Hien thi gia tri nhiet do, do am nhan duoc tu Slave ra cua so
      Terminal (nhan tu Slave moi 1 giay).
    - Thu thap va xac dinh gia tri trung binh cua nhiet do, do am trong
      moi 20 giay. Dong thoi gui du lieu trung binh nay len Server cua
      ThingSpeak sau moi 20 giay cho 1 goi tin. Viec gui goi tin len
      Server phai duoc thuc hien lien tuc trong it nhat 30 phut.
    - Sau moi 1 giay se gui tin hieu dieu khien 3 LED sang duoi lien tuc
      (Do -> Vang -> Xanh).
    - Nhom 3 (le) -> BAT BUOC dung UDP; frame phai co CRC
      (xem chi tiet cau truc frame trong buoi_7/protocol.py).

May tinh khong co GPIO nen Master CHI lam nhiem vu mang + hien thi +
gui ThingSpeak; 3 LED vat ly nam ben Slave, Master chi gui LENH dieu
khien qua mang (Slave chiu trach nhiem bat/tat LED that).

CAU HINH MANG + THINGSPEAK (dien vao truoc khi chay that, hien tai de
placeholder vi chua tao channel ThingSpeak de test):
    SLAVE_IP           = dia chi IP cua Raspberry Slave
    SLAVE_PORT         = cong UDP Slave dang lang nghe lenh dieu khien LED
                         (phai TRUNG voi SLAVE_LISTEN_PORT trong
                         slave/chuong_trinh_slave_pi.py)
    MASTER_LISTEN_PORT = cong UDP Master dung de lang nghe du lieu cam bien
                         (phai TRUNG voi MASTER_PORT trong
                         slave/chuong_trinh_slave_pi.py)
"""

import os
import sys
import socket
import threading
from time import sleep, monotonic
from datetime import datetime

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import protocol as proto

# ---------------------------------------------------------------------------
# Cau hinh mang
# ---------------------------------------------------------------------------
SLAVE_IP = "192.168.44.211"   # Pi "pi4-tdbao", IP LAN da test thuc te (2026-09-14).
                              # Neu Pi doi IP (DHCP) hoac chay tu mang khac, doi
                              # thanh "pi4-tdbao.local" hoac Tailscale IP 100.116.157.59
SLAVE_PORT = 6002            # phai trung SLAVE_LISTEN_PORT ben Slave
MASTER_LISTEN_PORT = 6001    # phai trung MASTER_PORT ben Slave

SEND_INTERVAL = 20           # gui trung binh len ThingSpeak moi 20s (dung theo de)
LED_CHASE_INTERVAL = 1       # gui lenh dieu khien LED moi 1s (dung theo de)
MIN_RUN_SECONDS = 30 * 60    # yeu cau de bai: gui lien tuc toi thieu 30 phut

# ---------------------------------------------------------------------------
# Thong tin ThingSpeak - HAY DIEN THONG TIN THAT CUA BAN VAO DAY TRUOC KHI CHAY
# (channel dung field1 = temperature, field2 = humidity)
# ---------------------------------------------------------------------------
THINGSPEAK_UPDATE_URL = "https://api.thingspeak.com/update.json"
THINGSPEAK_CHANNEL_ID = "DIEN_CHANNEL_ID_CUA_BAN"
THINGSPEAK_WRITE_API_KEY = "DIEN_WRITE_API_KEY_CUA_BAN"
FIELD_TEMP = "field1"
FIELD_HUMI = "field2"


def log_event(message):
    now_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{now_str}] {message}")


# ---------------------------------------------------------------------------
# Trang thai dung chung giua cac luong (bao ve bang lock)
# ---------------------------------------------------------------------------
lock = threading.Lock()
window = {"temp": [], "humi": []}


def note_sample(temp, humi):
    with lock:
        if temp is not None:
            window["temp"].append(temp)
        if humi is not None:
            window["humi"].append(humi)


def pop_window():
    with lock:
        data = {k: list(v) for k, v in window.items()}
        for v in window.values():
            v.clear()
    return data


# ---------------------------------------------------------------------------
# Luong 1: nhan du lieu cam bien tu Slave, hien thi ra Terminal
# ---------------------------------------------------------------------------
def sensor_listener(sock, stop_event):
    last_seq = None
    sock.settimeout(1.0)
    while not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(128)
        except socket.timeout:
            continue
        except OSError:
            break

        frame = proto.parse_frame(data)
        if frame is None:
            print("[UDP] Frame SENSOR_DATA hong (sai STX/ETX/CRC) - bo qua.")
            continue
        if frame["type"] != proto.TYPE_SENSOR_DATA:
            continue

        temp, humi, temp_valid, humi_valid = proto.decode_sensor_data(frame["payload"])
        log_event(f"Nhan tu Slave -> Nhiet do: {temp} C, Do am: {humi} %"
                   f"{'' if temp_valid and humi_valid else '  (co gia tri loi, khong tinh vao trung binh)'}")
        note_sample(temp, humi)


# ---------------------------------------------------------------------------
# Luong 2: gui lenh dieu khien 3 LED sang duoi Do -> Vang -> Xanh moi 1 giay
# ---------------------------------------------------------------------------
def led_chase_loop(sock, stop_event):
    seq = 0
    state = 0  # 0 = Do, 1 = Vang, 2 = Xanh
    while not stop_event.is_set():
        started = monotonic()

        red, yellow, green = (state == 0), (state == 1), (state == 2)
        frame = proto.encode_led_ctrl(seq, red, yellow, green)
        try:
            sock.sendto(frame, (SLAVE_IP, SLAVE_PORT))
        except OSError as e:
            print("[UDP] Gui lenh dieu khien LED loi:", e)
        seq = (seq + 1) & 0xFF
        state = (state + 1) % 3

        elapsed = monotonic() - started
        stop_event.wait(max(0.0, LED_CHASE_INTERVAL - elapsed))


# ---------------------------------------------------------------------------
# Gui trung binh 20s len ThingSpeak (HTTP) - mau lay tu buoi_6/raspberry/chuong_trinh_pi.py
# ---------------------------------------------------------------------------
def send_to_thingspeak(**fields):
    payload = {"api_key": THINGSPEAK_WRITE_API_KEY}
    payload.update(fields)
    for attempt in range(3):
        try:
            response = requests.post(THINGSPEAK_UPDATE_URL, json=payload, timeout=5)
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError) as e:
            print(f"[HTTP] Gui du lieu loi (lan thu {attempt + 1}):", e)
            result = 0
        if isinstance(result, dict) and result.get("entry_id"):
            return True
        if attempt < 2:
            sleep(3)
    print("[HTTP] Gui du lieu that bai sau nhieu lan thu.")
    return False


def send_window_average():
    data = pop_window()
    averages = {key: (sum(values) / len(values)) for key, values in data.items() if values}
    if not averages:
        print("[HTTP] Khong co du lieu hop le trong 20s vua qua, bo qua goi tin nay.")
        return
    fields = {}
    if "temp" in averages:
        fields[FIELD_TEMP] = round(averages["temp"], 1)
    if "humi" in averages:
        fields[FIELD_HUMI] = round(averages["humi"], 1)
    if send_to_thingspeak(**fields):
        log_event(f"Da gui trung binh 20s len ThingSpeak: {fields}")


# ---------------------------------------------------------------------------
# Vong lap chinh
# ---------------------------------------------------------------------------
def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", MASTER_LISTEN_PORT))

    stop_event = threading.Event()
    threading.Thread(target=sensor_listener, args=(sock, stop_event), daemon=True).start()
    threading.Thread(target=led_chase_loop, args=(sock, stop_event), daemon=True).start()

    run_start = monotonic()
    window_start = monotonic()
    min_run_logged = False
    try:
        while True:
            sleep(0.2)
            if monotonic() - window_start >= SEND_INTERVAL:
                send_window_average()
                window_start = monotonic()

            if not min_run_logged and monotonic() - run_start >= MIN_RUN_SECONDS:
                # Da dat yeu cau toi thieu de bai (>= 30 phut lien tuc);
                # van tiep tuc chay binh thuong, chi ghi log 1 lan de biet moc.
                log_event("Da chay lien tuc du toi thieu 30 phut theo yeu cau de bai.")
                min_run_logged = True
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
    finally:
        stop_event.set()
        sock.close()


if __name__ == '__main__':
    main()
