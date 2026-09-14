"""
Buoi 7 - Bai tap muc do 3 (10 diem)
Raspberry "Slave"

De bai (Slave):
    - Doc gia tri nhiet do, do am cua moi truong va hien thi len LCD 16x2
      moi 1 giay.
    - Gui du lieu nhiet do, do am nay den Master moi 1 giay.
    - Nhan tin hieu dieu khien tu Master de thay doi trang thai hoat dong
      cua 3 LED.
    - Nhom 3 (le) -> BAT BUOC dung UDP; frame phai co CRC
      (xem chi tiet cau truc frame trong buoi_7/protocol.py).

So do noi day (GPIO / cong Grove) - lay theo dung cac file cu trong repo:
    DHT (nhiet do, do am)  -> D5   (GPIO5)   [giong buoi_6/raspberry/chuong_trinh_pi.py]
    LCD 16x2 (JHD1802, RGB backlight) -> I2C-1, 0x3E (man hinh) + 0x62 (den nen)
                                         [giong buoi_6/raspberry/chuong_trinh_pi.py]
    LED do    -> D16 (GPIO16)   [giong buoi_1/muc_do_3.py, module 1]
    LED vang  -> D22 (GPIO22)   [da doi cho voi GPIO24 sau khi test thuc te
                                 ngay 2026-09-14: day that tren Pi pi4-tdbao
                                 co LED vang o GPIO22, LED xanh o GPIO24]
    LED xanh  -> D24 (GPIO24)

    Ghi chu: anh de bai co chup them 1 module nut nhan (button) canh cam
    bien DHT, nhung noi dung de muc do 3 KHONG mo ta chuc nang nao cho nut
    nhan o phia Slave nen file nay CHUA dau day/dung toi no. Neu can dung,
    chi can them "from gpiozero import Button" + "button = Button(<pin>)"
    theo dung mau o buoi_1/muc_do_3.py.

CAU HINH MANG (dien vao truoc khi chay that, hien tai de placeholder vi
chua co Master de test):
    MASTER_IP   = dia chi IP cua may tinh dong vai tro Master
    MASTER_PORT = cong UDP Master dung de LANG NGHE du lieu cam bien
    SLAVE_LISTEN_PORT = cong UDP Slave dung de LANG NGHE lenh dieu khien LED
"""

import os
import sys
import socket
import threading
from time import sleep, monotonic
from datetime import datetime

from seeed_dht import DHT
from gpiozero import LED
import smbus2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import protocol as proto

# ---------------------------------------------------------------------------
# Cau hinh mang
# ---------------------------------------------------------------------------
MASTER_IP = "192.168.44.206"  # May tinh dong vai tro Master, da test thuc te (2026-09-14).
                              # Neu doi sang may khac lam Master, doi lai IP nay.
MASTER_PORT = 6001          # Slave gui du lieu cam bien den cong nay ben Master
SLAVE_LISTEN_PORT = 6002    # Slave lang nghe lenh dieu khien LED tu Master o cong nay

SAMPLE_INTERVAL = 1  # doc cam bien + gui du lieu moi 1 giay (dung theo de bai)

TEMP_RANGE = (0, 100)
HUMI_RANGE = (20, 95)


def log_event(message):
    now_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{now_str}] {message}")


def is_valid(value, min_val, max_val):
    return value is not None and min_val <= value <= max_val


def seq_is_newer(new_seq, old_seq):
    """So sanh 2 so thu tu 1 byte (0..255) co xet vong (wrap-around).

    Dung de Slave khong ap dung nham 1 goi LED_CTRL den TRE hoac bi
    TRUNG LAP (UDP khong dam bao thu tu/khong lap lai goi) so voi goi
    da xu ly gan nhat.
    """
    if old_seq is None:
        return True
    diff = (new_seq - old_seq) & 0xFF
    return 0 < diff < 128


# ---------------------------------------------------------------------------
# Cam bien nhiet do / do am (giong buoi_6/raspberry/chuong_trinh_pi.py)
# ---------------------------------------------------------------------------
sensor_temp_humi = DHT('11', 5)


def read_temp_humi():
    try:
        humi_raw, temp_raw = sensor_temp_humi.read()
        humi_raw, temp_raw = int(humi_raw), int(temp_raw)
    except Exception as e:
        print("Loi doc DHT:", e)
        return None, None
    temp = temp_raw if is_valid(temp_raw, *TEMP_RANGE) else None
    humi = humi_raw if is_valid(humi_raw, *HUMI_RANGE) else None
    return temp, humi


# ---------------------------------------------------------------------------
# LCD 16x2 (JHD1802 - man hinh 0x3E, den nen RGB 0x62)
# Copy nguyen tu buoi_6/raspberry/chuong_trinh_pi.py (da chay on dinh thuc te)
# ---------------------------------------------------------------------------
class JHD1802:
    def __init__(self, text_addr=0x3E, rgb_addr=0x62):
        self.bus = smbus2.SMBus(1)
        self.text_addr = text_addr
        self.rgb_addr = rgb_addr
        try:
            self._set_rgb_backlight(255, 255, 255)
            self.textCommand(0x38)
            self.textCommand(0x0C)
            self.textCommand(0x01)
            sleep(0.1)
        except Exception as e:
            print("Loi khoi tao LCD/Den nen:", e)

    def _set_rgb_backlight(self, r, g, b):
        try:
            self.bus.write_byte_data(self.rgb_addr, 0, 0)
            self.bus.write_byte_data(self.rgb_addr, 1, 0)
            self.bus.write_byte_data(self.rgb_addr, 0x08, 0xAA)
            self.bus.write_byte_data(self.rgb_addr, 4, r)
            self.bus.write_byte_data(self.rgb_addr, 3, g)
            self.bus.write_byte_data(self.rgb_addr, 2, b)
        except Exception:
            pass

    def textCommand(self, cmd):
        try:
            self.bus.write_byte_data(self.text_addr, 0x80, cmd)
        except Exception:
            pass

    def setCursor(self, row, column):
        val = (0x40 * row) + (column % 0x10) + 0x80
        self.textCommand(val)

    def write(self, msg):
        for c in msg:
            try:
                self.bus.write_byte_data(self.text_addr, 0x40, ord(c))
            except Exception:
                pass

    def clear(self):
        self.textCommand(0x01)
        sleep(0.05)


lcd = JHD1802()


def show_lcd(temp, humi):
    temp_str = f'{temp:>3}' if temp is not None else ' Er'
    humi_str = f'{humi:>3}' if humi is not None else ' Er'
    lcd.setCursor(0, 0)
    lcd.write('Nhiet do: {0} C '.format(temp_str))
    lcd.setCursor(1, 0)
    lcd.write('Do am   : {0} % '.format(humi_str))


# ---------------------------------------------------------------------------
# 3 LED dieu khien tu Master (giong buoi_1/muc_do_3.py ve cach dung gpiozero.LED)
# ---------------------------------------------------------------------------
led_red = LED(16)
led_yellow = LED(22)
led_green = LED(24)


def apply_led_mask(red, yellow, green):
    led_red.on() if red else led_red.off()
    led_yellow.on() if yellow else led_yellow.off()
    led_green.on() if green else led_green.off()


def leds_off():
    led_red.off()
    led_yellow.off()
    led_green.off()


# ---------------------------------------------------------------------------
# Mang: nhan lenh dieu khien LED tu Master (luong rieng)
# ---------------------------------------------------------------------------
def led_control_listener(sock, stop_event):
    """Lang nghe lien tuc frame LED_CTRL tu Master, chay o luong rieng de
    khong lam cham nhip doc cam bien/hien thi LCD o vong lap chinh."""
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
            print("[UDP] Frame LED_CTRL hong (sai STX/ETX/CRC) - bo qua.")
            continue
        if frame["type"] != proto.TYPE_LED_CTRL:
            continue
        if not seq_is_newer(frame["seq"], last_seq):
            continue  # goi den tre hoac trung lap so voi goi da ap dung
        last_seq = frame["seq"]

        red, yellow, green = proto.decode_led_ctrl(frame["payload"])
        apply_led_mask(red, yellow, green)


# ---------------------------------------------------------------------------
# Vong lap chinh
# ---------------------------------------------------------------------------
def main():
    lcd.clear()
    leds_off()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", SLAVE_LISTEN_PORT))

    stop_event = threading.Event()
    listener_thread = threading.Thread(
        target=led_control_listener, args=(sock, stop_event), daemon=True)
    listener_thread.start()

    seq = 0
    try:
        while True:
            started = monotonic()

            temp, humi = read_temp_humi()
            show_lcd(temp, humi)

            frame = proto.encode_sensor_data(
                seq, temp, humi, temp is not None, humi is not None)
            try:
                sock.sendto(frame, (MASTER_IP, MASTER_PORT))
            except OSError as e:
                print("[UDP] Gui du lieu cam bien loi:", e)
            seq = (seq + 1) & 0xFF

            elapsed = monotonic() - started
            sleep(max(0.0, SAMPLE_INTERVAL - elapsed))
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
    finally:
        stop_event.set()
        leds_off()
        sock.close()


if __name__ == '__main__':
    main()
