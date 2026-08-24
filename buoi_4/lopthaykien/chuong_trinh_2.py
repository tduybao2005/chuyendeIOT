from grove.display.jhd1802 import JHD1802
from gpiozero import LED
from time import sleep
from datetime import datetime
import csv
import os
import json
import requests
import paho.mqtt.client as mqtt

DISPLAY_INTERVAL = 1
LOG_FILE = 'log_chuong_trinh_2.csv'

THINGSPEAK_CHANNEL_ID = "DIEN_CHANNEL_ID_CUA_BAN"
THINGSPEAK_READ_API_KEY = "DIEN_READ_API_KEY_CUA_BAN"
# Nang cao +1: doc du lieu toan bo channel (feeds.json), khong phai chi 1 dong cuoi (feeds/last.json)
THINGSPEAK_FEEDS_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"

MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "DIEN_MQTT_CLIENT_ID_CUA_BAN"
MQTT_USERNAME = "DIEN_MQTT_USERNAME_CUA_BAN"
MQTT_PASSWORD = "DIEN_MQTT_PASSWORD_CUA_BAN"
# Nang cao +1: doc theo topic so 1 (subscribe toan bo channel feed, tat ca field cung luc)
# channels/<channelID>/subscribe/fields/<fieldID> moi la topic so 2 (chi 1 field)
MQTT_SUBSCRIBE_TOPIC = f"channels/{THINGSPEAK_CHANNEL_ID}/subscribe"

LOG_FIELDS = ['timestamp', 'source', 'temp', 'humi', 'voltage', 'random_signal', 'led1', 'led2', 'led3', 'note']


def log_event(source, temp='', humi='', voltage='', random_signal='', led1='', led2='', led3='', note=''):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': source,
            'temp': temp, 'humi': humi, 'voltage': voltage, 'random_signal': random_signal,
            'led1': led1, 'led2': led2, 'led3': led3,
            'note': note,
        })


lcd = JHD1802()
led1 = LED(26)  # bat/tat theo tin hieu random
led2 = LED(22)  # bat/tat theo nhiet do
led3 = LED(24)  # bat/tat theo dien ap tren bien tro

latest_mqtt = {'temp': None, 'humi': None, 'voltage': None, 'random_signal': None}


def to_float(value):
    return float(value) if value is not None else None


def fetch_entire_channel_http():
    params = {'api_key': THINGSPEAK_READ_API_KEY}
    try:
        response = requests.get(THINGSPEAK_FEEDS_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[HTTP] Doc du lieu that bai: {e}")
        log_event('http', note=f'fetch_error: {e}')
        return None
    feeds = data.get('feeds') or []
    if not feeds:
        return None
    last_feed = feeds[-1]
    return {
        'temp': to_float(last_feed.get('field1')),
        'humi': to_float(last_feed.get('field2')),
        'voltage': to_float(last_feed.get('field3')),
        'random_signal': to_float(last_feed.get('field4')),
    }


def on_mqtt_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[MQTT] Ket noi thanh cong, dang subscribe (topic so 1): {MQTT_SUBSCRIBE_TOPIC}")
        client.subscribe(MQTT_SUBSCRIBE_TOPIC)
    else:
        print(f"[MQTT] Ket noi/xac thuc that bai, reason_code={reason_code}")


def on_mqtt_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[MQTT] Payload khong hop le: {e}")
        return
    latest_mqtt['temp'] = to_float(data.get('field1'))
    latest_mqtt['humi'] = to_float(data.get('field2'))
    latest_mqtt['voltage'] = to_float(data.get('field3'))
    latest_mqtt['random_signal'] = to_float(data.get('field4'))
    print(f"[MQTT] Nhan du lieu moi: {latest_mqtt}")


def start_mqtt_subscriber():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)
    client.loop_start()
    return client


def control_leds(temp, voltage, random_signal):
    if random_signal is not None:
        if random_signal > 50:
            led1.on()
        elif random_signal < 50:
            led1.off()
    if temp is not None:
        if temp > 25:
            led2.on()
        elif temp < 24:
            led2.off()
    if voltage is not None:
        if voltage > 2.0:
            led3.on()
        elif voltage < 1.8:
            led3.off()


def show_on_lcd(temp, humi, random_signal):
    temp_str = '{0:2.0f}'.format(temp) if temp is not None else '  '
    humi_str = '{0:2.0f}'.format(humi) if humi is not None else '  '
    rand_str = '{0:3.0f}'.format(random_signal) if random_signal is not None else '   '
    lcd.setCursor(0, 0)
    lcd.write('T:{0} H:{1}'.format(temp_str, humi_str))
    lcd.setCursor(1, 0)
    lcd.write('Rand:{0}'.format(rand_str))


def apply_reading(source, reading):
    if reading is None:
        return
    temp = reading.get('temp')
    humi = reading.get('humi')
    voltage = reading.get('voltage')
    random_signal = reading.get('random_signal')
    print(f"[{source.upper()}] temp={temp} humi={humi} voltage={voltage} random={random_signal}")
    show_on_lcd(temp, humi, random_signal)
    control_leds(temp, voltage, random_signal)
    print("###############################")
    log_event(
        source, temp=temp, humi=humi, voltage=voltage, random_signal=random_signal,
        led1=led1.is_lit, led2=led2.is_lit, led3=led3.is_lit, note='OK',
    )


def main():
    lcd.clear()
    mqtt_client = start_mqtt_subscriber()
    # Nang cao +1: xen ke doc du lieu bang HTTP va MQTT (moi luot doi nguon doc)
    use_http_turn = True
    try:
        while True:
            if use_http_turn:
                reading = fetch_entire_channel_http()
                apply_reading('http', reading)
            else:
                has_data = latest_mqtt['temp'] is not None
                apply_reading('mqtt', latest_mqtt if has_data else None)
            use_http_turn = not use_http_turn
            sleep(DISPLAY_INTERVAL)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == '__main__':
    main()
