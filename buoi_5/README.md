# Buổi 5 - Nhóm 4

Hệ thống Web + Raspberry Pi giám sát & điều khiển qua ThingSpeak.

## Cấu trúc thư mục

```
buoi_5/
├── raspberry/
│   └── chuong_trinh_pi.py     # Chương trình chạy trên Raspberry Pi
└── web-expo/                  # Giao diện Web (Expo + TypeScript)
    ├── config.ts               # Điền API key / channel ID / MQTT credentials tại đây
    ├── App.tsx
    ├── hooks/                  # Logic (không dính UI)
    │   ├── useThingSpeakData.ts   # Đọc dữ liệu qua HTTP (polling)
    │   ├── useMqttMode.ts         # Kết nối MQTT (chọn chế độ + nghe realtime)
    │   └── useDeviceCommand.ts    # Gửi lệnh LED/Buzzer/Relay qua HTTP
    └── components/              # Từng khối giao diện, 1 file/1 chức năng
        ├── ModeToggle.tsx
        ├── DeviceControlPanel.tsx
        ├── LatestReadingCard.tsx
        ├── ClockCard.tsx
        └── TempHumiChart.tsx
```

## Sơ đồ field ThingSpeak (dùng đủ 8 field)

| Field | Dữ liệu | Ai ghi | Giao thức ghi | Bắt buộc? |
|---|---|---|---|---|
| field1 | Nhiệt độ trung bình (20s) | Pi | HTTP | Tùy chọn HTTP/MQTT (đã chọn HTTP) |
| field2 | Độ ẩm trung bình (20s) | Pi | HTTP | như trên |
| field3 | Điện áp biến trở TB (20s) | Pi | HTTP | như trên |
| field4 | Khoảng cách TB (20s) | Pi | HTTP | như trên |
| field5 | Chế độ (0=Auto, 1=Manual) | Web | **MQTT** | **Bắt buộc** |
| field6 | Lệnh LED (0/1) | Web | **HTTP** | **Bắt buộc** |
| field7 | Lệnh Buzzer (0/1) | Web | **HTTP** | **Bắt buộc** |
| field8 | Lệnh Relay (0/1) | Web | **HTTP** | **Bắt buộc** |

**Lưu ý về giao thức (đọc kỹ để không nhầm):**
- Việc **Raspberry Pi gửi dữ liệu cảm biến lên Server** (field1-4): đề cho **chọn 1 trong 2** giao thức (HTTP hoặc MQTT) → code đã chọn **HTTP**.
- Việc **Web gửi lệnh điều khiển lên Server** (field5-8): đề **bắt buộc dùng cả 2** — nút chọn chế độ dùng MQTT, nút điều khiển LED/Buzzer/Relay dùng HTTP. Không được chọn 1 trong 2 ở phần này.
- Việc Pi **đọc lại** lệnh điều khiển từ Server không bị đề giới hạn giao thức — code Pi dùng MQTT subscribe (topic số 1 - toàn kênh) để phản hồi tức thời (đáp ứng yêu cầu đổi trạng thái ≤ 2 giây).

## GPIO / cổng Grove trên Raspberry Pi

| Module | Cổng | GPIO (BCM) |
|---|---|---|
| DHT (nhiệt độ, độ ẩm) | D5 | GPIO5 |
| Cảm biến siêu âm (khoảng cách) | D16 | GPIO16 |
| Biến trở (điện áp) qua Grove ADC | I2C `0x08`, kênh 2 | — |
| LCD 16x2 (JHD1802) | I2C-1 (`0x3E` + `0x62`) | — |
| LED | D18 | GPIO18 |
| Buzzer | D24 | GPIO24 |
| Relay | D26 | GPIO26 |

## Cách chạy Raspberry Pi

1. Điền `THINGSPEAK_CHANNEL_ID`, `THINGSPEAK_WRITE_API_KEY`, `MQTT_CLIENT_ID`, `MQTT_USERNAME`, `MQTT_PASSWORD` thật vào đầu file `raspberry/chuong_trinh_pi.py`.
2. Chạy: `python3 chuong_trinh_pi.py`

## Cách chạy Web (Expo)

1. Điền thông tin thật vào `web-expo/config.ts` (channel ID, read/write API key, MQTT client ID/username/password - lấy từ ThingSpeak > Devices > MQTT > Add a new device).
2. Cài đặt & chạy:
   ```
   cd web-expo
   npm install
   npm run web
   ```
3. Mở trên iPad: dùng trình duyệt Safari truy cập địa chỉ Expo cấp (hoặc `npx expo export --platform web` rồi host file tĩnh trong thư mục `dist/`).

**Lưu ý:** giao diện được xây bằng Expo nhưng nhắm tới mục tiêu **Web** như đề yêu cầu (đã build-test qua `expo export --platform web` thành công). Chạy qua Expo Go trên native Android/iOS chưa được đảm bảo do thư viện `mqtt` cần môi trường WebSocket kiểu trình duyệt.

## Đã kiểm tra (không cần phần cứng)

- `npx tsc --noEmit` — không lỗi type.
- `npx expo export --platform web` — build thành công (232 modules), xác nhận Metro bundler xử lý được thư viện `mqtt` + `react-native-svg`.
- Raspberry Pi: không thể test trực tiếp (Pi hiện không cắm điện), code viết theo đúng phong cách các file mẫu đã chạy được trước đó trong repo.
