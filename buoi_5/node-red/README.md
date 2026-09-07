# Buổi 5 - Web bằng Node-RED (thay thế web-expo)

Thay vì viết web bằng Expo/React Native, phần Web của bài này được làm bằng
**Node-RED chạy ngay trên Raspberry Pi** (cùng máy với `../raspberry/chuong_trinh_pi.py`),
với giao diện là **HTML/CSS/JS tự viết** (không dùng các widget dựng sẵn của
`node-red-dashboard`) nhúng qua 1 node `ui_template` duy nhất - đầy đủ tính
năng y hệt bản Expo cũ: xem nhiệt độ/độ ẩm mới nhất + biểu đồ, đổi chế độ
Auto/Manual, bật/tắt LED - Buzzer - Relay ở chế độ Manual.

## Vì sao chạy trên Raspberry Pi thay vì máy khác?

Pi vốn đã online 24/7 để đọc cảm biến, nên chạy luôn Node-RED trên đó giúp
chỉ cần 1 thiết bị duy nhất, không cần deploy web lên đâu khác. Dashboard
truy cập được từ bất kỳ máy nào cùng mạng LAN (hoặc qua Tailscale nếu cần
truy cập từ xa) tại `http://<ip-cua-pi>:1880/ui`.

## Kiến trúc / luồng dữ liệu

Giữ nguyên đúng quy ước 2-channel ThingSpeak đã dùng ở `chuong_trinh_pi.py`
và bản Expo cũ (bắt buộc theo đề bài: chế độ Auto/Manual phải qua MQTT,
lệnh LED/Buzzer/Relay phải qua HTTP):

- **Kênh HTTP** (field1-4: cảm biến, field5-7: LED/Buzzer/Relay): flow đọc
  `GET feeds.json` mỗi 15 giây để vẽ biểu đồ + hiển thị trạng thái mới nhất,
  và gửi lệnh LED/Buzzer/Relay bằng `POST update.json` (tự động thử lại tối
  đa 3 lần, cách nhau 3s, vì ThingSpeak giới hạn tối thiểu 15s/lần ghi lên
  cùng 1 channel và trả về HTTP 200 kèm nội dung "0" khi bị từ chối - không
  phải mã lỗi HTTP).
- **Kênh MQTT riêng** (chỉ 1 field "Mode"): flow subscribe MQTT (đường
  nhanh) CỘNG VỚI polling HTTP mỗi 15s (dự phòng, vì ThingSpeak không lưu
  retained message thật sự trên topic dạng channel-feed này) để đảm bảo
  không bao giờ bị mất cập nhật chế độ. Đổi chế độ trên dashboard sẽ publish
  MQTT (retain) lên kênh này.

Sơ đồ node trong `flows.json`:

```
[inject 15s] -> [chuẩn bị URL] -> [GET kênh HTTP] -> [xử lý -> http_data] ---\
[mqtt in: subscribe Mode]      -> [xử lý -> mode_update] ------------------- -> [ui_template (dashboard)]
[inject 15s] -> [chuẩn bị URL] -> [GET kênh Mode] -> [xử lý -> mode_update] -/
                                                                                     |
                                                                     (scope.send trên trinh duyet)
                                                                                     v
                                                            [switch: mode / thiết bị]
                                                             |                    |
                                              [chuẩn bị lệnh Mode]      [chuẩn bị lệnh thiết bị]
                                                     |                            |
                                            [mqtt out: publish]         [POST update.json] --check--> (thử lại 3 lần / 3s nếu bị giới hạn 15s)
```

## Cài đặt trên Raspberry Pi

```bash
# Cai Node-RED (v4 - tuong thich Node.js v20 co san tren Pi; v5 can Node >=22.9)
sudo npm install -g --unsafe-perm node-red@4

# Chay lan dau de Node-RED tao thu muc ~/.node-red, roi cai them dashboard
node-red &   # Ctrl+C sau khi thay "Server now running" de dung lai
cd ~/.node-red && npm install node-red-dashboard@3.6.6
```

### Chạy như systemd service (khuyến nghị, tự khởi động lại khi crash/reboot)

Tạo `/lib/systemd/system/nodered.service`:

```ini
[Unit]
Description=Node-RED graphical event wiring tool
Wants=network.target
After=network.target

[Service]
Type=simple
User=pi
Group=pi
Nice=10
ExecStart=/usr/local/bin/node-red --max-old-space-size=256
Restart=on-failure
RestartSec=5
KillSignal=SIGINT
SyslogIdentifier=Node-RED
WorkingDirectory=/home/pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nodered.service
```

### Import flow

1. Điền thông tin ThingSpeak thật của bạn vào `flows.json` trước khi import
   (tìm các placeholder dạng `DIEN_..._CUA_BAN`, xem bảng bên dưới) - **không
   commit giá trị thật lên git công khai**.
2. Mở Node-RED editor tại `http://<ip-cua-pi>:1880`, vào menu **☰ > Import**,
   dán nội dung `flows.json` đã điền, chọn **Import to: new flow**, rồi bấm
   **Deploy**.
3. Truy cập dashboard tại `http://<ip-cua-pi>:1880/ui`.

Cách khác (không cần mở trình duyệt editor): deploy thẳng qua Admin API -

```bash
curl -X POST http://<ip-cua-pi>:1880/flows \
  -H "Content-Type: application/json" \
  -H "Node-RED-API-Version: v2" \
  -H "Node-RED-Deployment-Type: full" \
  -d "{\"flows\": $(cat flows.json)}"
```

### Các placeholder cần điền (giống hệt quy ước trong `../raspberry/chuong_trinh_pi.py`)

| Placeholder | Vị trí trong flow | Ý nghĩa |
|---|---|---|
| `DIEN_CHANNEL_ID_HTTP_CUA_BAN` | 2 node function đọc kênh HTTP | ID kênh ThingSpeak chứa cảm biến + lệnh thiết bị |
| `DIEN_READ_API_KEY_CUA_BAN` | node "Chuan bi URL doc kenh HTTP" | Read API Key của kênh HTTP |
| `DIEN_WRITE_API_KEY_CUA_BAN` | node "Chuan bi lenh thiet bi (HTTP)" | Write API Key của kênh HTTP |
| `DIEN_CHANNEL_ID_MQTT_CUA_BAN` | node đọc/ghi chế độ | ID kênh ThingSpeak riêng chỉ có field "Mode" |
| `DIEN_READ_API_KEY_CUA_KENH_MQTT_CUA_BAN` | node "Chuan bi URL doc che do du phong" | Read API Key của kênh Mode |
| `DIEN_MQTT_CLIENT_ID_CUA_BAN` | config node `mqtt-broker` | Client ID MQTT (**phải trùng username** - yêu cầu của ThingSpeak) |
| `DIEN_MQTT_USERNAME_CUA_BAN` | config node `mqtt-broker` (credentials) | Username MQTT (= Client ID) |
| `DIEN_MQTT_PASSWORD_CUA_BAN` | config node `mqtt-broker` (credentials) | MQTT API Key (mật khẩu) |

> Lưu ý (đã kiểm chứng khi test thật): Node-RED/Web và Raspberry Pi phải
> dùng **CHUNG 1 danh tính MQTT** (client_id/username/password) vì thiết bị
> MQTT của ThingSpeak chỉ cấp 1 danh tính cho mỗi channel.

## File trong thư mục này

- `flows.json` - flow Node-RED đầy đủ (đã điền placeholder, sẵn sàng import).
- `dashboard_template.html` - đúng nội dung HTML/CSS/JS đang nhúng trong node
  `ui_template` của `flows.json` (tách riêng ra để dễ đọc/diff bằng git; khi
  chỉnh sửa giao diện, sửa ở đây rồi dán lại vào field `format` của node
  `ui_template` trong `flows.json`).
