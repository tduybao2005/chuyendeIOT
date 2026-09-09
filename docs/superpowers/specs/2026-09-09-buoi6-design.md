# Buổi 6 — Thiết kế

Ngày: 2026-09-09

## Bối cảnh

Buổi 6 dùng lại **nguyên đề bài mức độ 3 của buổi 5 lớp thầy Thanh**
(`buoi_5/lopthaythanh/muc_do_3*.jpeg`), giữ nguyên mọi điều kiện vận hành,
nhưng:

- đổi sang bộ channel/API key ThingSpeak mới (`buoi_6_channel_1/2`);
- thay giao diện Node-RED bằng bản của `buoi_5/lopthaykien` (nền tối 2 cột);
- thêm khả năng tự khởi động khi bật nguồn và tự phục hồi khi lỗi.

Mã nguồn gốc để kế thừa:

| Lấy từ | Lấy cái gì |
|---|---|
| `buoi_5/lopthaythanh/raspberry/chuong_trinh_pi.py` | Điều kiện Auto, LCD, dải hợp lệ cảm biến, chu kỳ |
| `buoi_5/lopthaykien` (bản đang chạy trên Pi) | Kiến trúc 2 channel, luồng đọc lệnh nhịp 1s, giao diện, bố cục flow |

## Yêu cầu bắt buộc (trích đề mức độ 3)

**Raspberry**

- Đọc nhiệt độ, độ ẩm, điện áp biến trở, khoảng cách **mỗi 1 giây**.
- Trung bình 4 giá trị **mỗi 20 giây**, gửi **1 gói tin/20 giây** lên ThingSpeak.
- Chạy liên tục **ít nhất 45 phút**; 2 gói liền kề cách nhau **dưới 90 giây**.
- **Dữ liệu bất thường không được gửi** — phải đọc lại và gửi dữ liệu khác.
- **LCD 16x2 hiển thị thời gian hiện tại**.
- Manual: LED/Buzzer/Relay điều khiển bằng nút trên Web, trạng thái đổi
  **chậm nhất 2 giây** kể từ khi dữ liệu nút nhấn lên Server thành công.
- Auto:
  - LED sáng **18h–22h**, tắt thời gian còn lại.
  - Buzzer kêu khi nhiệt độ **> 40°C**, tắt khi **< 30°C**, giữa giữ nguyên.
  - Relay đóng khi độ ẩm **> 70%**, tắt khi **< 40%**, giữa giữ nguyên.

**Web**

- Bố cục cân đối, trực quan; hiển thị tốt trên iPad.
- Nút chọn Auto/Manual; nút bật/tắt LED (tự quyết số lượng).
- Đồ thị nhiệt độ và độ ẩm đọc từ Server.
- Biểu tượng trạng thái bật/tắt LED, Buzzer, Relay.
- Biểu tượng chế độ Auto/Manual.
- Cửa sổ giá trị nhiệt độ/độ ẩm của lần cập nhật cuối.
- Cửa sổ thời gian hiện tại.
- **Nút chọn chế độ bắt buộc MQTT; nút điều khiển bắt buộc HTTP.**

**Gợi ý của đề:** dùng `try/except` để lỗi cảm biến hoặc rớt mạng thì chương
trình chạy tiếp, không cần khởi động lại.

## Tính năng thêm cho buổi 6

1. Tự khởi động khi bật nguồn Raspberry (systemd, `enable`).
2. Tự khởi động lại khi lỗi cảm biến hoặc rớt mạng kéo dài.

## Kiến trúc

### Hai channel ThingSpeak

| Channel | Field | Ai ghi | Giao thức ghi | Ai đọc |
|---|---|---|---|---|
| **Cảm biến** `DIEN_CHANNEL_ID_CAM_BIEN_CUA_BAN` | 1 Temperature · 2 Humidity · 3 Voltage · 4 Distance | Pi | HTTP mỗi 20s | Web (HTTP mỗi 15s) |
| **Lệnh** `DIEN_CHANNEL_ID_LENH_CUA_BAN` | 1 LED · 2 Relay · 3 Buzzer · 4 Mode | Web | MQTT (Mode) + HTTP (thiết bị) | Pi (HTTP poll 1s) |

Key:

- Cảm biến: write `DIEN_WRITE_API_KEY_CAM_BIEN_CUA_BAN`, read `DIEN_READ_API_KEY_CAM_BIEN_CUA_BAN`
- Lệnh: write `DIEN_WRITE_API_KEY_LENH_CUA_BAN`, read `DIEN_READ_API_KEY_LENH_CUA_BAN`
- MQTT: clientId = username = `DIEN_MQTT_CLIENT_ID_CUA_BAN`,
  password = `DIEN_MQTT_PASSWORD_CUA_BAN`

Tách 2 channel vì ThingSpeak giới hạn ~17 giây giữa 2 lần ghi lên **cùng một**
channel. Nếu để chung, Pi ghi cảm biến mỗi 20s sẽ chiếm gần hết khe ghi, nút
HTTP hầu như không chen được.

### Phân chia giao thức 8 nút

| Nút | Giao thức | Field trên channel LỆNH |
|---|---|---|
| Auto | **MQTT** | field4 = 0 |
| Manual | **MQTT** | field4 = 1 |
| LED Bật / Tắt | **HTTP** | field1 = 1 / 0 |
| Relay Bật / Tắt | **HTTP** | field2 = 1 / 0 |
| Buzzer Bật / Tắt | **HTTP** | field3 = 1 / 0 |

### Vì sao Pi chỉ đọc lệnh bằng HTTP polling

ThingSpeak cấp **một** bộ danh tính MQTT cho mỗi channel (client_id phải trùng
username). Nếu Web và Pi cùng mở kết nối bằng chung client_id, broker sẽ đá
kết nối cũ mỗi lần có kết nối mới, gây rớt lệnh liên tục. Vì vậy chỉ Web giữ
kết nối MQTT; Pi đọc bằng HTTP polling mỗi giây — vẫn nhận đủ cả 8 nút vì
ThingSpeak lưu chung mọi lần ghi (bất kể giao thức) vào cùng một feed.

Nhịp poll phải là **chu kỳ cố định 1 giây** (trừ đi thời gian request), không
phải `sleep(1)` sau mỗi request — nếu không chu kỳ thực là 1s + thời gian
request (~0.3–0.9s) và độ trễ tối đa chạm mốc 2 giây của đề.

## Thành phần

```
buoi_6/
├── README.md
├── raspberry/
│   └── chuong_trinh_pi.py
├── node-red/
│   ├── flows.json
│   ├── dashboard_template.html
│   └── README.md
└── systemd/
    └── iot-buoi6.service
```

### `raspberry/chuong_trinh_pi.py`

Ba luồng công việc:

1. **Luồng chính** (nhịp 1s): đọc 4 cảm biến → lọc dải hợp lệ → gom cửa sổ
   trung bình → áp dụng Auto/Manual ra GPIO → cập nhật LCD → mỗi 20s gửi
   trung bình lên channel CẢM BIẾN.
2. **Luồng đọc lệnh** (chu kỳ cố định 1s): `GET feeds.json` channel LỆNH,
   quét ngược lấy giá trị không null đầu tiên cho từng field, đổi thì áp dụng
   ngay và ghi log có mili giây.
3. **Đồng bộ lúc khởi động**: đọc `fields/<n>/last.json` của cả 4 field lệnh
   để không mất chế độ Manual / trạng thái thiết bị sau khi khởi động lại.

Dải hợp lệ (dữ liệu ngoài dải bị loại, **không gửi lên Server**):

| Đại lượng | Dải |
|---|---|
| Nhiệt độ | 0 – 100 °C |
| Độ ẩm | 20 – 95 % |
| Điện áp | 0 – 3.3 V |
| Khoảng cách | 2 – 350 cm |

LCD 16x2:

```
Time 14:23:07
AUTO L1 B0 R1
```

### Tự phục hồi

Hai bộ đếm lỗi **liên tiếp**, mỗi lần thành công thì reset về 0:

| Bộ đếm | Tăng khi | Ngưỡng | Hành động |
|---|---|---|---|
| `sensor_fail_streak` | cả 4 cảm biến đều không đọc được trong một vòng | 30 | ghi log rồi `sys.exit(1)` |
| `network_fail_streak` | GET/POST ThingSpeak ném `RequestException` | 20 | ghi log rồi `sys.exit(1)` |

Lỗi lẻ tẻ chỉ được `try/except` nuốt và chạy tiếp (đúng gợi ý của đề). Chỉ khi
lỗi kéo dài liên tiếp mới thoát để systemd dựng lại tiến trình sạch. Dọn GPIO
trước khi thoát để lần chạy sau không bị chiếm chân.

### `systemd/iot-buoi6.service`

```ini
[Unit]
Description=IoT buoi 6 - doc cam bien va dieu khien qua ThingSpeak
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/buoi6
ExecStart=/usr/bin/python3 -u /home/pi/buoi6/chuong_trinh_pi.py
Restart=always
RestartSec=10
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
```

`StartLimitIntervalSec=0` để systemd không bao giờ bỏ cuộc sau nhiều lần
restart. `network-online.target` để không chạy trước khi có mạng lúc mới bật
nguồn.

Node-RED cũng bật `systemctl enable nodered` để lên cùng lúc.

### Node-RED

Giao diện: bê nguyên bản của lopthaykien (nền tối, 2 cột, `position:fixed`
gói đúng một khung hình không cuộn, đã kiểm tra ở 1600×950 / 1024×768 /
390×844). Chỉ đổi tiêu đề sang buổi 6.

Bố cục flow: 2 tầng, các khối gom vào nhóm có tên, vị trí cột tự tính theo độ
dài tên node để không khối nào chồng nhau.

```
TANG 1  [inject 15s] -> [prep URL] -> [GET cam bien] -> [parse] --\
        [inject 5s]  -> [prep URL] -> [GET lenh]     -> [parse] --+-> [DASHBOARD]
                                                                  |
TANG 2  [switch 2 nhanh] <--------------------------------------- /
          mode     -> [prep MQTT] -> [mqtt out]
          thiet bi -> [prep HTTP] -> [POST update.json] -> [check/retry 3s]
```

## Kiểm thử

1. `python3 -m py_compile` chương trình Pi; `json.load` flows.json.
2. Chạy service, xác nhận `systemctl is-active` và log không lỗi.
3. Đo độ trễ 8 nút: đối chiếu mốc mili giây trong log Node-RED
   (`GUI LENH MQTT` / `GUI THANH CONG`) với log Pi (`DA AP DUNG XONG`),
   cả hai cùng đồng hồ Pi. Yêu cầu **< 2 giây** khi channel rảnh.
4. Kiểm tra dashboard không sinh thanh cuộn ở 3 khổ màn hình.
5. Thử tự phục hồi: `kill` tiến trình → systemd phải dựng lại sau ~10s.
6. Thử tự khởi động: `reboot` Pi → cả service và Node-RED phải tự lên.

## Rủi ro

- Chương trình lopthaykien nếu còn chạy sẽ **tranh GPIO** với service buổi 6.
  Phải dừng hẳn trước khi bật service.
- Node-RED chỉ chạy được một flow tại một thời điểm. Nạp flow buổi 6 sẽ thay
  flow lopthaykien đang chạy; sao lưu `flows.json` trước.
