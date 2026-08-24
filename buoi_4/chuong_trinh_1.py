from grove.adc import ADC
from seeed_dht import DHT
from time import sleep
import time
import requests
import paho.mqtt.client as mqtt

DISPLAY_INTERVAL = 1
WINDOW_SECONDS = 20

TEMP_RANGE = (0, 100)
HUMI_RANGE = (20, 95)
VOLTAGE_RANGE = (0, 3.3)

THINGSPEAK_URL = "https://api.thingspeak.com/update.json"
HTTP_WRITE_API_KEY = "DAN_HTTP_WRITE_API_KEY_CUA_BAN_VAO_DAY"

MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 1883
MQTT_CHANNEL_ID = "DIEN_MQTT_CHANNEL_ID_CUA_BAN"
MQTT_CLIENT_ID = "DIEN_MQTT_CLIENT_ID_CUA_BAN"
MQTT_USERNAME = "DIEN_MQTT_USERNAME_CUA_BAN"
MQTT_PASSWORD = "DIEN_MQTT_PASSWORD_CUA_BAN"


def is_valid(value, min_val, max_val):
    return min_val <= value <= max_val


sensor_temp_humi = DHT('11', 16)
sensor_rotary_angle = ADC(0x08)


def show_temp_humi_value():
    humi_raw, temp_raw = sensor_temp_humi.read()
    humi_raw, temp_raw = int(humi_raw), int(temp_raw)

    temp_valid = is_valid(temp_raw, *TEMP_RANGE)
    humi_valid = is_valid(humi_raw, *HUMI_RANGE)

    return (temp_raw if temp_valid else None), (humi_raw if humi_valid else None)


def show_voltage_value():
    voltage_raw = sensor_rotary_angle.read_voltage(2) / 1000
    valid = is_valid(voltage_raw, *VOLTAGE_RANGE)

    return voltage_raw if valid else None


def send_to_thingspeak_http(**fields):
    payload = {"api_key": HTTP_WRITE_API_KEY}
    payload.update(fields)
    try:
        response = requests.post(THINGSPEAK_URL, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def send_to_thingspeak_mqtt(**fields):
    topic = f"channels/{MQTT_CHANNEL_ID}/publish"
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
            return False

        info = client.publish(topic, payload, qos=1)
        info.wait_for_publish(timeout=5)
        client.loop_stop()
        client.disconnect()
        return True
    except Exception:
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


def main():
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

            sleep(DISPLAY_INTERVAL)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
