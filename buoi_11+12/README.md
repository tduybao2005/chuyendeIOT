# Buổi 11+12 — Hệ thống Master / Slave 1 + Gateway / Slave 2 + LoRa

| Máy | Vai trò | Chương trình |
|---|---|---|
| Laptop (192.168.44.179) | **Master**: EMQX + web HTTP :8000 + MongoDB Atlas | `master/server.py` |
| pi4-tdbao (192.168.44.211) | **Slave 1** (DHT11, biến trở, khoảng cách, LED1, LED2) + **Gateway** MQTT ⇄ UDP | `slave1/slave1.py`, `gateway/gateway.py` |
| Pi nhóm 3 (192.168.44.176) | **Slave 2** (LED3, Buzzer, Relay, ánh sáng, LCD) + USB LoRa ⇄ IoT node 3 | `slave2/slave2.py` |

```
 Web --HTTP--> Master --MQTT (EMQX)--> pi4-tdbao [slave1 + gateway] --UDP--> Pi nhóm 3 [slave2] --LoRa--> node 3
```

## 1. Bảng cắm thiết bị (Grove Base Hat)

Tắt Pi trước khi cắm. LED Grove: chân dài của bóng cắm vào lỗ "+".

**pi4-tdbao (Slave 1 + Gateway)**

| Thiết bị | Cổng | Code |
|---|---|---|
| DHT11 | D5 | `DHT("11", 5)` |
| Cảm biến khoảng cách | D16 | `GroveUltrasonicRanger(16)` |
| LED 1 | D18 | `LED(18)` |
| LED 2 | D22 | `LED(22)` |
| Biến trở | A0 | `ADC(0x08).read_voltage(0)` |

**Pi nhóm 3 (Slave 2)**

| Thiết bị | Cổng | Code |
|---|---|---|
| LED 3 | D18 | `LED(18)` |
| Buzzer | D24 | `Buzzer(24)` |
| Relay | D26 | `OutputDevice(26)` |
| Cảm biến ánh sáng | A0 | `ADC(0x08).read(0)` |
| LCD 16x2 | I2C (cổng nào cũng được) | `JHD1802()` (0x3E) |
| USB LoRa | cổng USB | `/dev/ttyUSB0` |

## 2. Giao thức

| Topic MQTT | Publish | Subscribe | Nội dung |
|---|---|---|---|
| `buoi11/slave1/trung_binh` | slave1, 20 s/lần | master | nhiet_do, do_am, bien_tro (V), khoang_cach (cm), so_mau |
| `buoi11/slave1/trang_thai` | slave1, 1 s/lần | master | led1, led2 |
| `buoi11/slave2/trung_binh` | gateway, 20 s/lần | master | anh_sang (0–999), so_mau |
| `buoi11/slave2/trang_thai` | gateway, 1 s/lần | master | led3, buzzer, relay, light, alarm, lora_ok |
| `buoi11/dieu_khien` (retain) | master, khi đổi | slave1, gateway | led1, led2, led3, buzzer, relay, light, alarm |

UDP: gateway → Slave 2 cổng 5005 (lệnh, gửi lại mỗi giây); Slave 2 → gateway cổng 5006 (`{"loai": "trang_thai" | "trung_binh", ...}`).
LoRa node 3 (giống buổi 10): reg 9 = Light, reg 8 = Alarm Light.

## 3. Quy tắc điều khiển (master)

- Cảm biến đọc mỗi 1 s, gửi **trung bình 20 lần** (lần đọc lỗi không tính). Trạng thái 7 thiết bị gửi + lưu Database **mỗi giây**.
- Light / Alarm Light: **Thủ công** = nút trên web; **Tự động** = bật trong khung giờ [bật, tắt) (qua đêm được, vd 18:00 → 06:00).
- Ngưỡng: nhiệt độ TB ≥ T **hoặc** độ ẩm TB ≥ H → các LED đã tick bị ép BẬT; hết vượt → theo nút. Ô trống = bỏ điều kiện đó.
- Mỗi lần **Set** thay toàn bộ cài đặt cũ (lưu vào collection `cai_dat`, khởi động lại master sẽ nạp bản cuối).
- Thời gian bản ghi do master gán (đồng hồ Pi nhóm 3 bị sai).
- LoRa: slave 2 ghi Light (reg 9) / Alarm (reg 8) rồi **đọc lại** 2 reg này để web hiện trạng thái thật của node 3; node chưa theo lệnh thì ghi lại. Node 3 chỉ trả lời khi địa chỉ master trong khung lệnh = **9** (dongle CP2102 trên trường; địa chỉ 0 như buổi 10 thì node không trả lời) — đổi bằng `IOT_LORA_DIA_CHI`. Không có USB LoRa / node tắt thì hiện "(LoRa không phản hồi)", phần còn lại vẫn chạy.
- Pi nhóm 3: đã tắt AutorunProg (supervisord) để không tranh GPIO/LCD. Bật lại: sửa `autostart=true`, `autorestart=true` trong `/etc/supervisor/conf.d/AutorunProg.conf` rồi `sudo supervisorctl update`.

## 4. Chạy

**Laptop (master)** — EMQX đã chạy sẵn (`systemctl status emqx`):
```bash
cd buoi_11+12
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd master && cp .env.example .env   # dien MONGODB_URI (dung lai cua buoi 9)
../.venv/bin/python server.py       # web: http://localhost:8000
```
(Laptop có ROS: chạy `env -u PYTHONPATH ../.venv/bin/python server.py`.)

**pi4-tdbao** — copy `chung/trung_binh.py`, `slave1/slave1.py`, `gateway/gateway.py` vào `~/iot_buoi11/`:
```bash
cd ~/iot_buoi11
IOT_MQTT_HOST=<IP laptop> nohup python3 -u slave1.py > slave1.log 2>&1 &
IOT_MQTT_HOST=<IP laptop> IOT_SLAVE2_HOST=<IP Pi slave 2> nohup python3 -u gateway.py > gateway.log 2>&1 &
```

**Pi Slave 2** — copy `chung/trung_binh.py`, `slave2/slave2.py`, `slave2/IoT_Driver_USB.py` vào `~/iot_buoi11/`:
```bash
cd ~/iot_buoi11
IOT_GATEWAY_HOST=<IP pi4-tdbao> nohup python3 -u slave2.py > slave2.log 2>&1 &
```
IP đổi theo mạng (DHCP) → xem bằng `ip -4 -br addr` rồi sửa biến môi trường. Mặc định trong code là mạng trường: laptop 192.168.44.179, pi4-tdbao 192.168.44.211, Pi nhóm 3 192.168.44.176.

Pi Slave 2 phải **không còn chương trình nào khác giữ GPIO 18/24/26 hoặc LCD** (vd supervisord của bài cũ) — kiểm tra bằng `pgrep -af python3`. grove.py bản cũ (0.6, không có `grove.display`) vẫn chạy được: `slave2.py` tự điều khiển LCD qua I2C.

## 5. Kiểm thử

- Logic master + trung bình 20 mẫu: `cd buoi_11+12 && .venv/bin/pytest -q` (máy có ROS: thêm `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` phía trước)
- Xem dữ liệu chạy trên broker: `mosquitto_sub -h localhost -t 'buoi11/#' -v`
- Gửi lệnh tay (không qua web): `mosquitto_pub -h localhost -t buoi11/dieu_khien -r -m '{"led1":1,"led2":0,"led3":0,"buzzer":0,"relay":0,"light":0,"alarm":0}'` (xong thì xóa retained: `mosquitto_pub -h localhost -t buoi11/dieu_khien -r -n`)
- Database: MongoDB Atlas → DB `iot_buoi11`, collection `trang_thai` (mỗi giây), `trung_binh` (mỗi 20 giây), `cai_dat` (mỗi lần Set).
