# Buổi 8 — Mức độ 3 (10 điểm): HTTP Server có Database

FastAPI + **MongoDB Atlas** (database trên cloud) + Raspberry Pi với Grove
Base Hat.

---

## 1. Sơ đồ nối dây ⚡

| Linh kiện | Cổng Grove | Chân BCM | Vai trò |
|---|---|---|---|
| Cảm biến **DHT11** | **D5** | GPIO5 | nhiệt độ + độ ẩm |
| **LED đỏ** | **D16** | GPIO16 | báo `NÓNG` — từ 32 °C trở lên |
| **LED vàng** | **D22** | GPIO22 | báo `ẤM` — 28 → 32 °C |
| **LED xanh** | **D24** | GPIO24 | báo `MÁT` — dưới 28 °C |

```
        Raspberry Pi 4 + Grove Base Hat
        ┌──────────────────────────────────┐
        │  D5   ──────  DHT11              │  nhiệt độ, độ ẩm
        │  D16  ──────  LED đỏ    ●        │  >= 32 °C
        │  D22  ──────  LED vàng  ●        │  28 – 32 °C
        │  D24  ──────  LED xanh  ●        │  < 28 °C
        └──────────────────────────────────┘
```

Bộ chân này **lấy theo `buoi_7/slave/chuong_trinh_slave_pi.py`** — đã chạy
thực tế trên Pi `pi4-tdbao` ngày 2026-09-14, không phải suy ra từ sơ đồ.

> ⚠️ **Nếu cắm trên con Pi khác:** `buoi_6/lopthaykien` (chạy trên `pi4-hnc`)
> dùng bộ chân **hoàn toàn khác** — DHT ở D22, LED ở D5/D16/D18. Cắm theo sơ
> đồ buổi 6 rồi chạy code này thì cảm biến và đèn đều không hoạt động mà
> **không báo lỗi rõ ràng**. Kiểm tra kỹ trước khi chạy.
>
> Đổi chân thì chỉ sửa `raspberry/cau_hinh_pi.py`, không đụng file nào khác.

---

## 2. Yêu cầu đề — nằm ở đâu trong code

> **Bài tập mức độ 3 (10 điểm):** Xây dựng HTTP server có Database, thực hiện
> các chức năng sau:

| Yêu cầu của đề | Thực hiện ở đâu |
|---|---|
| API gửi nhiệt độ, độ ẩm, **trạng thái 3 LED** lên Server; dữ liệu **json hoặc form-urlencoded** | `POST /api/v1/du-lieu` — `server/dau_vao.py` nhận cả hai định dạng trên **cùng một** route |
| API đọc các giá trị đó từ Server, chọn **N bản gần nhất**, truy xuất theo **khoảng thời gian tuỳ chọn** | `GET /api/v1/du-lieu?n=..&tu=..&den=..` |
| Hỗ trợ **cả POST và GET** cho API gửi *và* đọc | Gửi: `POST /du-lieu` + `GET /du-lieu/gui`<br>Đọc: `GET /du-lieu` + `POST /du-lieu/doc` |
| Bản ghi phải có **ID, thời gian gửi, tên thiết bị** | `server/mo_hinh.py` → lớp `BanGhi` |
| Bảo mật **API_KEY**, **không lưu API vào Database** | `server/bao_mat.py`; và mô hình `DuLieuGui` **không có** trường `api_key` nên khoá không có đường nào xuống DB |

---

## 3. Cấu trúc thư mục

```
buoi_8/
├── server/                    # chạy trên MÁY TÍNH
│   ├── main.py                # FastAPI: toàn bộ route
│   ├── mo_hinh.py             # validate dữ liệu vào/ra (Pydantic)
│   ├── kho_du_lieu.py         # tầng truy cập MongoDB
│   ├── bao_mat.py             # kiểm tra API_KEY
│   ├── dau_vao.py             # đọc json HOẶC form-urlencoded
│   ├── cau_hinh.py            # đọc .env
│   ├── chay_server.py         # ← chạy file này
│   ├── kiem_tra_atlas.py      # kiểm tra kết nối Atlas trước khi chạy
│   ├── .env.example           # mẫu cấu hình (copy thành .env)
│   └── tests/                 # 95 test, chạy offline
├── raspberry/                 # chạy trên RASPBERRY PI
│   ├── chuong_trinh_pi.py     # ← chạy file này
│   ├── cau_hinh_pi.py         # sơ đồ chân + địa chỉ server
│   ├── logic_led.py           # luật bật đèn theo nhiệt độ
│   ├── giao_tiep.py           # đóng gói / hiển thị / phân loại lỗi
│   └── tests/                 # 46 test
├── HUONG_DAN_ATLAS.md         # tạo cluster MongoDB Atlas từng bước
└── pytest.ini
```

---

## 4. Chạy — máy tính (Server)

```bash
cd buoi_8

# 1. Cài thư viện
python3 -m venv .venv
.venv/bin/pip install -r server/requirements.txt

#    Muốn chạy thử chương trình Pi ở chế độ giả lập ngay trên máy tính
#    (mục 5) thì cài thêm:
.venv/bin/pip install requests

# 2. Cấu hình
cd server
cp .env.example .env
nano .env          # điền MONGODB_URI và API_KEY — xem HUONG_DAN_ATLAS.md

# 3. Kiểm tra Atlas trước (khuyến nghị, tránh mò lỗi lúc demo)
../.venv/bin/python kiem_tra_atlas.py

# 4. Chạy server
../.venv/bin/python chay_server.py
```

Server in sẵn dòng `export IOT_BUOI8_SERVER=...` — copy nguyên dòng đó sang Pi.

Mở <http://localhost:8000/docs> để thấy **tài liệu API tự sinh**, bấm thử được
từng endpoint ngay trên trình duyệt (nhớ điền `api_key`). Trang này **chụp màn
hình đưa vào báo cáo rất tốt**.

---

## 5. Chạy — Raspberry Pi

```bash
# Chép 4 file lên Pi
scp raspberry/*.py pi@<ip-cua-pi>:~/iot_buoi8/

# Trên Pi:
cd ~/iot_buoi8
pip3 install requests --break-system-packages

export IOT_BUOI8_API_KEY="khoá giống hệt trong server/.env"
export IOT_BUOI8_SERVER="http://192.168.x.x:8000"    # dòng server in ra

python3 chuong_trinh_pi.py
```

Kết quả trên terminal:

```
[   1] MAT  | [2026-09-20 20:58:44] pi4-tdbao    nhiet do  26.5 C | do am  57.4 % | LED(do,vang,xanh) 001 | ID 6aafe694af2f00c232265ad7
[   2] NONG | [2026-09-20 20:58:49] pi4-tdbao    nhiet do  32.0 C | do am  57.5 % | LED(do,vang,xanh) 100 | ID 6aafe699af2f00c232265ad8
  --- 5 ban ghi gan nhat doc tu server bang GET:
    [2026-09-20 20:59:09] pi4-tdbao    nhiet do  29.8 C | do am  60.2 % | LED(do,vang,xanh) 010 | ID ...
```

> **Mỗi dòng trên là dữ liệu ĐỌC VỀ TỪ SERVER, không phải biến cục bộ.** Pi
> gửi lên xong thì gọi API đọc để lấy lại rồi mới in. Làm vòng như vậy chứng
> minh cả đường đi lẫn đường về đều sống:
> `Pi → HTTP → FastAPI → MongoDB Atlas → FastAPI → HTTP → Pi`.
> In biến cục bộ thì màn hình vẫn đẹp y hệt kể cả khi Atlas đang chết.

### Chứng minh đủ 4 đường API (dùng khi quay video / demo)

```bash
python3 chuong_trinh_pi.py --kieu-gui json --kieu-doc get     # mặc định
python3 chuong_trinh_pi.py --kieu-gui form --kieu-doc post
python3 chuong_trinh_pi.py --kieu-gui get                     # gửi bằng GET
```

### Chưa có Pi / chưa cắm cảm biến

```bash
python3 chuong_trinh_pi.py --gia-lap
```

Sinh số ngẫu nhiên trong vùng 26–34 °C (đi qua cả hai ngưỡng 28 và 32 nên
thấy được cả ba màu đèn đổi), **không đụng GPIO** — chạy được ngay trên máy
tính.

---

## 6. Thử API bằng tay (curl)

Đặt biến cho gọn:

```bash
K="api-key-của-bạn"
U="http://localhost:8000/api/v1/du-lieu"
```

**Gửi — POST + JSON:**
```bash
curl -X POST "$U" -H "X-API-Key: $K" -H 'Content-Type: application/json' \
  -d '{"ten_thiet_bi":"pi4-tdbao","nhiet_do":28.5,"do_am":70,"led1":0,"led2":1,"led3":0}'
```

**Gửi — POST + form-urlencoded:**
```bash
curl -X POST "$U" -H "X-API-Key: $K" \
  -d 'ten_thiet_bi=pi4-tdbao&nhiet_do=33.1&do_am=65&led1=on&led2=off&led3=off'
```

**Gửi — GET:**
```bash
curl "$U/gui?ten_thiet_bi=pi4-tdbao&nhiet_do=25&do_am=55&led1=0&led2=0&led3=1" \
  -H "X-API-Key: $K"
```

**Đọc — GET, 5 bản gần nhất:**
```bash
curl "$U?n=5" -H "X-API-Key: $K"
```

**Đọc — GET, theo khoảng thời gian (giờ Việt Nam):**
```bash
curl "$U?tu=2026-09-20T10:00:00&den=2026-09-20T11:30:00&n=100" -H "X-API-Key: $K"
```

**Đọc — POST:**
```bash
curl -X POST "$U/doc" -H "X-API-Key: $K" -H 'Content-Type: application/json' -d '{"n":5}'
```

**Bản ghi cuối cùng:**
```bash
curl "$U/moi-nhat" -H "X-API-Key: $K"
```

**Chứng minh API_KEY có tác dụng — phải trả về `401`:**
```bash
curl -i "$U?n=1"          # không gửi khoá
```

**Thử ngay trên trình duyệt** (không đặt được header nên dùng query):
```
http://localhost:8000/api/v1/du-lieu?n=5&api_key=api-key-của-bạn
```

---

## 7. Chạy test

```bash
cd buoi_8
env -u PYTHONPATH .venv/bin/python -m pytest
```

**141 test, chạy hoàn toàn offline** — không cần Atlas, không cần Pi, không
cần mạng. Bộ test dùng một kho dữ liệu giả trong bộ nhớ
(`server/tests/kho_gia.py`) thay cho MongoDB.

> 💡 `env -u PYTHONPATH` là để gỡ biến `PYTHONPATH` của ROS trên máy này —
> nó nạp plugin `launch_testing` vào pytest và làm pytest lỗi ngay khi khởi
> động. Máy không cài ROS thì chạy `pytest` bình thường.

Test **không** chứng minh được Atlas đã cấu hình đúng (vì nó chạy offline) —
phần đó dùng `kiem_tra_atlas.py`, script này ghi thật một bản ghi, đọc lại,
kiểm tra API_KEY không bị lưu, rồi xoá đi.

---

## 8. Thiết kế — vài chỗ đáng chú ý trong báo cáo

**Múi giờ.** Database lưu UTC (chuẩn, không phụ thuộc máy chủ đặt ở đâu),
nhưng thời gian **trả ra và nhận vào đều theo giờ Việt Nam (+07:00)**. Gõ
`?tu=2026-09-20T10:00:00` là 10 giờ sáng theo đồng hồ trên tường. Nếu hiểu
chuỗi đó là UTC thì truy vấn lệch đúng 7 tiếng và **trả về rỗng mà không báo
lỗi gì** — loại lỗi im lặng, rất khó tìm.

**Thời gian do server gán, không lấy của client.** Raspberry Pi không có pin
RTC; mất điện bật lên mà chưa kịp đồng bộ NTP thì đồng hồ báo năm 1970. Tin
giờ của Pi thì thứ tự bản ghi loạn và đồ thị vô nghĩa.

**Không lưu API_KEY — chặn bằng kiểu dữ liệu, không bằng trí nhớ.** Mô hình
`DuLieuGui` đơn giản là **không có trường `api_key`**. Client có cố nhét khoá
vào thân request thì Pydantic cũng bỏ qua, nó không có đường nào đi xuống
Database. Chặn kiểu này chắc hơn "nhớ xoá trong route" — thêm một route là
quên.

**Phân biệt lỗi cấu hình và lỗi tạm thời.** Sai API_KEY (401) thì thử lại 100
lần vẫn sai → Pi **báo ngay và thoát mã 2**. Mất mạng / server đang khởi động
lại (5xx) thì tự hết → **thử lại**, quá 15 lần liên tiếp mới thoát mã 1 cho
systemd dựng lại. Gộp chung một loại thì sai khoá cũng phải ngồi chờ 75 giây
mới biết, trong khi lý do thật đã rõ ngay từ lần đầu.

**`GET` để ghi dữ liệu là sai chuẩn HTTP** (GET phải là thao tác chỉ đọc —
trình duyệt có thể tự gọi lại khi bấm F5, và proxy được phép cache). Vẫn làm
vì đề yêu cầu rõ, và nó tiện thật khi demo: dán một đường link vào trình
duyệt là gửi được dữ liệu. Chương trình Pi thì luôn dùng POST.

---

## 9. Bảo mật khi đẩy lên GitHub

Repo này công khai. Hai thứ **không bao giờ** được commit:

- `server/.env` — chứa connection string Atlas (có sẵn mật khẩu bên trong) và
  API_KEY. Đã bị `.gitignore` chặn.
- `IOT_BUOI8_API_KEY` trên Pi — đặt bằng biến môi trường, không viết vào file
  `.py`.

`server/.env.example` thì **được** commit — nó chỉ chứa chỗ trống.

> Bot quét connection string trên GitHub là chuyện có thật và rất nhanh;
> Atlas còn tự gửi cảnh báo khi phát hiện khoá bị lộ công khai.

---

## 10. Trạng thái

| Hạng mục | Tình trạng |
|---|---|
| Server FastAPI — 6 endpoint | ✅ đã chạy thật, kiểm tra bằng curl |
| Nhận json + form-urlencoded | ✅ |
| POST/GET cho cả gửi và đọc | ✅ đã xác nhận GET và POST trả kết quả giống hệt nhau |
| API_KEY (header + query), không lưu vào DB | ✅ |
| Đọc N bản gần nhất + lọc khoảng thời gian | ✅ |
| Chương trình Pi (chế độ giả lập) | ✅ đã chạy thật với server |
| 141 test | ✅ pass, không warning |
| **Kết nối MongoDB Atlas thật** | ⏳ **chưa** — cần `MONGODB_URI`, chạy `kiem_tra_atlas.py` |
| **Cảm biến DHT11 + 3 LED thật trên Pi** | ⏳ **chưa** — Pi chưa cắm nguồn |

Hai mục cuối cần phần cứng và tài khoản Atlas nên chưa kiểm chứng được.
