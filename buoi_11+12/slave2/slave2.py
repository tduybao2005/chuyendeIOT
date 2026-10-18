"""
Buoi 11+12 - SLAVE 2 (Pi nhom 3): LED3 + Buzzer + Relay + cam bien anh sang
+ LCD, va USB LoRa noi toi IoT node 3 (Light / Alarm Light, giong buoi 10).

3 luong:
  - chinh (moi 1 giay): doc anh sang + trang thai LED3/Buzzer/Relay + Light/
    Alarm (lan doc LoRa gan nhat) -> UDP {"loai":"trang_thai",...} toi gateway,
    hien len LCD; du 20 mau -> UDP {"loai":"trung_binh","anh_sang",...}.
  - vong_nhan_lenh: UDP cong 5005 tu gateway -> bat/tat LED3/Buzzer/Relay
    ngay, ghi nho lenh Light/Alarm cho luong LoRa.
  - vong_lora: ghi Light (reg 9) / Alarm (reg 8), ghi lai moi ~2 giay. Rieng
    1 luong de ghi LoRa cham/loi khong lam tre vong 1 giay.

Cam day (Grove Base Hat):
    LED 3              -> D18  (GPIO18)
    Buzzer             -> D24  (GPIO24)
    Relay              -> D26  (GPIO26)
    Cam bien anh sang  -> A0   (ADC kenh 0)
    LCD 16x2 JHD1802   -> I2C
    USB LoRa           -> cong USB (/dev/ttyUSB0)

Chay (cung thu muc voi trung_binh.py, IoT_Driver_USB.py):
    IOT_GATEWAY_HOST=192.168.44.211 python3 slave2.py
"""

import json
import os
import socket
import threading
import time

from gpiozero import LED, Buzzer, OutputDevice
from grove.adc import ADC

try:
    from grove.display.jhd1802 import JHD1802
except ImportError:
    # grove.py ban cu (0.6) khong co grove.display -> tu gui lenh I2C cho LCD,
    # giong het grove/display/jhd1802.py ban moi.
    import smbus2

    class JHD1802:
        def __init__(self, address=0x3E):
            self._bus = smbus2.SMBus(1)
            self._addr = address
            self._bus.write_byte(address, 0)  # chua cam LCD -> OSError
            self._lenh(0x02)
            time.sleep(0.1)
            self._lenh(0x08 | 0x04)  # bat man hinh, khong hien con tro
            self._lenh(0x28)  # 2 dong

        def _lenh(self, ma):
            self._bus.write_byte_data(self._addr, 0x80, ma)

        def clear(self):
            self._lenh(0x01)
            time.sleep(0.002)

        def setCursor(self, dong, cot):
            self._lenh(0x40 * dong + cot % 0x10 + 0x80)

        def write(self, chuoi):
            for ky_tu in chuoi:
                self._bus.write_byte_data(self._addr, 0x40, ord(ky_tu))


from IoT_Driver_USB import LORA_USB
from trung_binh import CuaSoTrungBinh

GATEWAY_HOST = os.environ.get("IOT_GATEWAY_HOST", "192.168.44.211")
CONG_SLAVE2 = 5005
CONG_GATEWAY = 5006
LORA_COM = os.environ.get("IOT_LORA_COM", "/dev/ttyUSB0")
NODE = 3
REG_DEN = {"light": 9, "alarm": 8}  # giong buoi 10: reg 9 = Light, reg 8 = Alarm Light

thiet_bi = {"led3": LED(18), "buzzer": Buzzer(24), "relay": OutputDevice(26)}
adc = ADC(0x08)
khoa = threading.Lock()
node = {"light": None, "alarm": None, "lora_ok": False}  # lan doc LoRa gan nhat
muon_node = {"light": None, "alarm": None}  # lenh master muon cho node 3
co_lenh_moi = threading.Event()  # danh thuc vong_lora ngay khi Light/Alarm doi

try:
    lcd = JHD1802()
except OSError as loi:  # chua cam LCD -> van chay, chi khong hien thi
    print("Khong thay LCD:", loi)
    lcd = None


def doc_anh_sang():
    try:
        return adc.read(0)  # 0-999 (phan nghin cua 3.3 V), cang sang cang lon
    except Exception as loi:
        print("Loi doc anh sang:", loi)
        return None


def hien_lcd(trang_thai, anh_sang):
    if lcd is None:
        return
    dong1 = f"L3:{trang_thai['led3']} BZ:{trang_thai['buzzer']} RL:{trang_thai['relay']}"
    dong2 = f"Anh sang:{'--' if anh_sang is None else anh_sang}"
    try:
        lcd.setCursor(0, 0)
        lcd.write(dong1.ljust(16)[:16])
        lcd.setCursor(1, 0)
        lcd.write(dong2.ljust(16)[:16])
    except OSError as loi:
        print("Loi LCD:", loi)


def vong_nhan_lenh():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", CONG_SLAVE2))
    while True:
        goi, _ = sock.recvfrom(1024)
        try:
            lenh = json.loads(goi)
            for ten, tb in thiet_bi.items():
                if ten in lenh:
                    tb.on() if lenh[ten] else tb.off()
            with khoa:
                for ten in REG_DEN:
                    if ten in lenh and muon_node[ten] != int(lenh[ten]):
                        muon_node[ten] = int(lenh[ten])
                        co_lenh_moi.set()
        except Exception as loi:
            print("Lenh UDP hong:", loi, goi)


def vong_lora():
    try:
        lora = LORA_USB(COM=LORA_COM, address=0)
    except Exception as loi:
        print("Khong mo duoc USB LoRa:", loi)
        return
    # Node 3 NHAN lenh ghi nhung khong tra loi lenh doc (do: 0 byte voi reg 4-9)
    # -> khong doc lai duoc den that. Bao gia tri vua ghi, va GHI LAI moi ~2 giay
    # de bu goi LoRa bi mat / node khoi dong lai. lora_ok = cong serial dang ghi
    # duoc (khong co xac nhan tu node).
    while True:
        with khoa:
            muon = dict(muon_node)
        try:
            for ten, reg in REG_DEN.items():
                if muon[ten] is not None:
                    lora.write_data(NODE, reg, muon[ten])
                    time.sleep(0.3)
            ok = True
        except Exception as loi:
            print("Loi ghi LoRa:", loi)
            ok = False
        with khoa:
            node["lora_ok"] = ok and any(v is not None for v in muon.values())
            node.update({ten: muon[ten] for ten in REG_DEN})
        co_lenh_moi.wait(1.4)
        co_lenh_moi.clear()


def main():
    threading.Thread(target=vong_nhan_lenh, daemon=True).start()
    threading.Thread(target=vong_lora, daemon=True).start()
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def gui(goi):
        try:
            udp.sendto(json.dumps(goi).encode(), (GATEWAY_HOST, CONG_GATEWAY))
        except OSError as loi:
            print("Khong gui duoc toi gateway:", loi)

    if lcd:
        lcd.clear()
    print(f"Slave 2 -> gateway {GATEWAY_HOST}:{CONG_GATEWAY} | nghe lenh UDP :{CONG_SLAVE2} | LoRa {LORA_COM}")
    cua_so = CuaSoTrungBinh()
    nhip = time.monotonic()
    try:
        while True:
            anh_sang = doc_anh_sang()
            trang_thai = {ten: int(bool(tb.value)) for ten, tb in thiet_bi.items()}
            with khoa:
                trang_thai.update(node)
            gui({"loai": "trang_thai", **trang_thai})
            trung_binh = cua_so.them({"anh_sang": anh_sang})
            if trung_binh:
                gui({"loai": "trung_binh", **trung_binh})
                print("[GUI TRUNG BINH 20s]", trung_binh)
            hien_lcd(trang_thai, anh_sang)
            print(f"anh sang {anh_sang} | {trang_thai}")

            nhip += 1
            con_lai = nhip - time.monotonic()
            if con_lai > 0:
                time.sleep(con_lai)
            else:
                nhip = time.monotonic()
    except KeyboardInterrupt:
        print("\nDa dung slave 2.")
    finally:
        for tb in thiet_bi.values():
            tb.off()
        if lcd:
            try:
                lcd.clear()
            except OSError:
                pass


if __name__ == "__main__":
    main()
