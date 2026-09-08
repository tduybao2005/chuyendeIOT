"""
Buoi 5 - Chuong trinh Raspberry Pi (lop thay Kien)
Muc do 3 - dung 2 CHANNEL ThingSpeak: 1 cho cam bien, 1 cho lenh dieu khien.

VI SAO PHAI TACH 2 CHANNEL (do that tren phan cung):
    ThingSpeak gioi han toi thieu ~17 GIAY giua 2 lan ghi len CUNG 1 channel
    (tai lieu ghi 15s nhung do thuc te chat hon), va de bai bat buoc Pi gui
    trung binh cam bien moi 20 GIAY. Neu de chung 1 channel thi moi chu ky
    21s chi con ~4s trong cho lenh nut bam -> lenh HTTP tu Web bi tu choi
    lien tuc (da gap: 20 lan thu lien tiep deu that bai). Tach ra 2 channel
    thi lenh nut bam khong con tranh khe ghi voi du lieu cam bien nua ->
    bam nut la an ngay (<2s).

Chuc nang:
- Doc nhiet do, do am (DHT), dien ap tren bien tro (ADC), khoang cach (sieu am)
  moi 1 giay; tinh trung binh moi 20 giay va gui len CHANNEL CAM BIEN qua
  HTTP (field1..field4), lien tuc toi thieu 30 phut.
- Hien thi gia tri trung binh + thoi gian + trang thai len LCD 16x2.
- Nhan lenh dieu khien tu Web tren CHANNEL LENH (field5..field8), theo
  dung bang phan chia giao thuc nhom da chon cho 8 nut nhan (2 Auto/Manual +
  6 On/Off cua LED/Buzzer/Relay):
    Auto        -> MQTT   (field4 = 0)
    Manual      -> MQTT   (field4 = 1)
    LED Bat     -> MQTT   (field1 = 1)
    LED Tat     -> HTTP   (field1 = 0)
    Buzzer Bat  -> MQTT   (field2 = 1)
    Buzzer Tat  -> HTTP   (field2 = 0)
    Relay Bat   -> HTTP   (field3 = 1)
    Relay Tat   -> HTTP   (field3 = 0)
  Ca 8 nut nay do WEB (Node-RED) ghi len CHANNEL LENH - giao thuc MQTT/HTTP
  chi anh huong ben phia Web, khong bat buoc Pi phai doc bang cung giao thuc.

- Pi CHI DOC LENH QUA HTTP POLLING MOI GIAY, KHONG SUBSCRIBE MQTT.
  Ly do (phat hien khi test that voi phan cung): ThingSpeak yeu cau client_id
  MQTT phai trung voi username, va nhom chi duoc cap 1 danh tinh MQTT duy
  nhat -> neu CA Web (Node-RED publish) VA Pi (subscribe) cung giu ket noi
  MQTT voi CHUNG 1 client_id, ThingSpeak se lien tuc ngat ket noi ben cu moi
  khi ben kia (tu dong) ket noi lai, tao thanh vong lap "da nhau" ngat/ket
  noi lai moi vai giay MOT CACH LIEN TUC (khong can ai bam nut) - khien hau
  het lenh publish MQTT tu Web bi mat, kha nang cao hon nhieu so voi hinh
  dung ban dau la "chi mat luc dang publish". Giai phap: Pi bo han duong
  subscribe MQTT, CHI GIU 1 duong doc DUY NHAT la HTTP polling moi giay -
  van nhan du CA 8 nut (ke ca 4 nut Web ghi bang MQTT) vi ThingSpeak luu
  chung moi lan ghi (du giao thuc nao) vao CUNG 1 feed cua channel LENH,
  doc lai bang HTTP deu thay day du. Nho vay Node-RED (Web) la ben DUY NHAT giu ket
  noi MQTT, khong con ai tranh client_id nua -> on dinh hon han.
  Poll moi 1 giay van dam bao dung yeu cau de "trang thai LED doi cham nhat
  2s ke tu khi du lieu gui thanh cong len ThingSpeak", vi day la thoi gian
  tinh TU LUC DU LIEU DA CO TREN THINGSPEAK, khong tinh tu luc nguoi dung
  bam nut.

- Che do Auto:
    + LED: sang tu 18h-22h, tat ngoai khoang do.
    + Buzzer: keu khi nhiet do > 37C, tat khi nhiet do < 31C, con lai giu nguyen.
    + Relay: dong khi do am > 90%, tat khi do am < 60%, con lai giu nguyen.
- Che do Manual: LED/Buzzer/Relay bat/tat theo dung lenh moi nhat nhan duoc.

GPIO / cong Grove da lap:
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
import threading
import smbus2
import requests

# ---------------------------------------------------------------------------
# Cau hinh chung
# ---------------------------------------------------------------------------
SAMPLE_INTERVAL = 1        # doc cam bien moi 1s
CONTROL_POLL_INTERVAL = 1  # doc lenh dieu khien moi 1s (chay o LUONG RIENG)
SEND_INTERVAL = 20         # gui trung binh len ThingSpeak moi 20s
MIN_RUN_SECONDS = 30 * 60  # chay lien tuc toi thieu 30 phut (chi de ghi chu/log)

TEMP_RANGE = (0, 100)
HUMI_RANGE = (20, 95)
VOLTAGE_RANGE = (0, 3.3)
DISTANCE_RANGE = (2, 350)   # cm, theo thong so pho bien cua Grove Ultrasonic Ranger

# ---------------------------------------------------------------------------
# Thong tin ThingSpeak (khoa that cua Nhom 7 - lop thay Kien, de nop bai chay
# duoc ngay khong can chinh sua):
#
# Pi CHI CAN thong tin HTTP cua 2 channel (khong can thong tin MQTT vi khong
# con subscribe - xem giai thich o dau file):
#   - Channel CAM BIEN: chi can WRITE key (Pi ghi field1-4 moi 20s).
#   - Channel LENH:     chi can READ key  (Pi doc field5-8 moi 1s).
# ---------------------------------------------------------------------------
# --- Channel CAM BIEN: chi chua du lieu cam bien, Pi ghi moi 20s ---
SENSOR_CHANNEL_ID = "3484407"
SENSOR_WRITE_API_KEY = "N73SVAS2MEDLUESL"

# --- Channel LENH: chi chua 8 nut dieu khien, Web ghi (MQTT + HTTP) ---
COMMAND_CHANNEL_ID = "3484393"
COMMAND_READ_API_KEY = "95WYH34HA3U7KLMO"

THINGSPEAK_UPDATE_URL = "https://api.thingspeak.com/update.json"
COMMAND_FEEDS_URL = f"https://api.thingspeak.com/channels/{COMMAND_CHANNEL_ID}/feeds.json"

# Field tren channel CAM BIEN
FIELD_TEMP = "field1"      # Pi ghi (HTTP, trung binh 20s)
FIELD_HUMI = "field2"      # Pi ghi (HTTP, trung binh 20s)
FIELD_DISTANCE = "field3"  # Pi ghi (HTTP, trung binh 20s)
FIELD_VOLTAGE = "field4"   # Pi ghi (HTTP, trung binh 20s)
# Field tren channel LENH (channel rieng, danh so lai tu field1)
FIELD_LED = "field1"       # Web ghi: MQTT khi Bat (1), HTTP khi Tat (0)
FIELD_BUZZER = "field2"    # Web ghi: MQTT khi Bat (1), HTTP khi Tat (0)
FIELD_RELAY = "field3"     # Web ghi HTTP ca Bat lan Tat
FIELD_MODE = "field4"      # Web ghi MQTT: 0 = Auto, 1 = Manual
CONTROL_POLL_RESULTS = 30  # so ban ghi gan nhat lay ve moi lan doc lenh dieu khien
                           # (~10 phut vi Pi ghi cam bien moi 20s) - du de bat
                           # moi thay doi; con trang thai BAN DAU luc khoi dong
                           # thi doc rieng bang sync_initial_state() ben duoi.


def log_event(message):
    """In ra terminal kem moc thoi gian CO MILI GIAY (HH:MM:SS.mmm).

    Dung de doi chieu voi moc thoi gian Node-RED da ghi lai luc gui lenh
    thanh cong len ThingSpeak (xem console.log trong dashboard_template.html
    va cac ham chuan bi lenh trong flows.json) - tu do tinh ra do tre thuc
    te tu luc bam nut tren Web den luc Pi nhan & ap dung xong.
    """
    now_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{now_str}] {message}")


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

# Trang thai dieu khien hien tai (mac dinh Auto de an toan neu chua nhan
# duoc lenh nao tu Web)
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
        if temp > 37:
            buzzer.on()
        elif temp < 31:
            buzzer.off()
        # con lai: giu nguyen trang thai

    humi = state['humi']
    if humi is not None:
        if humi > 90:
            relay.on()
        elif humi < 60:
            relay.off()
        # con lai: giu nguyen trang thai


def to_bool(value):
    try:
        return float(value) >= 1
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# HTTP polling: doc lai TOAN BO lenh dieu khien (field5-8) tren cung channel.
# Day la DUONG DOC DUY NHAT (khong con subscribe MQTT - xem giai thich o
# dau file) cho ca 8 nut, vi ThingSpeak luu chung vao 1 feed du ghi bang
# giao thuc nao.
# ---------------------------------------------------------------------------
def poll_http_commands():
    params = {"api_key": COMMAND_READ_API_KEY, "results": CONTROL_POLL_RESULTS}
    try:
        response = requests.get(COMMAND_FEEDS_URL, params=params, timeout=5)
        response.raise_for_status()
        feeds = response.json().get("feeds") or []
    except (requests.RequestException, ValueError) as e:
        print("[HTTP] Doc lenh dieu khien that bai:", e)
        return

    # Moi lan Web ghi rieng le 1 field se tao 1 DONG MOI, cac field con lai
    # cua dong do la null. Vi vay phai quet nguoc tu ban ghi moi nhat ve cu
    # va lay gia tri KHONG null dau tien cho TUNG field rieng biet.
    changed = False
    changed_fields = []  # de in log doi chieu thoi gian voi Node-RED (xem log_event())
    found = {'mode': False, 'led': False, 'buzzer': False, 'relay': False}
    for feed in reversed(feeds):
        if not found['mode'] and feed.get(FIELD_MODE) not in (None, ""):
            new_mode = 'manual' if to_bool(feed.get(FIELD_MODE)) else 'auto'
            if new_mode != state['mode']:
                state['mode'] = new_mode
                changed = True
                changed_fields.append(f"Mode->{new_mode}")
            found['mode'] = True
        if not found['led'] and feed.get(FIELD_LED) not in (None, ""):
            new_val = to_bool(feed.get(FIELD_LED))
            if new_val != state['led_cmd']:
                state['led_cmd'] = new_val
                changed = True
                changed_fields.append(f"LED->{'ON' if new_val else 'OFF'}")
            found['led'] = True
        if not found['buzzer'] and feed.get(FIELD_BUZZER) not in (None, ""):
            new_val = to_bool(feed.get(FIELD_BUZZER))
            if new_val != state['buzzer_cmd']:
                state['buzzer_cmd'] = new_val
                changed = True
                changed_fields.append(f"Buzzer->{'ON' if new_val else 'OFF'}")
            found['buzzer'] = True
        if not found['relay'] and feed.get(FIELD_RELAY) not in (None, ""):
            new_val = to_bool(feed.get(FIELD_RELAY))
            if new_val != state['relay_cmd']:
                state['relay_cmd'] = new_val
                changed = True
                changed_fields.append(f"Relay->{'ON' if new_val else 'OFF'}")
            found['relay'] = True
        if all(found.values()):
            break
    if changed:
        # Moc thoi gian co mili giay - de doi chieu voi moc "gui thanh cong
        # len ThingSpeak" ma Node-RED da in ra, tinh ra do tre thuc te tu
        # Web bam nut den khi Pi nhan & ap dung xong.
        log_event(f"NHAN LENH: {', '.join(changed_fields)} "
                  f"(mode={state['mode']} led={state['led_cmd']} "
                  f"buzzer={state['buzzer_cmd']} relay={state['relay_cmd']})")
        apply_outputs()
        log_event(f"DA AP DUNG XONG: {', '.join(changed_fields)}")


def sync_initial_state():
    """Doc trang thai lenh HIEN TAI luc moi khoi dong.

    Khong the dua vao poll_http_commands() cho viec nay: no chi quet
    CONTROL_POLL_RESULTS ban ghi gan nhat, ma Pi ghi cam bien moi 20s nen
    mot lenh cu (vd chon che do Manual tu 30 phut truoc) da troi ra ngoai
    cua so do -> Pi se hieu nham la "chua co lenh nao" va quay ve mac dinh
    Auto, khien cac nut Bat/Tat khong con tac dung (loi da gap khi test).
    ThingSpeak co san API tra ve gia tri cuoi cung cua TUNG field bat ke
    cu bao lau: /channels/<id>/fields/<n>/last.json
    """
    targets = [
        (FIELD_MODE, 'mode'), (FIELD_LED, 'led_cmd'),
        (FIELD_BUZZER, 'buzzer_cmd'), (FIELD_RELAY, 'relay_cmd'),
    ]
    for field, key in targets:
        num = field.replace('field', '')
        url = f"https://api.thingspeak.com/channels/{COMMAND_CHANNEL_ID}/fields/{num}/last.json"
        try:
            response = requests.get(url, params={"api_key": COMMAND_READ_API_KEY}, timeout=5)
            response.raise_for_status()
            # API nay tra ve THANG GIA TRI (vd "1", "0") chu khong phai
            # object {"fieldN": ...} - va tra ve -1 neu field chua bao gio
            # co du lieu (quy uoc cua ThingSpeak).
            value = response.json()
        except (requests.RequestException, ValueError) as e:
            print(f"[HTTP] Khong doc duoc gia tri cuoi cua {field}:", e)
            continue
        if value in (None, "", -1, "-1"):
            continue
        if key == 'mode':
            state['mode'] = 'manual' if to_bool(value) else 'auto'
        else:
            state[key] = to_bool(value)
    print(f"[HTTP] Trang thai ban dau doc tu ThingSpeak: mode={state['mode']} "
          f"led={state['led_cmd']} buzzer={state['buzzer_cmd']} relay={state['relay_cmd']}")
    apply_outputs()


def control_poll_loop(stop_event):
    """Doc lenh dieu khien o LUONG RIENG, dung nhip 1 giay.

    LY DO tach luong: neu de chung trong vong lap chinh, moi vong con phai
    doc DHT (~1s, ham chan), cam bien sieu am, ghi LCD... nen chu ky thuc te
    do duoc len toi ~2.2s -> lenh co the nam cho toi 2.2s moi duoc xu ly,
    VUOT moc "cham nhat 2s" cua de bai. Tach ra luong rieng thi viec doc
    lenh luon dung nhip 1s, khong bi cam bien cham lam nghen.
    """
    while not stop_event.is_set():
        try:
            poll_http_commands()
        except Exception as e:
            print("[HTTP] Loi trong luong doc lenh:", e)
        stop_event.wait(CONTROL_POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Gui du lieu trung binh len ThingSpeak (HTTP)
# ---------------------------------------------------------------------------
def send_to_thingspeak(**fields):
    """Gui 1 ban ghi len ThingSpeak, co tu dong thu lai.

    LUU Y: ThingSpeak gioi han toi thieu 15 giay giua 2 lan ghi len CUNG 1
    channel, bat ke ghi bang HTTP hay MQTT (cac nut dieu khien tu Web cung
    ghi len channel nay) - khi bi tu choi, ThingSpeak tra ve HTTP 200 kem
    noi dung "0" (khong phai loi HTTP) nen phai kiem tra noi dung tra ve,
    khong the chi dua vao raise_for_status().
    """
    payload = {"api_key": SENSOR_WRITE_API_KEY}
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
        fields[FIELD_TEMP] = round(averages['temp'], 1)
    if 'humi' in averages:
        fields[FIELD_HUMI] = round(averages['humi'], 1)
    if 'voltage' in averages:
        fields[FIELD_VOLTAGE] = round(averages['voltage'], 2)
    if 'distance' in averages:
        fields[FIELD_DISTANCE] = round(averages['distance'], 1)
    if send_to_thingspeak(**fields):
        print(f"[HTTP] Da gui trung binh len ThingSpeak: {fields}")


# ---------------------------------------------------------------------------
# Vong lap chinh
# ---------------------------------------------------------------------------
def main():
    lcd.clear() if hasattr(lcd, 'clear') else None

    # Dong bo trang thai lenh hien tai truoc khi vao vong lap, de khoi dong
    # lai giua chung khong bi mat che do Manual / trang thai thiet bi.
    sync_initial_state()

    # Doc lenh dieu khien o luong rieng, dung nhip 1s (khong bi cam bien
    # cham lam nghen) -> dam bao "trang thai doi cham nhat 2s".
    stop_event = threading.Event()
    control_thread = threading.Thread(target=control_poll_loop, args=(stop_event,), daemon=True)
    control_thread.start()

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

                # (Viec doc lenh dieu khien field5-8 da duoc tach sang luong
                # rieng control_poll_loop() chay dung nhip 1s - xem ghi chu o
                # ham do; vong lap nay chi lo cam bien / LCD / gui trung binh.)

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
        stop_event.set()
        # An toan: chu dong tat ca 3 thiet bi khi chuong trinh dung (ke ca do
        # loi), vi GPIO khong tu dong ve muc thap khi tien trinh ket thuc -
        # neu dang bat thi se giu nguyen trang thai vat ly cho den khi co
        # lenh tat ro rang.
        led.off()
        buzzer.off()
        relay.off()


if __name__ == '__main__':
    main()
