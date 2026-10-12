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
- Pi nhóm 3: đã tắt AutorunProg (supervisord) để không tranh GPIO/LCD. Bật lại: sửa `autostart=true`, `autorestart=true` trong `/etc/supervisor/conf.d/AutorunProg.conf` rồi `sudo supervisorctl update`.
