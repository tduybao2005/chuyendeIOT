from grove.adc import ADC
from seeed_dht import DHT
from grove.display.jhd1802 import JHD1802
from time import sleep
from collections import deque
import time
import requests
import paho.mqtt.client as mqtt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DISPLAY_INTERVAL = 1
WINDOW_SECONDS = 20
FILTER_WINDOW_SIZE = 5

TEMP_RANGE = (0, 100)
HUMI_RANGE = (20, 95)
VOLTAGE_RANGE = (0, 3.3)

THINGSPEAK_URL = "https://api.thingspeak.com/update.json"
THINGSPEAK_API_KEY = "DAN_WRITE_API_KEY_CUA_BAN_VAO_DAY"

MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 1883
THINGSPEAK_CHANNEL_ID = "DIEN_CHANNEL_ID_CUA_BAN"
MQTT_CLIENT_ID = "DIEN_MQTT_CLIENT_ID_CUA_BAN"
MQTT_USERNAME = "DIEN_MQTT_USERNAME_CUA_BAN"
MQTT_PASSWORD = "DIEN_MQTT_PASSWORD_CUA_BAN"


def is_valid(value, min_val, max_val):
    return min_val <= value <= max_val


class MovingAverageFilter:
    def __init__(self, window_size=FILTER_WINDOW_SIZE):
        self._buffer = deque(maxlen=window_size)

    def update(self, value):
        self._buffer.append(value)
        return sum(self._buffer) / len(self._buffer)


lcd = JHD1802()
sensor_temp_humi = DHT('11', 16)
sensor_rotary_angle = ADC(0x08)

temp_filter = MovingAverageFilter()
humi_filter = MovingAverageFilter()
voltage_filter = MovingAverageFilter()

history_temp_raw = []
history_temp_filtered = []
history_humi_raw = []
history_humi_filtered = []
history_voltage_raw = []
history_voltage_filtered = []


def show_temp_humi_value():
    humi_raw, temp_raw = sensor_temp_humi.read()
    humi_raw, temp_raw = int(humi_raw), int(temp_raw)

    temp_valid = is_valid(temp_raw, *TEMP_RANGE)
    humi_valid = is_valid(humi_raw, *HUMI_RANGE)

    temp_filtered = temp_filter.update(temp_raw) if temp_valid else None
    humi_filtered = humi_filter.update(humi_raw) if humi_valid else None

    if temp_valid:
        history_temp_raw.append(temp_raw)
        history_temp_filtered.append(temp_filtered)
        print(f"temp: raw={temp_raw}, filtered={temp_filtered:.1f}")
        temp_str = '{0:4.1f}'.format(temp_filtered)
    else:
        print(f"temp: {temp_raw} (gia tri bi loi/ngoai range)")
        temp_str = '    '

    if humi_valid:
        history_humi_raw.append(humi_raw)
        history_humi_filtered.append(humi_filtered)
        print(f"humi: raw={humi_raw}, filtered={humi_filtered:.1f}")
        humi_str = '{0:4.1f}'.format(humi_filtered)
    else:
        print(f"humi: {humi_raw} (gia tri bi loi/ngoai range)")
        humi_str = '    '

    lcd.setCursor(0, 0)
    lcd.write('T:{0},H:{1}'.format(temp_str, humi_str))

    return temp_filtered, humi_filtered


def show_voltage_value():
    voltage_raw = sensor_rotary_angle.read_voltage(2) / 1000
    valid = is_valid(voltage_raw, *VOLTAGE_RANGE)

    voltage_filtered = voltage_filter.update(voltage_raw) if valid else None

    if valid:
        history_voltage_raw.append(voltage_raw)
        history_voltage_filtered.append(voltage_filtered)
        print(f"voltage: raw={voltage_raw:.2f}, filtered={voltage_filtered:.2f}")
        voltage_str = '{0:4.2f}'.format(voltage_filtered)
    else:
        print(f"voltage: {voltage_raw:.2f} (gia tri bi loi/ngoai range)")
        voltage_str = '    '

    lcd.setCursor(1, 0)
    lcd.write('V:{0}'.format(voltage_str))

    return voltage_filtered


def send_to_thingspeak_http(**fields):
    payload = {"api_key": THINGSPEAK_API_KEY}
    payload.update(fields)
    try:
        response = requests.post(THINGSPEAK_URL, json=payload, timeout=5)
        response.raise_for_status()
        print(f"[HTTP] Gui thanh cong, entry_id={response.text}")
        return True
    except requests.RequestException as e:
        print(f"[HTTP] Gui that bai: {e}")
        return False


def send_to_thingspeak_mqtt(**fields):
    topic = f"channels/{THINGSPEAK_CHANNEL_ID}/publish"
    payload = "&".join(f"{key}={value}" for key, value in fields.items())

    connect_result = {'rc': None}

    def on_connect(client, userdata, flags, reason_code, properties=None):
        connect_result['rc'] = reason_code

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.on_connect = on_connect
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=10)
        client.loop_start()

        for _ in range(50):
            if connect_result['rc'] is not None:
                break
            time.sleep(0.1)

        if connect_result['rc'] != 0:
            client.loop_stop()
            client.disconnect()
            print(f"[MQTT] Ket noi/xac thuc that bai, reason_code={connect_result['rc']}")
            return False

        info = client.publish(topic, payload, qos=1)
        info.wait_for_publish(timeout=5)
        client.loop_stop()
        client.disconnect()
        print(f"[MQTT] Gui thanh cong: {payload}")
        return True
    except Exception as e:
        print(f"[MQTT] Gui that bai: {e}")
        return False


def send_window_average(window):
    averages = {key: (sum(values) / len(values)) for key, values in window.items() if values}

    if not averages:
        return

    fields = {}
    if 'temp' in averages:
        fields['field1'] = round(averages['temp'])
    if 'humi' in averages:
        fields['field2'] = round(averages['humi'])
    if 'voltage' in averages:
        fields['field3'] = round(averages['voltage'], 2)

    send_to_thingspeak_http(**fields)
    send_to_thingspeak_mqtt(**fields)


def plot_noise_comparison():
    if not history_temp_raw:
        print("Chua co du lieu de ve bieu do.")
        return

    plt.figure(figsize=(10, 9))

    plt.subplot(3, 1, 1)
    plt.plot(history_temp_raw, label='Nhiet do - Raw', alpha=0.5, marker='o')
    plt.plot(history_temp_filtered, label='Nhiet do - Da loc (MA)', marker='s')
    plt.ylabel('Nhiet do (C)')
    plt.legend()
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(history_humi_raw, label='Do am - Raw', alpha=0.5, marker='o')
    plt.plot(history_humi_filtered, label='Do am - Da loc (MA)', marker='s')
    plt.ylabel('Do am (%)')
    plt.legend()
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.plot(history_voltage_raw, label='Dien ap - Raw', alpha=0.5, marker='o')
    plt.plot(history_voltage_filtered, label='Dien ap - Da loc (MA)', marker='s')
    plt.xlabel('Lan do')
    plt.ylabel('Dien ap (V)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('noise_comparison.png')
    print("Da luu bieu do so sanh: noise_comparison.png")


def main():
    lcd.clear()

    window_start = time.time()
    window = {'temp': [], 'humi': [], 'voltage': []}

    try:
        while True:
            temp_r, humi_r = show_temp_humi_value()
            voltage_r = show_voltage_value()

            if temp_r is not None:
                window['temp'].append(temp_r)
            if humi_r is not None:
                window['humi'].append(humi_r)
            if voltage_r is not None:
                window['voltage'].append(voltage_r)

            if time.time() - window_start >= WINDOW_SECONDS:
                send_window_average(window)
                window = {k: [] for k in window}
                window_start = time.time()

            print("###############################")
            sleep(DISPLAY_INTERVAL)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
        plot_noise_comparison()


if __name__ == '__main__':
    main()
