# Buổi 9 — Mức độ 3 (10 điểm): MQTT Broker có Database

EMQX (MQTT broker, ma nguon mo) + Python server (paho-mqtt + MongoDB Atlas) +
Raspberry Pi với Grove Base Hat. Mỗi phía chỉ **một file Python duy nhất**.

---

## 1. Sơ đồ nối dây ⚡ (giống buổi 8)

| Linh kiện | Cổng Grove | Chân BCM | Vai trò |
|---|---|---|---|
| Cảm biến **DHT11** | **D5** | GPIO5 | nhiệt độ + độ ẩm |
| **LED đỏ** | **D16** | GPIO16 | bước 0 của vòng đuổi |
| **LED vàng** | **D22** | GPIO22 | bước 1 |
| **LED xanh** | **D24** | GPIO24 | bước 2 |

---

## 2. Yêu cầu đề — nằm ở đâu trong code

8 topic = `{gui, doc} × {tung, toanbo} × {json, form}`:

| Topic | Vai trò |
|---|---|
| `buoi9/gui/tung/json`, `buoi9/gui/tung/form` | Pi **gửi từng** giá trị (nhiệt độ / độ ẩm / 1 LED) lên server |
| `buoi9/gui/toanbo/json`, `buoi9/gui/toanbo/form` | Pi **gửi toàn bộ** (nhiệt độ + độ ẩm + cả 3 LED) lên server |
| `buoi9/doc/tung/json`, `buoi9/doc/tung/form` | server phát lại từng giá trị mới nhất — subscribe để **đọc từng** |
| `buoi9/doc/toanbo/json`, `buoi9/doc/toanbo/form` | server phát lại toàn bộ trạng thái mới nhất — subscribe để **đọc toàn bộ** |

| Yêu cầu của đề | Thực hiện ở đâu |
|---|---|
| Topic gửi/đọc từng dữ liệu, gửi/đọc toàn bộ dữ liệu | `server/server.py` — `xu_ly_tung()` / `xu_ly_toanbo()` |
| Hỗ trợ json và form-urlencoded, mỗi loại 2 topic riêng | Hậu tố `/json` và `/form` trên mọi topic; `ma_hoa()`/`giai_ma()` |
| Bản ghi phải có ID, thời gian, tên thiết bị | Mỗi tin nhắn nhận được → `luu_db()` ghi vào Mongo với `_id` (tự sinh), `thoi_gian_gui` (server tự gán), `ten_thiet_bi` |
| **Lưu ý bắt buộc 1:** gửi TỪNG cũng phải kích hoạt topic đọc TOÀN BỘ | `xu_ly_tung()` sau khi lưu DB thì publish (retain) cả lên `doc/toanbo/*` với state đầy đủ |
| **Lưu ý bắt buộc 2:** gửi TOÀN BỘ cũng phải kích hoạt topic đọc TỪNG | `xu_ly_toanbo()` sau khi lưu DB thì publish (retain) từng field lên `doc/tung/*` |
| **Lưu ý bắt buộc 3:** gửi bằng topic json thì subscribe bằng topic form (và ngược lại) vẫn thấy | Mọi lần publish lên topic "đọc" đều publish **cả 2 định dạng** (`doc/.../json` và `doc/.../form`) cùng lúc, không phụ thuộc định dạng gốc nhận vào |

**Vì sao dùng `retain=True`:** MQTT có sẵn cơ chế "retained message" — client mới subscribe vào là nhận ngay giá trị cuối cùng đã publish, không cần đợi tin nhắn mới. Đây chính là ý nghĩa "đọc dữ liệu mới nhất từ Server" mà đề yêu cầu, không cần giả lập kiểu HTTP GET.

---

## 3. Cấu trúc thư mục

```
buoi_9/
├── server/
│   ├── server.py          # ← chạy file này — toàn bộ server, 1 file
│   ├── .env.example       # mẫu cấu hình (copy thành .env)
│   └── requirements.txt
├── raspberry/
│   ├── chuong_trinh_pi.py # ← chạy file này — toàn bộ chương trình Pi, 1 file
│   └── requirements.txt
└── README.md
```

---

## 4. Cài EMQX (MQTT broker) — làm 1 lần trên máy chạy server

Dùng bản **mã nguồn mở** (repo `emqx/emqx`, không phải `emqx-enterprise5`):

```bash
curl -s https://packagecloud.io/install/repositories/emqx/emqx/script.deb.sh | sudo bash
sudo apt-get install -y emqx
sudo systemctl enable --now emqx
```

Mặc định EMQX đã lắng nghe `0.0.0.0:1883` (mọi thiết bị trong LAN kết nối
được) và cho phép kết nối ẩn danh (không cần username/password) — không
cần sửa file cấu hình nào thêm, đúng phạm vi đề bài (không yêu cầu bảo
mật MQTT ở mức độ 3).

Cài `mosquitto-clients` để có 2 lệnh `mosquitto_pub`/`mosquitto_sub` dùng
thử tay (bản thân 2 lệnh này chỉ là client, dùng được với bất kỳ broker
nào kể cả EMQX):
```bash
sudo apt-get install -y mosquitto-clients
```

Kiểm tra broker sống:
```bash
mosquitto_sub -h localhost -t 'test' &
mosquitto_pub -h localhost -t 'test' -m 'hello'
# thay dong "hello" hien ra la broker chay dung
```

Dashboard web (theo dõi client/topic trực quan, chụp ảnh báo cáo tốt):
`http://<ip-may-chay-server>:18083` — đăng nhập `admin` / `public` (bắt
buộc đổi mật khẩu ngay lần đăng nhập đầu, không ảnh hưởng gì tới hoạt
động MQTT).

---

## 5. Chạy — máy tính (Server)

```bash
cd buoi_9
python3 -m venv .venv
.venv/bin/pip install -r server/requirements.txt

cd server
cp .env.example .env
nano .env          # dien MONGODB_URI (dung lai cua buoi_8 cung duoc, doi
                    # MONGODB_DB/MONGODB_COLLECTION de khong lan du lieu)

../.venv/bin/python server.py
```

---

## 6. Chạy — Raspberry Pi

```bash
scp raspberry/chuong_trinh_pi.py pi@<ip-cua-pi>:~/iot_buoi9/
ssh pi@<ip-cua-pi>

cd ~/iot_buoi9
pip3 install paho-mqtt --break-system-packages

export IOT_MQTT_HOST="192.168.x.x"     # IP may chay EMQX/server
python3 chuong_trinh_pi.py
```

---

## 7. Thử bằng tay (mosquitto_pub / mosquitto_sub)

Mở 1 cửa sổ terminal subscribe xem dữ liệu đọc về (cả 4 topic):
```bash
mosquitto_sub -h localhost -t 'buoi9/doc/#' -v
```

Cửa sổ khác, gửi thử — **gửi từng** (định dạng json):
```bash
mosquitto_pub -h localhost -t 'buoi9/gui/tung/json' \
  -m '{"ten_thiet_bi":"test","ten_truong":"nhiet_do","gia_tri":29.5}'
```

**Gửi toàn bộ** (định dạng form-urlencoded):
```bash
mosquitto_pub -h localhost -t 'buoi9/gui/toanbo/form' \
  -m 'ten_thiet_bi=test&nhiet_do=30&do_am=65&led1=1&led2=0&led3=0'
```

Cửa sổ subscribe ở trên phải thấy dữ liệu xuất hiện trên **cả 4** topic
`doc/tung/json`, `doc/tung/form`, `doc/toanbo/json`, `doc/toanbo/form` sau
mỗi lần gửi — đúng "Lưu ý bắt buộc" của đề.

---

## 8. Thiết kế — vài chỗ đáng chú ý trong báo cáo

**Vì sao không cần "API_KEY" như buổi 8?** Đề mức độ 3 của buổi 9 (MQTT)
không nhắc tới bảo mật API_KEY như buổi 8 (HTTP) — EMQX ở đây chạy
`allow_anonymous true` cho đơn giản, đúng phạm vi đề yêu cầu.

**Thời gian do server gán, không lấy của client** — giống lý do ở buổi 8:
Raspberry Pi không có pin RTC.

**Trạng thái "toàn bộ" giữa trong bộ nhớ (`trang_thai_hien_tai`)** — khi
nhận một tin "gửi từng", server cần biết 4 giá trị còn lại (đã nhận từ
trước) để ghép thành "toàn bộ" đầy đủ publish lên `doc/toanbo/*`. Giữ
trong RAM theo `ten_thiet_bi`, không cần hỏi lại Database mỗi lần.

---

## 9. Bảo mật khi đẩy lên GitHub

`server/.env` (chứa connection string Atlas) đã bị `.gitignore` chặn —
không bao giờ commit file này.
