# Buổi 6 - Nhóm 3 - Mức độ 3

Đề bài dùng lại **nguyên yêu cầu mức độ 3 của buổi 5 (lớp thầy Thanh)** — xem
ảnh đề ở `../buoi_5/lopthaythanh/muc_do_3*.jpeg` — giữ nguyên mọi điều kiện
vận hành, nhưng đổi sang bộ channel/API key mới, làm lại giao diện Web và
thêm khả năng tự khởi động / tự phục hồi.

```
buoi_6/
├── KIEN_TRUC.md                # so do kien truc he thong (Mermaid)
├── so_do_ham_pi.drawio         # so do CHI TIET TUNG HAM trong chuong_trinh_pi.py (draw.io)
├── raspberry/
│   └── chuong_trinh_pi.py      # chuong trinh chay tren Raspberry Pi
├── node-red/
│   ├── flows.json              # flow Node-RED day du
│   ├── dashboard_template.html # noi dung node ui_template (de doc/diff)
│   └── README.md               # huong dan cai dat + nap flow
└── systemd/
    └── iot-buoi6.service       # unit tu khoi dong khi bat nguon
```

Xem sơ đồ kiến trúc đầy đủ (luồng dữ liệu, vòng đời một lệnh) tại
**[`KIEN_TRUC.md`](KIEN_TRUC.md)**. Sơ đồ chi tiết **từng hàm** trong
`chuong_trinh_pi.py` (gọi hàm nào, khi nào gọi `fail_exit()`...) nằm ở
**[`so_do_ham_pi.drawio`](so_do_ham_pi.drawio)** — mở và chỉnh sửa trực tiếp
tại [app.diagrams.net](https://app.diagrams.net/) → **File → Open from →
GitHub** → chọn repo `tduybao2005/chuyendeIOT`, nhánh `main`, file
`buoi_6/so_do_ham_pi.drawio` (đăng nhập GitHub trong draw.io để lưu thẳng lại
lên repo sau khi sửa).

## Khác gì so với buổi 5 (lớp thầy Thanh)

| | Buổi 5 | Buổi 6 |
|---|---|---|
| Channel | `buoi_5_channel_1/2` | `buoi_6_channel_1/2` |
| Bố cục field | Kênh HTTP chứa cả cảm biến (1-4) lẫn lệnh (5-7); kênh MQTT chỉ 1 field Mode | Kênh 1 **chỉ cảm biến**, kênh 2 **chỉ lệnh** (4 field) |
| Pi đọc chế độ | MQTT subscribe + HTTP polling dự phòng | **Chỉ HTTP polling** (nhịp cố định 1s) |
| Giao diện Web | nền sáng, xếp dọc | nền tối, 2 cột, gói đúng 1 khung hình |
| Tự khởi động | chạy tay | **systemd, tự lên khi bật nguồn** |
| Tự phục hồi | chỉ try/except | try/except **+ tự khởi động lại khi lỗi kéo dài** |

Điều kiện vận hành (ngưỡng Auto, LCD, chu kỳ, dải hợp lệ) **giữ nguyên** như
buổi 5.

## Hai channel ThingSpeak

| Channel | Field | Ai ghi | Giao thức | Ai đọc |
|---|---|---|---|---|
| **CẢM BIẾN** `DIEN_CHANNEL_ID_CAM_BIEN_CUA_BAN` | field1 Temperature | Pi | HTTP mỗi 20s | Web (vẽ đồ thị) |
| | field2 Humidity | Pi | HTTP | như trên |
| | field3 Voltage | Pi | HTTP | như trên |
| | field4 Distance | Pi | HTTP | như trên |
| **LỆNH** `DIEN_CHANNEL_ID_LENH_CUA_BAN` | field1 LED (0/1) | Web | **HTTP** | Pi (HTTP poll 1s) |
| | field2 Relay (0/1) | Web | **HTTP** | như trên |
| | field3 Buzzer (0/1) | Web | **HTTP** | như trên |
| | field4 Mode (0=Auto, 1=Manual) | Web | **MQTT** | như trên |

### Phân chia giao thức cho 8 nút

Đề mức độ 3 ghi rõ: *"Bắt buộc nút nhấn chọn chế độ phải sử dụng giao thức
MQTT; nút nhấn điều khiển phải sử dụng giao thức HTTP để gửi dữ liệu lên
Server."*

| Nút | Giao thức | Field |
|---|---|---|
| Auto | **MQTT** | field4 = 0 |
| Manual | **MQTT** | field4 = 1 |
| LED Bật / Tắt | **HTTP** | field1 = 1 / 0 |
| Relay Bật / Tắt | **HTTP** | field2 = 1 / 0 |
| Buzzer Bật / Tắt | **HTTP** | field3 = 1 / 0 |

Minh chứng giao thức xem trực tiếp trên **sơ đồ khối của flow Node-RED**: một
node `switch` tách hẳn 2 nhánh — nhánh MQTT dùng node `mqtt out` (nhóm 5a),
nhánh HTTP dùng node `http request` (nhóm 5b).

### Vì sao phải tách 2 channel?

ThingSpeak giới hạn tối thiểu **~17 giây giữa 2 lần ghi lên cùng 1 channel**,
trong khi đề bắt buộc Pi gửi trung bình cảm biến **mỗi 20 giây**. Nếu để chung
1 channel thì mỗi chu kỳ chỉ còn vài giây trống cho lệnh nút bấm ⇒ lệnh HTTP
từ Web bị từ chối liên tục. Tách 2 channel thì channel LỆNH luôn rảnh ⇒ bấm
nút ăn ngay.

### Vì sao Pi chỉ đọc lệnh qua HTTP polling, không subscribe MQTT?

ThingSpeak chỉ cấp **đúng 1 bộ danh tính MQTT** cho mỗi channel (`client_id` =
`username`). Theo chuẩn MQTT, client_id phải duy nhất cho mỗi kết nối đang mở
— nếu Web (publish) và Pi (subscribe) cùng dùng chung 1 client_id thì broker
buộc phải đá kết nối cũ mỗi khi có kết nối mới, tạo vòng lặp đá nhau liên tục
làm rớt phần lớn lệnh publish.

**Giải pháp:** chỉ Web giữ kết nối MQTT; Pi bỏ hẳn subscribe, **chỉ đọc lệnh
qua HTTP polling mỗi giây**. Vẫn nhận đủ cả 8 nút (kể cả 2 nút Web ghi bằng
MQTT) vì ThingSpeak lưu chung mọi lần ghi — bất kể giao thức — vào cùng 1 feed
của channel.

**Nhịp poll phải là chu kỳ cố định 1 giây** (trừ đi thời gian request), không
phải `sleep(1)` sau mỗi request. Nếu chỉ `sleep(1)` thì chu kỳ thực là
`1s + thời gian request (~0.3-0.9s)`, khiến độ trễ tối đa chạm mốc 2 giây của
đề (đã đo được 1.977s trước khi sửa).

## Điều kiện vận hành (theo đề, giữ nguyên từ buổi 5)

- Đọc nhiệt độ, độ ẩm, điện áp biến trở, khoảng cách **mỗi 1 giây**.
- Trung bình 4 giá trị **mỗi 20 giây**, gửi **1 gói tin/20 giây**.
- Chạy liên tục **ít nhất 45 phút**; 2 gói liền kề cách nhau **dưới 90 giây**.
- **Dữ liệu bất thường không được gửi** — lọc theo dải hợp lệ rồi đọc lại:

  | Đại lượng | Dải hợp lệ |
  |---|---|
  | Nhiệt độ | 0 – 100 °C |
  | Độ ẩm | 20 – 95 % |
  | Điện áp | 0 – 3.3 V |
  | Khoảng cách | 2 – 350 cm |

- **LCD 16x2** hiển thị thời gian hiện tại:

  ```
  Time 14:23:07
  AUTO L1 B0 R1
  ```

- **Chế độ Auto:**
  - LED sáng **18h – 22h**, tắt khoảng thời gian còn lại.
  - Buzzer kêu khi nhiệt độ **> 40 °C**, tắt khi **< 30 °C**, giữa giữ nguyên.
  - Relay đóng khi độ ẩm **> 70 %**, tắt khi **< 40 %**, giữa giữ nguyên.
- **Chế độ Manual:** LED/Buzzer/Relay theo 6 nút trên Web, trạng thái đổi
  **chậm nhất 2 giây** kể từ khi dữ liệu nút nhấn lên Server thành công.

## GPIO / cổng Grove

| Module | Cổng | GPIO (BCM) |
|---|---|---|
| DHT (nhiệt độ, độ ẩm) | D5 | GPIO5 |
| Cảm biến siêu âm (khoảng cách) | D16 | GPIO16 |
| Biến trở (điện áp) qua Grove ADC | I2C `0x08`, kênh 2 | — |
| LCD 16x2 (JHD1802) | I2C-1 (`0x3E` + `0x62`) | — |
| LED | D18 | GPIO18 |
| Buzzer | D24 | GPIO24 |
| Relay | D26 | GPIO26 |

## Tính năng thêm của buổi 6

### 1. Tự khởi động khi bật nguồn

```bash
sudo cp systemd/iot-buoi6.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now iot-buoi6      # tu chay tu lan bat nguon sau
sudo systemctl enable nodered              # Node-RED cung tu len
```

Unit chờ `network-online.target` nên không chạy trước khi có Wi-Fi lúc mới bật
nguồn.

### 2. Tự khởi động lại khi lỗi cảm biến hoặc rớt mạng

Đề gợi ý dùng `try/except` để lỗi lẻ tẻ thì chương trình chạy tiếp — phần đó
giữ nguyên. Ngoài ra chương trình đếm số lỗi **liên tiếp** (mỗi lần thành công
reset về 0); vượt ngưỡng thì thoát để systemd dựng lại một tiến trình sạch:

| Bộ đếm | Tăng khi | Ngưỡng | Hành động |
|---|---|---|---|
| `sensor_fail_streak` | cả 4 cảm biến đều không ra giá trị hợp lệ trong 1 vòng | 30 (~30s) | ghi log rồi thoát mã 1 |
| `network_fail_streak` | gọi ThingSpeak thất bại | 20 | ghi log rồi thoát mã 1 |

`Restart=always` + `RestartSec=10` + `StartLimitIntervalSec=0` ⇒ systemd bật
lại sau 10 giây và **không bao giờ bỏ cuộc**.

Chương trình dùng `os._exit()` chứ không phải `sys.exit()` vì hàm thoát có thể
được gọi từ **luồng đọc lệnh**; `sys.exit()` trong luồng phụ chỉ kết thúc đúng
luồng đó, tiến trình vẫn sống nhưng không còn đọc lệnh nữa. Vì `os._exit()` bỏ
qua khối `finally` nên chương trình tự tắt LED/Buzzer/Relay trước khi thoát.

## Cách chạy

**Raspberry Pi**

```bash
# chay tay de xem log truc tiep
cd ~/buoi6 && python3 chuong_trinh_pi.py

# hoac chay bang service (khuyen nghi)
sudo systemctl start iot-buoi6
sudo journalctl -u iot-buoi6 -f
```

**Web (Node-RED)** — xem `node-red/README.md`. Tóm tắt: cài Node-RED v4 +
`node-red-dashboard@3.6.6`, nạp `node-red/flows.json`, nhập user/password MQTT
vào node `mqtt-broker`, Deploy, mở `http://<ip-cua-pi>:1880/ui`.

## Kiểm tra

| Hạng mục | Cách kiểm |
|---|---|
| Độ trễ nút < 2s | Đối chiếu mốc mili giây trong log Node-RED (`GUI LENH MQTT` / `GUI THANH CONG`) với log Pi (`DA AP DUNG XONG`) — cả hai cùng đồng hồ Pi |
| Giao diện 1 khung hình | Kiểm tra không sinh thanh cuộn ở 1600×950, 1024×768 (iPad), 390×844 |
| Tự phục hồi | `sudo systemctl kill iot-buoi6` → service phải tự lên lại sau ~10s |
| Tự khởi động | `sudo reboot` → cả `iot-buoi6` và `nodered` phải tự chạy |
