# Buổi 5 (lớp thầy Kiến) - Nhóm 7 - Mức độ 3

Hệ thống Raspberry Pi + Web giám sát & điều khiển qua **01 channel ThingSpeak
duy nhất** (khác bản làm cho lớp thầy Thanh dùng 2 channel).

- **Raspberry Pi** (`raspberry/chuong_trinh_pi.py`): đọc 4 cảm biến, hiển thị
  LCD 16x2, điều khiển LED/Buzzer/Relay (chế độ Auto hoặc Manual theo lệnh
  từ Web).
- **Web** (`node-red/`): dashboard **Node-RED** chạy trên Raspberry Pi,
  giao diện HTML/CSS/JS tự viết (không dùng widget dựng sẵn) qua `ui_template`,
  xem chi tiết ở `node-red/README.md`.

## Cấu trúc thư mục

```
buoi_5/lopthaykien/
├── IOT-Bai-5.pdf
├── raspberry/
│   └── chuong_trinh_pi.py     # Chuong trinh chay tren Raspberry Pi
└── node-red/
    ├── flows.json               # Flow Node-RED day du (dien placeholder truoc khi dung)
    ├── dashboard_template.html  # Noi dung HTML/CSS/JS cua node ui_template (de doc/diff)
    └── README.md                # Huong dan cai dat + import flow chi tiet
```

## Vì sao chỉ cần 1 channel (khác bản 2 channel trước)?

Ở bản trước (lớp thầy Thanh) phải tách 2 channel vì đổi Mode bắt buộc dùng
MQTT còn lệnh thiết bị bắt buộc dùng HTTP, và **một thiết bị MQTT của
ThingSpeak chỉ được cấp quyền subscribe/publish trên đúng 1 channel**. Ở bản
này đề cho phép **tự chọn** trong 8 nút (2 Auto/Manual + 6 On/Off của
LED/Buzzer/Relay) nút nào dùng MQTT, nút nào dùng HTTP — nên không cần tách
channel: cả 8 nút cùng ghi vào **field5-field8 của cùng 1 channel**, chỉ khác
giao thức ghi. Channel đã được cấp gồm đủ 8 field, dùng làm:

| Field | Ý nghĩa | Ai ghi | Giao thức |
|---|---|---|---|
| field1 | Nhiệt độ TB (20s) | Pi | HTTP |
| field2 | Độ ẩm TB (20s) | Pi | HTTP |
| field3 | Khoảng cách TB (20s) | Pi | HTTP |
| field4 | Điện áp biến trở TB (20s) | Pi | HTTP |
| field5 | Lệnh LED (0/1) | Web | **MQTT khi Bật (1)**, **HTTP khi Tắt (0)** |
| field6 | Chế độ (0=Auto, 1=Manual) | Web | **MQTT** (cả 2 nút Auto/Manual) |
| field7 | Lệnh Relay (0/1) | Web | **HTTP** (cả 2 nút Bật/Tắt) |
| field8 | Lệnh Buzzer (0/1) | Web | **MQTT khi Bật (1)**, **HTTP khi Tắt (0)** |

### Bảng chia giao thức cho đúng 8 nút nhấn (đề yêu cầu 4 nút MQTT / 4 nút HTTP)

| Nút | Giao thức |
|---|---|
| Auto | MQTT |
| Manual | MQTT |
| LED Bật | MQTT |
| Buzzer Bật | MQTT |
| LED Tắt | HTTP |
| Buzzer Tắt | HTTP |
| Relay Bật | HTTP |
| Relay Tắt | HTTP |

Giao diện Web không hiện nhãn MQTT/HTTP trên nút (theo yêu cầu gọn giao diện);
minh chứng giao thức xem trực tiếp trên **sơ đồ khối của flow Node-RED**: một
node `switch` tách hẳn 2 nhánh xử lý (nhánh MQTT dùng node `mqtt out`, nhánh
HTTP dùng node `http request`) thay vì chỉ chứng minh bằng code.

### Vì sao Raspberry Pi CHỈ đọc lệnh qua HTTP polling, không subscribe MQTT?

Về nguyên lý, MQTT bình thường (Web publish → broker → Pi subscribe) không hề
xung đột gì - hàng nghìn client có thể cùng subscribe một topic mà không ảnh
hưởng nhau. Vấn đề nằm ở **giới hạn riêng của ThingSpeak**: mỗi channel chỉ
được cấp **đúng 1 bộ danh tính MQTT** (`client_id` = `username`), dùng chung
cho cả publish lẫn subscribe. Theo đúng chuẩn MQTT, **client_id phải duy nhất
cho mỗi kết nối đang mở tới broker** - nếu Web (Node-RED publish) và Pi
(subscribe) cùng mở 2 kết nối riêng biệt nhưng dùng **chung 1 client_id**,
broker buộc phải đá kết nối cũ mỗi khi có kết nối mới với cùng client_id đó.

Thực tế đo được: cả Node-RED lẫn Pi đều tự động kết nối lại ngay khi bị đá,
tạo thành vòng lặp **đá nhau liên tục mỗi 10-15 giây, kể cả khi không ai bấm
nút gì** - khiến phần lớn lệnh publish MQTT từ Web bị rớt (không chỉ lúc đang
publish như suy đoán ban đầu). Nếu nhóm được cấp 2 bộ danh tính MQTT riêng
(1 cho Web, 1 cho Pi) thì sẽ không có vấn đề gì.

**Giải pháp**: Pi bỏ hẳn việc mở kết nối MQTT (không subscribe), **chỉ đọc
lệnh qua HTTP polling mỗi giây** - vẫn nhận đủ cả 8 nút (kể cả 4 nút Web ghi
bằng MQTT) vì ThingSpeak lưu chung mọi lần ghi (bất kể giao thức) vào cùng 1
feed của channel. Nhờ vậy chỉ còn Web giữ kết nối MQTT, không còn ai tranh
client_id nữa → publish MQTT từ Web ổn định hẳn. Poll mỗi giây vẫn đảm bảo
đúng yêu cầu "trạng thái LED đổi chậm nhất 2s kể từ khi dữ liệu **đã có**
trên ThingSpeak" (mốc tính là từ lúc dữ liệu lên server, không phải từ lúc
bấm nút).

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

1. Điền các giá trị `DIEN_..._CUA_BAN` thật vào đầu file
   `raspberry/chuong_trinh_pi.py` (channel ID, read/write API key, MQTT
   client ID/username/password).
2. Chạy: `python3 chuong_trinh_pi.py`

## Cách chạy Web (Node-RED)

Xem hướng dẫn đầy đủ tại **[`node-red/README.md`](node-red/README.md)**. Tóm tắt:

1. Cài Node-RED v4 + `node-red-dashboard@3.6.6` trên Raspberry Pi.
2. Điền các placeholder `DIEN_..._CUA_BAN` thật vào `node-red/flows.json`
   (danh sách đầy đủ trong `node-red/README.md`) - **không commit giá trị
   thật lên git**.
3. Import flow qua Node-RED editor hoặc Admin API, Deploy.
4. Mở dashboard tại `http://<ip-cua-pi>:1880/ui`.

## Kết quả đo độ trễ thật trên phần cứng

Đo bằng script chạy **trên chính Raspberry Pi** (dùng chung đồng hồ, không sai
lệch do SSH), tính từ lúc gửi lệnh đến lúc chân GPIO đổi mức thật sự
(đọc `/sys/kernel/debug/gpio`), mỗi lệnh đều đợi ThingSpeak rảnh mới gửi:

| Nút | Giao thức | Lần đo 1 | Lần đo 2 |
|---|---|---|---|
| LED Bật | MQTT | 0.01s | 0.23s |
| LED Tắt | HTTP | 0.77s | 1.37s |
| Buzzer Bật | MQTT | 0.77s | 0.77s |
| Buzzer Tắt | HTTP | 0.93s | 1.04s |
| Relay Bật | HTTP | 0.17s | 1.05s |
| Relay Tắt | HTTP | 0.17s | 0.88s |

⇒ Toàn bộ 8 nút đều **dưới 2s**, đúng yêu cầu đề bài.

**Lưu ý về giới hạn 15s của ThingSpeak** (đã kiểm chứng bằng thực nghiệm):

- **MQTT publish KHÔNG bị giới hạn 15s** - publish chỉ 1.9s sau khi Pi vừa
  ghi vẫn lên được channel ngay.
- **HTTP `update.json` thì BỊ giới hạn**: phải cách ≥15s so với bản ghi gần
  nhất của channel, *bất kể bản ghi đó do ai/giao thức nào tạo ra* (đã đo:
  sau 1 lần ghi MQTT, HTTP bị từ chối ở giây thứ 5.6 / 9.8 / 13.9 và chỉ
  được chấp nhận ở giây 18.1).
- Vì Pi ghi trung bình cảm biến mỗi 20s lên cùng channel (đề bắt buộc), nếu
  bấm nút HTTP đúng lúc kênh vừa có bản ghi thì lệnh phải chờ hết khe 15s
  (flow Node-RED tự thử lại tối đa 10 lần × 3s ≈ 30s để chắc chắn gửi được).
  Con số 2s ở bảng trên - và cũng là mốc đề bài quy định - được tính **từ khi
  dữ liệu đã lên tới ThingSpeak thành công**.

## Chấm điểm mức độ 3 - đối chiếu yêu cầu

- ✅ 4x2 nút nhấn (2 Auto/Manual + 6 LED/Buzzer/Relay On/Off), tự chọn 4 nút
  MQTT / 4 nút HTTP (bảng ở trên).
- ✅ Đồ thị 2 giá trị nhiệt độ, độ ẩm (đọc từ Server, click vào điểm để xem
  giá trị cụ thể).
- ✅ Pi đọc nhiệt độ, độ ẩm, biến trở, khoảng cách mỗi 1s, gửi trung bình
  mỗi 20s liên tục 30 phút.
- ✅ Hiển thị giá trị trung bình lên LCD 16x2.
- ✅ Auto: LED sáng 18h-22h; Buzzer kêu khi nhiệt độ > 37°C, tắt khi < 31°C;
  Relay bật khi độ ẩm > 90%, tắt khi < 60%.
- ✅ Manual: LED/Buzzer/Relay điều khiển bằng 6 nút trên Web.
- ✅ Trạng thái LED đổi chậm nhất 2s kể từ khi dữ liệu gửi thành công lên
  ThingSpeak (đảm bảo bằng HTTP polling mỗi giây, không phụ thuộc riêng MQTT).
