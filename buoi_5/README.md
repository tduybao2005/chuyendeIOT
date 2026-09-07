# Buổi 5 - Nhóm 3

Hệ thống Raspberry Pi + Web giám sát & điều khiển qua ThingSpeak.

- **Raspberry Pi** (`raspberry/chuong_trinh_pi.py`): đọc cảm biến, hiển thị
  LCD, điều khiển LED/Buzzer/Relay (chế độ Auto hoặc Manual theo lệnh từ Web).
- **Web** (`node-red/`): dashboard **Node-RED chạy ngay trên Raspberry Pi**,
  giao diện HTML/CSS/JS tự viết (không dùng widget dựng sẵn), xem chi tiết ở
  `node-red/README.md`.

## Cấu trúc thư mục

```
buoi_5/
├── raspberry/
│   └── chuong_trinh_pi.py     # Chuong trinh chay tren Raspberry Pi
└── node-red/                  # Web: dashboard Node-RED (HTML/CSS/JS tuy chinh)
    ├── flows.json               # Flow Node-RED day du (dien placeholder truoc khi dung)
    ├── dashboard_template.html  # Noi dung HTML/CSS/JS cua node ui_template (de doc/diff)
    └── README.md                # Huong dan cai dat + import flow chi tiet
```

## Vì sao dùng 2 kênh ThingSpeak riêng?

Đề bài yêu cầu: đổi chế độ Auto/Manual **bắt buộc qua MQTT**, lệnh
LED/Buzzer/Relay **bắt buộc qua HTTP**. Khi tạo thiết bị MQTT trên
ThingSpeak (Devices > MQTT > Add a new device), thiết bị chỉ được **cấp
quyền subscribe/publish trên 1 channel duy nhất** - khác với channel dùng
để ghi/đọc HTTP. Vì vậy hệ thống dùng 2 channel:

| Channel | Field | Ai ghi | Giao thức | Bắt buộc? |
|---|---|---|---|---|
| **HTTP** (`buoi_5_channel_1`) | field1 Nhiệt độ TB (20s) | Pi | HTTP | Tùy chọn HTTP/MQTT (đã chọn HTTP) |
| | field2 Độ ẩm TB (20s) | Pi | HTTP | như trên |
| | field3 Điện áp biến trở TB (20s) | Pi | HTTP | như trên |
| | field4 Khoảng cách TB (20s) | Pi | HTTP | như trên |
| | field5 Lệnh LED (0/1) | Web | **HTTP** | **Bắt buộc** |
| | field6 Lệnh Buzzer (0/1) | Web | **HTTP** | **Bắt buộc** |
| | field7 Lệnh Relay (0/1) | Web | **HTTP** | **Bắt buộc** |
| **MQTT** (`buoi_5_channel_2`, riêng, chỉ 1 field) | field1 "Mode" (0=Auto, 1=Manual) | Web | **MQTT** | **Bắt buộc** |

**Lưu ý về giao thức đọc lại lệnh (không bị đề giới hạn):**
- Pi đọc lệnh LED/Buzzer/Relay bằng cách **poll HTTP mỗi giây** trên kênh
  HTTP (không thể subscribe MQTT trên kênh này).
- Pi đọc chế độ Auto/Manual bằng **CẢ 2 cách**: MQTT subscribe (đường
  nhanh, gần như tức thời) **cộng với** poll HTTP mỗi giây trên kênh MQTT
  (dự phòng) - vì ThingSpeak **không lưu retained message thật sự** trên
  topic dạng channel-feed, và vì ThingSpeak yêu cầu client_id phải trùng
  username nên Web/Pi buộc dùng chung 1 danh tính MQTT → mỗi lần Web publish
  có thể làm Pi mất gói tin tạm thời. Dùng cả 2 đường đảm bảo không bao giờ
  bị "kẹt" ở chế độ cũ.

## GPIO / cổng Grove trên Raspberry Pi

| Module | Cổng | GPIO (BCM) |
|---|---|---|
| DHT (nhiệt độ, độ ẩm) | D5 | GPIO5 |
| Cảm biến siêu âm (khoảng cách) | D16 | GPIO16 |
| Biến trở (điện áp) qua Grove ADC | A2 | — |
| LCD 16x2 (JHD1802) | I2C-1 (`0x3E` + `0x62`) | — |
| LED | D18 | GPIO18 |
| Buzzer | D24 | GPIO24 |
| Relay | D26 | GPIO26 |

## Cách chạy Raspberry Pi

1. Điền các giá trị `DIEN_..._CUA_BAN` (channel ID, read/write API key, MQTT
   client ID/username/password) thật vào đầu file `raspberry/chuong_trinh_pi.py`.
2. Chạy: `python3 chuong_trinh_pi.py`

## Cách chạy Web (Node-RED)

Xem hướng dẫn đầy đủ (cài Node-RED, import flow, điền placeholder, chạy như
systemd service) tại **[`node-red/README.md`](node-red/README.md)**. Tóm tắt:

1. Cài Node-RED v4 + `node-red-dashboard@3.6.6` trên Raspberry Pi.
2. Điền các placeholder `DIEN_..._CUA_BAN` thật vào `node-red/flows.json`
   (danh sách đầy đủ nằm trong `node-red/README.md`) - **không commit giá
   trị thật lên git**.
3. Import flow qua Node-RED editor hoặc Admin API, Deploy.
4. Mở dashboard tại `http://<ip-cua-pi>:1880/ui`.

## Đã kiểm tra trên phần cứng thật (Raspberry Pi `pi4-tdbao`)

- Cảm biến DHT/ADC/siêu âm đọc và gửi trung bình lên ThingSpeak đúng chu kỳ.
- LCD hiển thị giờ + trạng thái Auto/Manual + LED/Buzzer/Relay.
- Chế độ Auto/Manual: dashboard Node-RED publish MQTT → Pi nhận qua subscribe
  (đường nhanh) hoặc qua HTTP polling dự phòng, xác nhận bằng cách đọc lại
  feed trên ThingSpeak sau khi bấm nút.
- Lệnh LED/Buzzer/Relay: dashboard gửi HTTP `update.json`, tự động thử lại
  khi bị ThingSpeak từ chối do giới hạn 15s/lần ghi; Pi poll lại và áp dụng
  đúng trạng thái (đã xác nhận qua feed `entry_id` mới xuất hiện đúng field).
- Dashboard responsive: kiểm tra ở độ rộng desktop (1280px) và mobile (390px)
  qua Playwright - xem `screenshots/`.
