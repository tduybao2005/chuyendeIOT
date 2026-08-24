from grove.display.jhd1802 import JHD1802
from gpiozero import LED
from time import sleep
from datetime import datetime
import csv
import os
import requests

DISPLAY_INTERVAL = 1
LOG_FILE = 'server_log.csv'

HTTP_CHANNEL_ID = "DIEN_HTTP_CHANNEL_ID_CUA_BAN"
THINGSPEAK_READ_API_KEY = "DAN_READ_API_KEY_CUA_BAN_VAO_DAY"
THINGSPEAK_READ_URL = f"https://api.thingspeak.com/channels/{HTTP_CHANNEL_ID}/feeds/last.json"

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


def fetch_average_from_server():
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


def main():
    lcd.clear()
    try:
        while True:
            temp, humi, voltage = fetch_average_from_server()

            print(f"temp: {temp}")
            print(f"humi: {humi}")
            print(f"voltage: {voltage}")

            if temp is not None or humi is not None or voltage is not None:
                show_on_lcd(temp, humi, voltage)
                control_leds(temp, humi, voltage)
                log_event('reading', temp=temp, humi=humi, voltage=voltage, note='OK')

            print("###############################")
            sleep(DISPLAY_INTERVAL)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")


if __name__ == '__main__':
    main()
