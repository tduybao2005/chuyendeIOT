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
    import smbus2

    class JHD1802:
        def __init__(self, address=0x3E):
            self._bus = smbus2.SMBus(1)
            self._addr = address
            self._bus.write_byte(address, 0)
            self._lenh(0x02)
            time.sleep(0.1)
            self._lenh(0x08 | 0x04)
            self._lenh(0x28)

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
REG_DEN = {"light": 9, "alarm": 8}

thiet_bi = {"led3": LED(18), "buzzer": Buzzer(24), "relay": OutputDevice(26)}
adc = ADC(0x08)
khoa = threading.Lock()
node = {"light": None, "alarm": None, "lora_ok": False}
muon_node = {"light": None, "alarm": None}
co_lenh_moi = threading.Event()

try:
    lcd = JHD1802()
except OSError as loi:
    print("Khong thay LCD:", loi)
    lcd = None


def doc_anh_sang():
    try:
        return adc.read(0)
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
