"""
Buoi 5 - Chuong trinh Raspberry Pi
Nhom 4

Chuc nang:
- Doc nhiet do, do am (DHT), dien ap tren bien tro (ADC), khoang cach (sieu am)
  moi 1 giay; tinh trung binh moi 20 giay va gui len ThingSpeak qua HTTP.
- Hien thi thoi gian hien tai (va trang thai) len LCD 16x2.
- Nhan lenh dieu khien tu Web qua 2 kenh ThingSpeak khac nhau (dung theo cach
  thiet bi MQTT cua nhom da duoc cap quyen - xem ghi chu o phan cau hinh):
    + Che do Auto/Manual: doc qua MQTT subscribe (topic so 1) tren kenh MQTT
      rieng -> nhan duoc gan nhu tuc thi.
    + Lenh LED/Buzzer/Relay: Web ghi bang HTTP len kenh HTTP, nen Pi doc lai
      bang HTTP polling (GET feeds.json) moi 1 giay -> van dam bao phan hoi
      trong vong <= 2 giay.
- Che do Auto:
    + LED: sang tu 18h-22h, tat ngoai khoang do.
    + Buzzer: keu khi nhiet do > 40C, tat khi nhiet do < 30C, con lai giu nguyen.
    + Relay: dong khi do am > 70%, tat khi do am < 40%, con lai giu nguyen.
- Che do Manual: LED/Buzzer/Relay bat/tat theo dung lenh moi nhat nhan duoc.

GPIO / cong Grove da lap (theo bang da thong nhat voi nhom 4):
    DHT (nhiet do, do am)              -> D5   (GPIO5)
    Cam bien sieu am (khoang cach)      -> D16  (GPIO16)
    Bien tro (dien ap) qua Grove ADC    -> I2C 0x08, kenh 2
    LCD 16x2 (JHD1802, RGB backlight)   -> I2C-1 (0x3E hien thi + 0x62 den nen)
    LED                                 -> D18  (GPIO18)
    Buzzer                              -> D24  (GPIO24)
    Relay                               -> D26  (GPIO26)
"""

from seeed_dht import DHT
from grove.adc import ADC
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger
from gpiozero import LED, Buzzer, OutputDevice
from time import sleep
from datetime import datetime
import json
import smbus2
import requests
import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Cau hinh chung
# ---------------------------------------------------------------------------
SAMPLE_INTERVAL = 1        # doc cam bien + xu ly lenh dieu khien moi 1s
SEND_INTERVAL = 20         # gui trung binh len ThingSpeak moi 20s
MIN_RUN_SECONDS = 45 * 60  # chay lien tuc toi thieu 45 phut (chi de ghi chu/log)

TEMP_RANGE = (0, 100)
HUMI_RANGE = (20, 95)
VOLTAGE_RANGE = (0, 3.3)
DISTANCE_RANGE = (2, 350)   # cm, theo thong so pho bien cua Grove Ultrasonic Ranger

# ---------------------------------------------------------------------------
# Thong tin ThingSpeak - HAY DIEN THONG TIN THAT CUA BAN VAO DAY TRUOC KHI CHAY
#
# LUU Y: du an nay dung 2 CHANNEL RIENG (giong quy uoc da dung o buoi_4) vi
# thiet bi MQTT chi duoc cap quyen subscribe tren 1 channel rieng, khac voi
# channel dung cho HTTP:
#   - THINGSPEAK_CHANNEL_ID  (kenh HTTP) : Pi ghi trung binh cam bien (field1-4)
#     va cung la kenh Web ghi lenh LED/Buzzer/Relay bang HTTP (field5-7) ->
#     Pi doc lai bang HTTP polling (khong the subscribe MQTT tren kenh nay).
#   - MQTT_CHANNEL_ID (kenh MQTT) : channel nay CHI CO 1 field duy nhat ten
#     "Mode" va no la field1 CUA CHINH KENH NAY (khac field1 = nhiet do cua
#     kenh HTTP) -> Pi subscribe MQTT tren kenh nay de nhan tuc thi.
#
# LUU Y QUAN TRONG (phat hien khi test that voi phan cung): vi ThingSpeak
# yeu cau client_id MQTT phai trung voi username, Web va Pi buoc phai dung
# CHUNG 1 danh tinh MQTT -> moi lan Web publish se lam Pi bi ngat ket noi
# tam thoi (client_id bi trung), va broker cua ThingSpeak KHONG luu retained
# message that su tren topic dang channel-feed nay, nen Pi co the bi MAT tin
# nhan mode ngay ca khi da subscribe lai. Vi vay code doc gia tri che do
# theo CA 2 CACH: MQTT (nhanh, nhung co the mat) VA HTTP polling (cham hon 1
# nhip nhung chac chan, dung lam nguon du lieu chinh/du phong).
# ---------------------------------------------------------------------------
THINGSPEAK_CHANNEL_ID = "DIEN_CHANNEL_ID_HTTP_CUA_BAN"
THINGSPEAK_READ_API_KEY = "DIEN_READ_API_KEY_CUA_BAN"
THINGSPEAK_WRITE_API_KEY = "DIEN_WRITE_API_KEY_CUA_BAN"
THINGSPEAK_UPDATE_URL = "https://api.thingspeak.com/update.json"
THINGSPEAK_FEEDS_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"

MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 1883
MQTT_CHANNEL_ID = "DIEN_CHANNEL_ID_MQTT_CUA_BAN"
MQTT_CHANNEL_READ_API_KEY = "DIEN_READ_API_KEY_CUA_KENH_MQTT_CUA_BAN"
MQTT_CHANNEL_FEEDS_URL = f"https://api.thingspeak.com/channels/{MQTT_CHANNEL_ID}/feeds.json"
MQTT_CLIENT_ID = "DIEN_MQTT_CLIENT_ID_CUA_BAN"
MQTT_USERNAME = "DIEN_MQTT_USERNAME_CUA_BAN"
MQTT_PASSWORD = "DIEN_MQTT_PASSWORD_CUA_BAN"
# Topic so 1: subscribe toan bo channel feed (tat ca field cung luc) tren
# kenh MQTT rieng - chi mang gia tri che do Auto/Manual (field5).
MQTT_SUBSCRIBE_TOPIC = f"channels/{MQTT_CHANNEL_ID}/subscribe"

# Kenh HTTP: field1..field4 Pi ghi (trung binh 20s), field5..field7 Web ghi
# (lenh dieu khien, Pi doc lai bang polling). Kenh MQTT: field1 = che do.
FIELD_MODE = "field1"     # 0 = Auto, 1 = Manual (field "Mode" tren KENH MQTT rieng - khac field1 cua kenh HTTP)
FIELD_LED = "field5"      # kenh HTTP (dat ten "LED" tren channel)
FIELD_BUZZER = "field6"   # kenh HTTP (dat ten "Buzzer" tren channel)
FIELD_RELAY = "field7"    # kenh HTTP (dat ten "Relay" tren channel)
CONTROL_POLL_RESULTS = 15  # so ban ghi gan nhat lay ve moi lan doc lenh dieu khien


def is_valid(value, min_val, max_val):
    return value is not None and min_val <= value <= max_val


# ---------------------------------------------------------------------------
# Cam bien
# ---------------------------------------------------------------------------
sensor_temp_humi = DHT('11', 5)
sensor_bien_tro = ADC(0x08)
sensor_khoang_cach = GroveUltrasonicRanger(16)


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


def read_voltage():
    try:
        voltage_raw = sensor_bien_tro.read_voltage(2) / 1000
    except Exception as e:
        print("Loi doc ADC (bien tro):", e)
        return None
    return voltage_raw if is_valid(voltage_raw, *VOLTAGE_RANGE) else None


def read_distance():
    try:
        distance_raw = sensor_khoang_cach.get_distance()
    except Exception as e:
        print("Loi doc cam bien sieu am:", e)
        return None
    return distance_raw if is_valid(distance_raw, *DISTANCE_RANGE) else None


# ---------------------------------------------------------------------------
# LCD 16x2 (JHD1802 - man hinh 0x3E, den nen RGB 0x62)
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


lcd = JHD1802()


def show_lcd(mode, led_on, buzzer_on, relay_on):
    now_str = datetime.now().strftime('%H:%M:%S')
    mode_str = 'MANU' if mode == 'manual' else 'AUTO'
    lcd.setCursor(0, 0)
    lcd.write('Time {0}    '.format(now_str))
    lcd.setCursor(1, 0)
    lcd.write('{0} L{1} B{2} R{3}   '.format(
        mode_str, int(led_on), int(buzzer_on), int(relay_on)))


# ---------------------------------------------------------------------------
# Thiet bi dieu khien
# ---------------------------------------------------------------------------
led = LED(18)
buzzer = Buzzer(24)
relay = OutputDevice(26)

# Trang thai dieu khien hien tai (cap nhat tu MQTT, mac dinh Auto de an toan
# neu chua nhan duoc lenh nao tu Web)
state = {
    'mode': 'auto',        # 'auto' hoac 'manual'
    'led_cmd': False,
    'buzzer_cmd': False,
    'relay_cmd': False,
    'temp': None,          # gia tri tuc thoi moi nhat (dung cho logic Auto)
    'humi': None,
}


def apply_outputs():
    """Ap dung trang thai LED/Buzzer/Relay theo che do hien tai."""
    if state['mode'] == 'manual':
        led.on() if state['led_cmd'] else led.off()
        buzzer.on() if state['buzzer_cmd'] else buzzer.off()
        relay.on() if state['relay_cmd'] else relay.off()
        return

    # Che do Auto
    hour = datetime.now().hour
    if 18 <= hour < 22:
        led.on()
    else:
        led.off()

    temp = state['temp']
    if temp is not None:
        if temp > 40:
            buzzer.on()
        elif temp < 30:
            buzzer.off()
        # con lai: giu nguyen trang thai

    humi = state['humi']
    if humi is not None:
        if humi > 70:
            relay.on()
        elif humi < 40:
            relay.off()
        # con lai: giu nguyen trang thai


# ---------------------------------------------------------------------------
# MQTT: nhan lenh dieu khien (topic so 1 - subscribe toan bo channel feed)
# ---------------------------------------------------------------------------
def to_bool(value):
    try:
        return float(value) >= 1
    except (TypeError, ValueError):
        return False


def on_mqtt_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[MQTT] Ket noi thanh cong, dang subscribe (topic so 1): {MQTT_SUBSCRIBE_TOPIC}")
        client.subscribe(MQTT_SUBSCRIBE_TOPIC)
    else:
        print(f"[MQTT] Ket noi/xac thuc that bai, reason_code={reason_code}")


def on_mqtt_message(client, userdata, message):
    """Kenh MQTT rieng chi mang gia tri che do Auto/Manual (field5)."""
    try:
        data = json.loads(message.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print("[MQTT] Payload khong hop le:", e)
        return

    if data.get(FIELD_MODE) is not None:
        state['mode'] = 'manual' if to_bool(data.get(FIELD_MODE)) else 'auto'
        print(f"[MQTT] Cap nhat che do: mode={state['mode']}")
        apply_outputs()  # phan hoi ngay, khong doi den vong lap ke tiep


def start_mqtt_subscriber():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)
    client.loop_start()
    return client


# ---------------------------------------------------------------------------
# HTTP polling: doc lenh LED/Buzzer/Relay (kenh HTTP, vi khong subscribe MQTT
# duoc tren kenh nay) - goi moi giay de dam bao phan hoi <= 2 giay.
# ---------------------------------------------------------------------------
def poll_http_commands():
    params = {"api_key": THINGSPEAK_READ_API_KEY, "results": CONTROL_POLL_RESULTS}
    try:
        response = requests.get(THINGSPEAK_FEEDS_URL, params=params, timeout=5)
        response.raise_for_status()
        feeds = response.json().get("feeds") or []
    except (requests.RequestException, ValueError) as e:
        print("[HTTP] Doc lenh dieu khien that bai:", e)
        return

    # Moi lan Web ghi rieng le 1 field se tao 1 DONG MOI, cac field con lai
    # cua dong do la null. Vi vay phai quet nguoc tu ban ghi moi nhat ve cu
    # va lay gia tri KHONG null dau tien cho TUNG field rieng biet.
    changed = False
    found = {'led': False, 'buzzer': False, 'relay': False}
    for feed in reversed(feeds):
        if not found['led'] and feed.get(FIELD_LED) not in (None, ""):
            new_val = to_bool(feed.get(FIELD_LED))
            if new_val != state['led_cmd']:
                state['led_cmd'] = new_val
                changed = True
            found['led'] = True
        if not found['buzzer'] and feed.get(FIELD_BUZZER) not in (None, ""):
            new_val = to_bool(feed.get(FIELD_BUZZER))
            if new_val != state['buzzer_cmd']:
                state['buzzer_cmd'] = new_val
                changed = True
            found['buzzer'] = True
        if not found['relay'] and feed.get(FIELD_RELAY) not in (None, ""):
            new_val = to_bool(feed.get(FIELD_RELAY))
            if new_val != state['relay_cmd']:
                state['relay_cmd'] = new_val
                changed = True
            found['relay'] = True
        if all(found.values()):
            break
    if changed:
        print(f"[HTTP] Cap nhat lenh dieu khien: led={state['led_cmd']} "
              f"buzzer={state['buzzer_cmd']} relay={state['relay_cmd']}")
        apply_outputs()


def poll_http_mode():
    """Doc du phong gia tri che do (field5) qua HTTP tren kenh MQTT.

    MQTT subscribe (on_mqtt_message) van la duong nhanh cho che do, nhung vi
    Web va Pi phai dung chung 1 client_id MQTT (ThingSpeak yeu cau client_id
    trung username) nen moi lan Web publish co the lam Pi bi ngat ket noi
    tam thoi - va ThingSpeak khong luu retained message that su tren topic
    nay nen Pi co the mat han tin nhan do. Ham nay dam bao che do luon duoc
    cap nhat dung du MQTT co bi mat goi tin hay khong.
    """
    params = {"api_key": MQTT_CHANNEL_READ_API_KEY, "results": CONTROL_POLL_RESULTS}
    try:
        response = requests.get(MQTT_CHANNEL_FEEDS_URL, params=params, timeout=5)
        response.raise_for_status()
        feeds = response.json().get("feeds") or []
    except (requests.RequestException, ValueError) as e:
        print("[HTTP] Doc che do du phong that bai:", e)
        return

    for feed in reversed(feeds):
        if feed.get(FIELD_MODE) not in (None, ""):
            new_mode = 'manual' if to_bool(feed.get(FIELD_MODE)) else 'auto'
            if new_mode != state['mode']:
                state['mode'] = new_mode
                print(f"[HTTP] Cap nhat che do (du phong): mode={state['mode']}")
                apply_outputs()
            break


# ---------------------------------------------------------------------------
# Gui du lieu trung binh len ThingSpeak (HTTP)
# ---------------------------------------------------------------------------
def send_to_thingspeak(**fields):
    """Gui 1 ban ghi len ThingSpeak, co tu dong thu lai.

    LUU Y: ThingSpeak gioi han toi thieu 15 giay giua 2 lan ghi len CUNG 1
    channel, bat ke ghi tu Pi hay tu Web (nut LED/Buzzer/Relay cung ghi len
    channel nay qua HTTP) - khi bi tu choi, ThingSpeak tra ve HTTP 200 kem
    noi dung "0" (khong phai ma loi HTTP) nen phai kiem tra noi dung tra ve,
    khong the chi dua vao raise_for_status().
    """
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
        if isinstance(result, dict) and result.get('entry_id'):
            return True
        if attempt < 2:
            sleep(3)  # co the dang trung nhip gioi han 15s, doi roi thu lai
    print("[HTTP] Gui du lieu that bai sau nhieu lan thu (co the do gioi han 15s/lan ghi cua ThingSpeak)")
    return False


def send_window_average(window):
    averages = {key: (sum(values) / len(values))
                for key, values in window.items() if values}
    if not averages:
        print("[HTTP] Khong co du lieu hop le trong 20s vua qua, bo qua goi tin nay.")
        return
    fields = {}
    if 'temp' in averages:
        fields['field1'] = round(averages['temp'], 1)
    if 'humi' in averages:
        fields['field2'] = round(averages['humi'], 1)
    if 'voltage' in averages:
        fields['field3'] = round(averages['voltage'], 2)
    if 'distance' in averages:
        fields['field4'] = round(averages['distance'], 1)
    if send_to_thingspeak(**fields):
        print(f"[HTTP] Da gui trung binh len ThingSpeak: {fields}")


# ---------------------------------------------------------------------------
# Vong lap chinh
# ---------------------------------------------------------------------------
def main():
    lcd.clear() if hasattr(lcd, 'clear') else None
    mqtt_client = start_mqtt_subscriber()

    window_start = None
    window = {'temp': [], 'humi': [], 'voltage': [], 'distance': []}
    run_start = datetime.now()

    try:
        while True:
            try:
                temp, humi = read_temp_humi()
                voltage = read_voltage()
                distance = read_distance()

                if temp is not None:
                    state['temp'] = temp
                    window['temp'].append(temp)
                if humi is not None:
                    state['humi'] = humi
                    window['humi'].append(humi)
                if voltage is not None:
                    window['voltage'].append(voltage)
                if distance is not None:
                    window['distance'].append(distance)

                print(f"Nhiet do:{temp} Do am:{humi} Dien ap:{voltage} Khoang cach:{distance}")

                # Doc lenh LED/Buzzer/Relay tu kenh HTTP moi giay (khong the
                # subscribe MQTT tren kenh nay - xem ghi chu o phan cau hinh)
                poll_http_commands()
                # Doc du phong che do (field5) qua HTTP, phong khi MQTT bi mat
                # goi tin do tranh chap client_id voi Web (xem ghi chu tren)
                poll_http_mode()

                # Auto mode can duoc danh gia lai moi giay (vi dieu kien theo
                # gio he thong / nhiet do / do am co the thay doi lien tuc)
                apply_outputs()
                show_lcd(state['mode'], led.is_lit, buzzer.is_active, relay.is_active)

                if window_start is None:
                    window_start = datetime.now()
                elapsed = (datetime.now() - window_start).total_seconds()
                if elapsed >= SEND_INTERVAL:
                    send_window_average(window)
                    window = {k: [] for k in window}
                    window_start = datetime.now()

            except Exception as e:
                # Bat loi o muc vong lap de chuong trinh khong bao gio dung han
                # (cam bien loi, mat mang, ...) - doc lai va gui du lieu khac.
                print("Loi trong vong lap chinh:", e)

            sleep(SAMPLE_INTERVAL)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
    finally:
        # An toan: chu dong tat ca 3 thiet bi khi chuong trinh dung (ke ca do
        # loi), vi GPIO khong tu dong ve muc thap khi tien trinh ket thuc -
        # neu dang bat thi se giu nguyen trang thai vat ly cho den khi co
        # lenh tat ro rang.
        led.off()
        buzzer.off()
        relay.off()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == '__main__':
    main()
