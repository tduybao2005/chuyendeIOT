# Hướng dẫn cài đặt thư viện Grove (grove.py) trên Raspberry Pi (pi4-tdbao.local)

Thư viện gốc: https://github.com/Seeed-Studio/grove.py (thư viện Python chính thức của Seeed Studio cho Grove Base Hat trên Raspberry Pi)

## Thông tin máy đích

- Host: `pi4-tdbao.local` (Raspberry Pi 4 Model B)
- Hệ điều hành: Debian GNU/Linux 13 (trixie), arm64
- Python: 3.13.5 / pip 25.1.1

⚠️ **Lưu ý quan trọng:** Script cài đặt chính thức của Seeed (`curl -sL .../install.sh | sudo bash -s -`) dùng `pip3 install <package>` **không có** `--break-system-packages`. Trên Debian 13 (và Raspberry Pi OS bản mới dựa trên trixie), pip mặc định chặn cài package vào hệ thống theo chuẩn PEP 668 ("externally-managed-environment"), nên script gốc sẽ báo lỗi và dừng giữa chừng. Các bước dưới đây làm thủ công lại đúng các gói mà script gốc cài, nhưng thêm cờ `--break-system-packages` để tương thích Debian 13, đồng thời ưu tiên dùng gói `apt` (đã build sẵn cho arm64) ở những chỗ có thể.

## Bước 1: Bật giao tiếp I2C

Grove Base Hat giao tiếp với Pi qua I2C, cần bật interface này trước:

```bash
sudo raspi-config nonint do_i2c 0
```

Kiểm tra đã bật:

```bash
sudo raspi-config nonint get_i2c   # kết quả phải là 0 (0 = enabled)
grep i2c /boot/firmware/config.txt # phải thấy dòng: dtparam=i2c_arm=on
```

Trên máy này, sau lệnh trên `/dev/i2c-1` xuất hiện ngay không cần khởi động lại. Nếu máy bạn chưa thấy `/dev/i2c-1`, hãy `sudo reboot` rồi kiểm tra lại.

```bash
ls /dev/i2c*
```

## Bước 2: Cài các gói phụ thuộc hệ thống qua apt

```bash
sudo apt-get update
sudo apt-get install -y python3-rpi.gpio python3-smbus i2c-tools python3-dev python3-pip
```

- `python3-rpi.gpio` — thư viện điều khiển chân GPIO (RPi.GPIO)
- `python3-smbus` — giao tiếp I2C qua smbus
- `i2c-tools` — công cụ `i2cdetect`, `i2cget`, `i2cset` để dò/debug thiết bị I2C
- `python3-dev` — header để build các gói pip cần biên dịch (vd. `rpi-ws281x`)
- `python3-pip` — trình quản lý gói Python

> Trên Raspberry Pi OS/Debian bản mới, hệ thống có thể đã cài sẵn `python3-rpi-lgpio` (lớp tương thích RPi.GPIO dùng driver `lgpio`, khuyến nghị cho kernel mới). Lệnh `apt install python3-rpi.gpio` ở trên sẽ **gỡ** `python3-rpi-lgpio` và thay bằng bản `RPi.GPIO` chính thức (đúng như grove.py yêu cầu). Đã kiểm tra trên Pi 4 kernel 6.18, `import RPi.GPIO` vẫn hoạt động bình thường sau khi thay.

Kiểm tra RPi.GPIO hoạt động:

```bash
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print('RPi.GPIO OK', GPIO.VERSION)"
```

## Bước 3: Cài các thư viện cảm biến Grove phụ trợ qua pip

Đây là các thư viện mà `grove.py` phụ thuộc (dùng cho các cảm biến cụ thể như IMU, khí gas, LED strip...):

```bash
pip3 install --break-system-packages --no-cache-dir rpi-ws281x bme680 bmm150 sgp30
```

- `rpi-ws281x` — điều khiển dải LED WS281x (Grove RGB LED Strip)
- `bme680` — cảm biến nhiệt độ/độ ẩm/áp suất/khí gas BME680
- `bmm150` — cảm biến từ trường 3 trục (compass) BMM150
- `sgp30` — cảm biến chất lượng không khí SGP30

## Bước 4: Cài chính thư viện grove.py

```bash
pip3 install --break-system-packages --no-cache-dir --upgrade \
    https://github.com/Seeed-Studio/grove.py/archive/master.zip
```

Lệnh này cài toàn bộ package `Seeed-grove.py` (import bằng `import grove`), bao gồm hơn 50 script điều khiển thiết bị Grove cụ thể, ví dụ:

```
grove_button, grove_led, grove_relay, grove_servo, grove_switch,
grove_temperature_sensor, grove_temperature_humidity_bme680,
grove_ultrasonic_ranger, grove_rotary_angle_sensor, grove_oled_display_128x64,
grove_16x2_lcd, grove_ws2813_rgb_led_strip, grove_gesture_sensor,
grove_i2c_motor_driver, grove_3_axis_compass_bmm150, ... (và nhiều hơn nữa)
```

## Bước 5: Thêm `~/.local/bin` vào PATH (để chạy trực tiếp các lệnh `grove_*`)

Vì cài bằng `pip3 install --break-system-packages` (không phải root), các script trên nằm ở `~/.local/bin`. File `~/.profile` trên Raspberry Pi OS mặc định đã có đoạn tự thêm thư mục này vào PATH nếu nó tồn tại:

```bash
# đã có sẵn trong ~/.profile, không cần chỉnh sửa gì thêm:
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
```

Chỉ cần mở lại phiên SSH mới (hoặc chạy `source ~/.profile`) là các lệnh `grove_button`, `grove_led`, v.v. sẽ chạy được trực tiếp từ terminal.

## Bước 6: Kiểm tra cài đặt

```bash
# import thư viện chính
python3 -c "import grove; print('grove import OK')"
python3 -c "from grove.gpio import GPIO; print('grove.gpio OK')"

# dò thiết bị I2C đang cắm trên Grove Base Hat (bus 1)
sudo i2cdetect -y 1

# danh sách package đã cài
pip3 list --user | grep -iE 'grove|smbus|rpi|ws281x|bme680|bmm150|sgp30'
```

Kết quả trên máy này:

```
bme680         2.0.0
bmm150         0.2.2
rpi_ws281x     5.0.0
Seeed-grove.py 0.7
sgp30          0.1.6
```

## Bước 7: Cài thư viện đọc cảm biến DHT11 (`seeed_dht`)

Cảm biến DHT11 (cắm ở chân **D** trên Grove Base Hat, không phải A — xem giải thích ở phần dưới) dùng giao thức số riêng, đọc qua thư viện `seeed_dht` (module Python `seeed_dht`). Thư viện này **không nằm trong gói `Seeed-grove.py`** đã cài ở Bước 4, phải cài riêng:

```bash
pip3 install --break-system-packages --no-cache-dir seeed-python-dht
```

- Tên gói pip: `seeed-python-dht`, import bằng `from seeed_dht import DHT`
- Có sẵn wheel arm64 trên piwheels (`seeed_python_dht-0.0.2-py3-none-arm64...whl`), cài nhanh, không cần build.

Kiểm tra:

```bash
python3 -c "from seeed_dht import DHT; print('seeed_dht import OK')"
```

Ví dụ dùng (đọc DHT11 cắm ở chân D5):

```python
from seeed_dht import DHT

sensor = DHT('11', 5)   # '11' = model DHT11, 5 = số chân D trên Grove Base Hat
humi, temp = sensor.read()
```

**Vì sao DHT11 cắm chân D chứ không phải A:** DHT11 không xuất điện áp analog liên tục — nó gửi dữ liệu qua một dây tín hiệu số duy nhất theo giao thức timing riêng (bit 0/1 phân biệt bằng độ rộng xung cỡ micro giây). Chân A trên Grove Base Hat chỉ đọc được điện áp qua ADC, không đọc được chuỗi xung có timing chính xác đó; chân D nối thẳng GPIO số của Pi nên đọc/giải mã được.

## Tóm tắt toàn bộ lệnh (copy-paste nhanh)

```bash
# 1. Bật I2C
sudo raspi-config nonint do_i2c 0

# 2. Gói hệ thống
sudo apt-get update
sudo apt-get install -y python3-rpi.gpio python3-smbus i2c-tools python3-dev python3-pip

# 3. Thư viện cảm biến phụ trợ
pip3 install --break-system-packages --no-cache-dir rpi-ws281x bme680 bmm150 sgp30

# 4. Thư viện grove.py chính
pip3 install --break-system-packages --no-cache-dir --upgrade \
    https://github.com/Seeed-Studio/grove.py/archive/master.zip

# 5. Thư viện đọc cảm biến DHT11
pip3 install --break-system-packages --no-cache-dir seeed-python-dht

# 6. Kiểm tra
python3 -c "import grove; print('grove import OK')"
python3 -c "from seeed_dht import DHT; print('seeed_dht import OK')"
sudo i2cdetect -y 1
```

## Gỡ cài đặt

```bash
pip3 uninstall -y Seeed-grove.py seeed-python-dht
```
