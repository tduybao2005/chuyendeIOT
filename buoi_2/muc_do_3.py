from gpiozero import LED
from signal import pause
from grove.adc import ADC
from seeed_dht import DHT
from grove.display.jhd1802 import JHD1802
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger
from time import sleep
from collections import deque
import time
import requests
import matplotlib
matplotlib.use('Agg')  # khong co man hinh GUI tren Pi qua SSH
import matplotlib.pyplot as plt

class GroveLightSensor:
    def __init__(self, channel):
        self.channel = channel
        self.adc = ADC(address = 0x08)

    @property
    def Light(self):
        value = self.adc.read(self.channel)
        return value

class MovingAverageFilter:
    """Loc trung binh truot (moving average) tren N mau gan nhat."""

    def __init__(self, window_size=5):
        self._buffer = deque(maxlen=window_size)

    def update(self, value):
        self._buffer.append(value)
        return sum(self._buffer) / len(self._buffer)

lcd = JHD1802()
sensor_temp_humi = DHT('11', 16)
sensor_distance = GroveUltrasonicRanger(5)
sensor_light = GroveLightSensor(0)
sensor_rotary_angle = ADC(0x08)

led_red = LED(26)
led_yellow = LED(22)
led_blue = LED(24)

# filter rieng cho tung tin hieu can loc nhieu (temp, humi)
temp_filter = MovingAverageFilter(window_size=5)
humi_filter = MovingAverageFilter(window_size=5)

# luu lai lich su raw/filtered de ve bieu do so sanh luc thoat chuong trinh
history_temp_raw = []
history_temp_filtered = []
history_humi_raw = []
history_humi_filtered = []

# cau hinh gui du lieu len ThingSpeak (HTTP POST, dinh dang JSON)
THINGSPEAK_URL = "https://api.thingspeak.com/update.json"
THINGSPEAK_API_KEY = "DAN_WRITE_API_KEY_CUA_BAN_VAO_DAY"
THINGSPEAK_MIN_INTERVAL = 15  # giay - gioi han toi thieu cua ThingSpeak free tier
_last_thingspeak_sent_at = 0.0


def send_to_thingspeak(**fields):
    """Gui du lieu len ThingSpeak qua HTTP POST, dinh dang JSON.

    Tu dong gioi han toi thieu THINGSPEAK_MIN_INTERVAL giay giua 2 lan goi,
    nen co the goi ham nay moi vong lap ma khong lo bi ThingSpeak tu choi
    (429). Khong nem exception ra ngoai de tranh lam crash vong lap chinh
    khi mang loi/mat Wi-Fi.
    """
    global _last_thingspeak_sent_at

    now = time.time()
    if now - _last_thingspeak_sent_at < THINGSPEAK_MIN_INTERVAL:
        return False

    payload = {"api_key": THINGSPEAK_API_KEY}
    payload.update(fields)

    try:
        response = requests.post(THINGSPEAK_URL, json=payload, timeout=5)
        response.raise_for_status()
        _last_thingspeak_sent_at = now
        print(f"[ThingSpeak] Gui thanh cong, entry_id={response.text}")
        return True
    except requests.RequestException as e:
        print(f"[ThingSpeak] Gui that bai: {e}")
        return False


def show_temp_humi_value():
    humi_raw, temp_raw = sensor_temp_humi.read()
    humi_raw, temp_raw = float(humi_raw), float(temp_raw)

    temp_filtered = temp_filter.update(temp_raw)
    humi_filtered = humi_filter.update(humi_raw)

    history_temp_raw.append(temp_raw)
    history_temp_filtered.append(temp_filtered)
    history_humi_raw.append(humi_raw)
    history_humi_filtered.append(humi_filtered)

    lcd.setCursor(0, 0)
    lcd.write('T:{0:2},H:{1:2}'.format(temp_filtered, humi_filtered))

    # dung gia tri DA LOC de bat/tat LED, tranh nhap nhay do nhieu tuc thoi
    if temp_filtered > 40:
        led_red.on()
    elif temp_filtered < 30:
        led_red.off()

    if humi_filtered > 70:
        led_yellow.on()
    elif humi_filtered < 40:
        led_yellow.off()

    print(f"temp: raw={temp_raw:.1f} filtered={temp_filtered:.1f}, "
          f"humi: raw={humi_raw:.1f} filtered={humi_filtered:.1f}")

    return temp_raw, temp_filtered, humi_raw, humi_filtered

def show_light_value():
    light = sensor_light.Light
    lcd.setCursor(1,0)
    lcd.write('l:{0:3}'.format(light))
    print(f"light: {light}")
    return light

def show_rotary_angle_value():
    value = sensor_rotary_angle.read_voltage(2)
    lcd.setCursor(1, 9)
    lcd.write(',V:{0:4}'.format(value))

    if value / 1000 > 2:
        led_blue.on()
    elif value / 1000 < 1:
        led_blue.off()

    print(f"voltage: {value}")
    return value

def show_distance_value():
    distance = sensor_distance.get_distance()
    lcd.setCursor(0, 9)
    lcd.write(',D:{0:3.0f}'.format(distance))
    print(f"Distance: {distance}")
    return distance


def plot_noise_comparison():
    """Ve bieu do so sanh du lieu raw va da loc (temp, humi), luu ra PNG."""
    if not history_temp_raw:
        print("Chua co du lieu de ve bieu do.")
        return

    plt.figure(figsize=(10, 6))

    plt.subplot(2, 1, 1)
    plt.plot(history_temp_raw, label='Nhiet do - Raw', alpha=0.5, marker='o')
    plt.plot(history_temp_filtered, label='Nhiet do - Da loc (MA)', marker='s')
    plt.ylabel('Nhiet do (C)')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(history_humi_raw, label='Do am - Raw', alpha=0.5, marker='o')
    plt.plot(history_humi_filtered, label='Do am - Da loc (MA)', marker='s')
    plt.xlabel('Lan do')
    plt.ylabel('Do am (%)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('noise_comparison.png')
    print("Da luu bieu do so sanh: noise_comparison.png")


def main():
    lcd.clear()
    try:
        while True:
            temp_raw, temp_filtered, humi_raw, humi_filtered = show_temp_humi_value()
            light = show_light_value()
            voltage = show_rotary_angle_value()
            distance = show_distance_value()

            send_to_thingspeak(
                field1=temp_raw, field2=temp_filtered,
                field3=humi_raw, field4=humi_filtered,
                field5=light, field6=distance, field7=voltage,
            )

            sleep(1)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
        plot_noise_comparison()

if __name__ == '__main__':
    main()
