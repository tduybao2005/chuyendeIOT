# Buổi 8 — Mức độ 3 (10 điểm): HTTP Server có Database

FastAPI + **MongoDB Atlas** (database trên cloud) + Raspberry Pi với Grove
Base Hat. Mỗi phía chỉ **một file Python duy nhất**.

---

## 1. Sơ đồ nối dây ⚡

| Linh kiện | Cổng Grove | Chân BCM | Vai trò |
|---|---|---|---|
| Cảm biến **DHT11** | **D5** | GPIO5 | nhiệt độ + độ ẩm |
| **LED đỏ** | **D16** | GPIO16 | báo `NÓNG` — từ 32 °C trở lên |
| **LED vàng** | **D22** | GPIO22 | báo `ẤM` — 28 → 32 °C |
| **LED xanh** | **D24** | GPIO24 | báo `MÁT` — dưới 28 °C |

Đổi chân hoặc đổi ngưỡng thì sửa trực tiếp các hằng số ở đầu
`raspberry/chuong_trinh_pi.py` (`CHAN_...`, `NGUONG_AM`, `NGUONG_NONG`).

---

## 2. Yêu cầu đề — nằm ở đâu trong code

| Yêu cầu của đề | Thực hiện ở đâu |
|---|---|
| API gửi nhiệt độ, độ ẩm, **trạng thái 3 LED** lên Server; dữ liệu **json hoặc form-urlencoded** | `POST /du-lieu` trong `server/server.py` — đọc `Content-Type` để nhận cả hai định dạng trên cùng một route |
| API đọc các giá trị đó từ Server, chọn **N bản gần nhất**, truy xuất theo **khoảng thời gian tuỳ chọn** | `GET /du-lieu?n=..&tu=..&den=..` |
| Hỗ trợ **cả POST và GET** cho API gửi *và* đọc | **POST để gửi, GET để đọc** — mỗi chiều một giao thức, đúng chuẩn HTTP (POST = ghi, GET = đọc) |
| Bản ghi phải có **ID, thời gian gửi, tên thiết bị** | Mỗi bản ghi Mongo có `_id`, `thoi_gian_gui` (server tự gán), `ten_thiet_bi` |
| Bảo mật **API_KEY**, **không lưu API vào Database** | `kiem_tra_api_key()`; mô hình `DuLieuGui` **không có** trường `api_key` nên khoá không có đường nào xuống DB |

---

## 3. Cấu trúc thư mục

```
buoi_8/
├── server/
│   ├── server.py          # ← chạy file này — toàn bộ server, 1 file
│   ├── .env.example       # mẫu cấu hình (copy thành .env)
│   └── requirements.txt
├── raspberry/
│   ├── chuong_trinh_pi.py # ← chạy file này — toàn bộ chương trình Pi, 1 file
│   └── requirements.txt
└── HUONG_DAN_ATLAS.md      # tạo cluster MongoDB Atlas từng bước
```

---

## 4. Chạy — máy tính (Server)

```bash
cd buoi_8
python3 -m venv .venv
.venv/bin/pip install -r server/requirements.txt

cd server
cp .env.example .env
nano .env          # điền MONGODB_URI và API_KEY — xem ../HUONG_DAN_ATLAS.md

../.venv/bin/python server.py
```

Mở <http://localhost:8000/docs> để thấy tài liệu API tự sinh và bấm thử
từng endpoint (nhớ điền `api_key`).

---

## 5. Chạy — Raspberry Pi

```bash
scp raspberry/chuong_trinh_pi.py pi@<ip-cua-pi>:~/iot_buoi8/
ssh pi@<ip-cua-pi>

cd ~/iot_buoi8
pip3 install requests --break-system-packages

export IOT_SERVER="http://192.168.x.x:8000"     # IP máy chạy server
export IOT_API_KEY="khoá giống hệt trong server/.env"

python3 chuong_trinh_pi.py
```

---

## 6. Thử API bằng tay (curl)

```bash
K="api-key-của-bạn"
U="http://localhost:8000/du-lieu"
```

**Gửi — POST + JSON:**
```bash
curl -X POST "$U" -H "X-API-Key: $K" -H 'Content-Type: application/json' \
  -d '{"ten_thiet_bi":"pi4-tdbao","nhiet_do":28.5,"do_am":70,"led1":0,"led2":1,"led3":0}'
```

**Gửi — POST + form-urlencoded:**
```bash
curl -X POST "$U" -H "X-API-Key: $K" \
  -d 'ten_thiet_bi=pi4-tdbao&nhiet_do=33.1&do_am=65&led1=1&led2=0&led3=0'
```

**Đọc — GET, 5 bản gần nhất:**
```bash
curl "$U?n=5" -H "X-API-Key: $K"
```

**Đọc — GET, theo khoảng thời gian (giờ Việt Nam):**
```bash
curl "$U?tu=2026-09-20T10:00:00&den=2026-09-20T11:30:00&n=100" -H "X-API-Key: $K"
```

**Chứng minh API_KEY có tác dụng — phải trả về `401`:**
```bash
curl -i "$U?n=1"          # không gửi khoá
```

**Thử ngay trên trình duyệt** (không đặt được header nên dùng query):
```
http://localhost:8000/du-lieu?n=5&api_key=api-key-của-bạn
```

---

## 7. Thiết kế — vài chỗ đáng chú ý trong báo cáo

**Múi giờ.** Database lưu UTC, nhưng thời gian trả ra và nhận vào đều theo
giờ Việt Nam (+07:00).

**Thời gian do server gán, không lấy của client** — Raspberry Pi không có
pin RTC nên đồng hồ có thể sai sau mất điện.

**Không lưu API_KEY — chặn bằng kiểu dữ liệu.** Mô hình `DuLieuGui` không
có trường `api_key`; client cố nhét khoá vào thân request thì Pydantic bỏ
qua, không có đường nào xuống Database.

**POST để gửi, GET để đọc.** Đây là chiều hỗ trợ "cả 2 giao thức" mà đề bài
yêu cầu — ghi dữ liệu luôn dùng POST (đúng chuẩn HTTP: GET không được có
tác dụng phụ), đọc dữ liệu luôn dùng GET.

---

## 8. Bảo mật khi đẩy lên GitHub

Repo này công khai. `server/.env` (chứa connection string Atlas và
API_KEY) đã bị `.gitignore` chặn — không bao giờ commit file này. Trên Pi,
`IOT_API_KEY` chỉ đặt bằng biến môi trường, không viết vào file `.py`.
