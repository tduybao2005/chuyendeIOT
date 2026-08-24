from grove.adc import ADC
from seeed_dht import DHT
from time import sleep
import time
import random
import requests

DISPLAY_INTERVAL = 1
WINDOW_SECONDS = 20

TEMP_RANGE = (0, 100)
HUMI_RANGE = (20, 95)
VOLTAGE_RANGE = (0, 3.3)

THINGSPEAK_UPDATE_URL = "https://api.thingspeak.com/update.json"
THINGSPEAK_WRITE_API_KEY = "DIEN_WRITE_API_KEY_CUA_BAN_VAO_DAY"

# field1: nhiet do trung binh, field2: do am trung binh
# field3: dien ap trung binh tren bien tro, field4: tin hieu random (0-100)


def is_valid(value, min_val, max_val):
    return min_val <= value <= max_val


sensor_temp_humi = DHT('11', 16)
sensor_rotary_angle = ADC(0x08)


def read_temp_humi():
    humi_raw, temp_raw = sensor_temp_humi.read()
    humi_raw, temp_raw = int(humi_raw), int(temp_raw)
    temp_valid = is_valid(temp_raw, *TEMP_RANGE)
    humi_valid = is_valid(humi_raw, *HUMI_RANGE)
    return (temp_raw if temp_valid else None), (humi_raw if humi_valid else None)


def read_voltage():
    voltage_raw = sensor_rotary_angle.read_voltage(2) / 1000
    return voltage_raw if is_valid(voltage_raw, *VOLTAGE_RANGE) else None


def send_to_thingspeak(**fields):
    payload = {"api_key": THINGSPEAK_WRITE_API_KEY}
    payload.update(fields)
    try:
        response = requests.post(THINGSPEAK_UPDATE_URL, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def send_window_average(window):
    averages = {key: (sum(values) / len(values)) for key, values in window.items() if values}
    fields = {}
    if 'temp' in averages:
        fields['field1'] = round(averages['temp'])
    if 'humi' in averages:
        fields['field2'] = round(averages['humi'])
    if 'voltage' in averages:
        fields['field3'] = round(averages['voltage'], 2)
    fields['field4'] = random.randint(0, 100)
    send_to_thingspeak(**fields)


def main():
    window_start = time.time()
    window = {'temp': [], 'humi': [], 'voltage': []}
    try:
        while True:
            temp_r, humi_r = read_temp_humi()
            voltage_r = read_voltage()
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
            sleep(DISPLAY_INTERVAL)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
