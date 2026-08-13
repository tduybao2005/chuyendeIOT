from grove.adc import ADC
from seeed_dht import DHT
from grove.display.jhd1802 import JHD1802
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger
from time import sleep
from collections import deque
from datetime import datetime
import time
import csv
import os
import json
import requests
import paho.mqtt.client as mqtt

DISPLAY_INTERVAL = 2
WINDOW_SECONDS = 20
LOG_FILE = 'sensor_log.csv'

TEMP_RANGE = (0, 50)
HUMI_RANGE = (20, 95)
LIGHT_RANGE = (0, 1000)
DISTANCE_RANGE = (2, 400)
VOLTAGE_RANGE = (0, 3300)

THINGSPEAK_URL = "https://api.thingspeak.com/update.json"
THINGSPEAK_API_KEY = "DAN_WRITE_API_KEY_CUA_BAN_VAO_DAY"

MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 1883
THINGSPEAK_CHANNEL_ID = "DIEN_CHANNEL_ID_CUA_BAN"
MQTT_CLIENT_ID = "DIEN_MQTT_CLIENT_ID_CUA_BAN"
MQTT_USERNAME = "DIEN_MQTT_USERNAME_CUA_BAN"
MQTT_PASSWORD = "DIEN_MQTT_PASSWORD_CUA_BAN"


class GroveLightSensor:
    def __init__(self, channel):
        self.channel = channel
        self.adc = ADC(address=0x08)

    @property
    def Light(self):
        value = self.adc.read(self.channel)
        return value


class MovingAverageFilter:
    def __init__(self, window_size=5):
        self._buffer = deque(maxlen=window_size)

    def update(self, value):
        self._buffer.append(value)
        return sum(self._buffer) / len(self._buffer)


def is_valid(value, min_val, max_val):
    return min_val <= value <= max_val


LOG_FIELDS = ['timestamp', 'event', 'temp', 'humi', 'light', 'distance', 'voltage', 'note']


def log_event(event, temp='', humi='', light='', distance='', voltage='', note=''):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'event': event,
            'temp': temp, 'humi': humi, 'light': light,
            'distance': distance, 'voltage': voltage,
            'note': note,
        })


lcd = JHD1802()
sensor_temp_humi = DHT('11', 16)
sensor_distance = GroveUltrasonicRanger(5)
sensor_light = GroveLightSensor(0)
sensor_rotary_angle = ADC(0x08)

temp_filter = MovingAverageFilter(window_size=5)
humi_filter = MovingAverageFilter(window_size=5)
light_filter = MovingAverageFilter(window_size=5)
distance_filter = MovingAverageFilter(window_size=5)
voltage_filter = MovingAverageFilter(window_size=5)


def show_temp_humi_value():
    humi_raw, temp_raw = sensor_temp_humi.read()
    humi_raw, temp_raw = float(humi_raw), float(temp_raw)

    temp_filtered = None
    humi_filtered = None

    if is_valid(temp_raw, *TEMP_RANGE):
        temp_filtered = temp_filter.update(temp_raw)
    else:
        log_event('invalid_reading', temp=temp_raw,
                   note=f'Nhiet do ngoai khoang hop le {TEMP_RANGE}')

    if is_valid(humi_raw, *HUMI_RANGE):
        humi_filtered = humi_filter.update(humi_raw)
    else:
        log_event('invalid_reading', humi=humi_raw,
                   note=f'Do am ngoai khoang hop le {HUMI_RANGE}')

    if temp_filtered is not None and humi_filtered is not None:
        lcd.setCursor(0, 0)
        lcd.write('T:{0:2},H:{1:2}'.format(temp_filtered, humi_filtered))
        log_event('reading', temp=f'{temp_filtered:.1f}', humi=f'{humi_filtered:.1f}', note='OK')
        print(f"temp: raw={temp_raw:.1f} filtered={temp_filtered:.1f}, "
              f"humi: raw={humi_raw:.1f} filtered={humi_filtered:.1f}")

    return temp_filtered, humi_filtered


def show_light_value():
    light_raw = sensor_light.Light

    if not is_valid(light_raw, *LIGHT_RANGE):
        log_event('invalid_reading', light=light_raw,
                   note=f'Anh sang ngoai khoang hop le {LIGHT_RANGE}')
        return None

    light_filtered = light_filter.update(light_raw)
    lcd.setCursor(1, 0)
    lcd.write('l:{0:3}'.format(light_filtered))
    log_event('reading', light=f'{light_filtered:.1f}', note='OK')
    print(f"light: raw={light_raw} filtered={light_filtered:.1f}")
    return light_filtered


def show_rotary_angle_value():
    voltage_raw = sensor_rotary_angle.read_voltage(2)

    if not is_valid(voltage_raw, *VOLTAGE_RANGE):
        log_event('invalid_reading', voltage=voltage_raw,
                   note=f'Dien ap ngoai khoang hop le {VOLTAGE_RANGE}')
        return None

    voltage_filtered = voltage_filter.update(voltage_raw)
    lcd.setCursor(1, 9)
    lcd.write(',V:{0:4}'.format(voltage_filtered))
    log_event('reading', voltage=f'{voltage_filtered:.1f}', note='OK')
    print(f"voltage: raw={voltage_raw} filtered={voltage_filtered:.1f}")
    return voltage_filtered


def show_distance_value():
    distance_raw = sensor_distance.get_distance()

    if not is_valid(distance_raw, *DISTANCE_RANGE):
        log_event('invalid_reading', distance=distance_raw,
                   note=f'Khoang cach ngoai khoang hop le {DISTANCE_RANGE}')
        return None

    distance_filtered = distance_filter.update(distance_raw)
    lcd.setCursor(0, 9)
    lcd.write(',D:{0:3.0f}'.format(distance_filtered))
    log_event('reading', distance=f'{distance_filtered:.1f}', note='OK')
    print(f"Distance: raw={distance_raw:.1f} filtered={distance_filtered:.1f}")
    return distance_filtered


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
    payload = json.dumps(fields)

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
        fields['field1'] = averages['temp']
    if 'humi' in averages:
        fields['field2'] = averages['humi']
    if 'light' in averages:
        fields['field3'] = averages['light']
    if 'distance' in averages:
        fields['field4'] = averages['distance']
    if 'voltage' in averages:
        fields['field5'] = averages['voltage']

    send_to_thingspeak_http(**fields)
    send_to_thingspeak_mqtt(**fields)


def main():
    lcd.clear()

    window_start = time.time()
    window = {'temp': [], 'humi': [], 'light': [], 'distance': [], 'voltage': []}

    try:
        while True:
            temp_f, humi_f = show_temp_humi_value()
            light_f = show_light_value()
            voltage_f = show_rotary_angle_value()
            distance_f = show_distance_value()

            if temp_f is not None:
                window['temp'].append(temp_f)
            if humi_f is not None:
                window['humi'].append(humi_f)
            if light_f is not None:
                window['light'].append(light_f)
            if voltage_f is not None:
                window['voltage'].append(voltage_f)
            if distance_f is not None:
                window['distance'].append(distance_f)

            if time.time() - window_start >= WINDOW_SECONDS:
                send_window_average(window)
                window = {k: [] for k in window}
                window_start = time.time()

            print("###############################")
            sleep(DISPLAY_INTERVAL)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")


if __name__ == '__main__':
    main()
