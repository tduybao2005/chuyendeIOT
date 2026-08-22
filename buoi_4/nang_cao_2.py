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
LOG_FILE = 'server_log_nangcao.csv'

THINGSPEAK_CHANNEL_ID = "DIEN_CHANNEL_ID_CUA_BAN"
THINGSPEAK_READ_API_KEY = "DAN_READ_API_KEY_CUA_BAN_VAO_DAY"
THINGSPEAK_READ_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json"

MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "DIEN_MQTT_CLIENT_ID_CUA_BAN"
MQTT_USERNAME = "DIEN_MQTT_USERNAME_CUA_BAN"
MQTT_PASSWORD = "DIEN_MQTT_PASSWORD_CUA_BAN"
MQTT_SUBSCRIBE_TOPIC = f"channels/{THINGSPEAK_CHANNEL_ID}/subscribe"

LOG_FIELDS = ['timestamp', 'event', 'temp', 'humi', 'voltage', 'note']


def log_event(event, temp='', humi='', voltage='', note=''):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'event': event,
            'temp': temp, 'humi': humi, 'voltage': voltage,
            'note': note,
        })


lcd = JHD1802()
led_red = LED(26)
led_yellow = LED(22)
led_blue = LED(24)

latest = {'temp': None, 'humi': None, 'voltage': None}


def control_leds(temp, humi, voltage):
    if temp is not None:
        if temp > 40:
            led_red.on()
        elif temp < 30:
            led_red.off()

    if humi is not None:
        if humi > 70:
            led_yellow.on()
        elif humi < 40:
            led_yellow.off()

    if voltage is not None:
        if voltage > 2:
            led_blue.on()
        elif voltage < 1:
            led_blue.off()


def show_on_lcd(temp, humi, voltage):
    temp_str = '{0:2.0f}'.format(temp) if temp is not None else '  '
    humi_str = '{0:2.0f}'.format(humi) if humi is not None else '  '
    voltage_str = '{0:4.2f}'.format(voltage) if voltage is not None else '    '

    lcd.setCursor(0, 0)
    lcd.write('T:{0},H:{1}'.format(temp_str, humi_str))
    lcd.setCursor(1, 0)
    lcd.write('V:{0}'.format(voltage_str))


def apply_new_data(temp, humi, voltage):
    latest['temp'] = temp
    latest['humi'] = humi
    latest['voltage'] = voltage

    show_on_lcd(temp, humi, voltage)
    control_leds(temp, humi, voltage)
    log_event('reading', temp=temp, humi=humi, voltage=voltage, note='OK')


def fetch_average_from_server_http():
    params = {'api_key': THINGSPEAK_READ_API_KEY}
    try:
        response = requests.get(THINGSPEAK_READ_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[HTTP] Doc du lieu that bai: {e}")
        log_event('fetch_error', note=str(e))
        return None, None, None

    temp = data.get('field1')
    humi = data.get('field2')
    voltage = data.get('field3')

    temp = float(temp) if temp is not None else None
    humi = float(humi) if humi is not None else None
    voltage = float(voltage) if voltage is not None else None

    return temp, humi, voltage


def on_mqtt_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[MQTT] Ket noi thanh cong, dang subscribe: {MQTT_SUBSCRIBE_TOPIC}")
        client.subscribe(MQTT_SUBSCRIBE_TOPIC)
    else:
        print(f"[MQTT] Ket noi/xac thuc that bai, reason_code={reason_code}")


def on_mqtt_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[MQTT] Payload khong hop le: {e}")
        return

    temp = data.get('field1')
    humi = data.get('field2')
    voltage = data.get('field3')

    temp = float(temp) if temp is not None else None
    humi = float(humi) if humi is not None else None
    voltage = float(voltage) if voltage is not None else None

    print(f"[MQTT] Nhan du lieu moi: temp={temp}, humi={humi}, voltage={voltage}")
    apply_new_data(temp, humi, voltage)


def start_mqtt_subscriber():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)
    client.loop_start()
    return client


def main():
    lcd.clear()
    mqtt_client = start_mqtt_subscriber()

    try:
        while True:
            temp, humi, voltage = fetch_average_from_server_http()

            print(f"temp: {temp}")
            print(f"humi: {humi}")
            print(f"voltage: {voltage}")

            if temp is not None or humi is not None or voltage is not None:
                apply_new_data(temp, humi, voltage)

            print("###############################")
            sleep(DISPLAY_INTERVAL)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == '__main__':
    main()
