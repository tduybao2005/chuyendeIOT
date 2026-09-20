# Hướng dẫn tạo MongoDB Atlas (cơ sở dữ liệu trên cloud)

Atlas là bản MongoDB chạy sẵn trên cloud. Gói **M0 miễn phí vĩnh viễn**
(512 MB) là quá đủ cho bài này — mỗi bản ghi của ta chỉ khoảng 150 byte, tức
chứa được cỡ **3 triệu bản ghi**. Không cần thẻ tín dụng.

Làm hết khoảng **10 phút**.

---

## Bước 1 — Tạo tài khoản

Vào <https://www.mongodb.com/cloud/atlas/register>, đăng ký bằng Google hoặc
email.

Atlas sẽ hỏi vài câu khảo sát (dùng để làm gì, ngôn ngữ nào...). Trả lời gì
cũng được, nó chỉ để gợi ý ví dụ code.

---

## Bước 2 — Tạo cluster miễn phí

1. Bấm **Create** ở màn hình Overview (hoặc **Build a Database**).
2. Chọn gói **M0 / Free** — cột ngoài cùng bên trái, ghi rõ `$0/month`.

   > ⚠️ Atlas hay để sẵn con trỏ ở gói trả phí (M10). **Nhìn kỹ chọn đúng cột
   > `FREE`** trước khi bấm tiếp.

3. **Provider & Region**: chọn khu vực gần Việt Nam nhất để độ trễ thấp —
   `AWS / Singapore (ap-southeast-1)`.
4. **Name**: đặt gì cũng được, ví dụ `iot-buoi8`.
5. Bấm **Create Deployment**.

Cluster mất **1–3 phút** để khởi tạo.

---

## Bước 3 — Tạo database user

Atlas thường tự mở hộp thoại này ngay sau khi tạo cluster
("Connect to Cluster" → "Create a database user").

> **Đây KHÔNG phải tài khoản Atlas bạn vừa đăng ký.** Nó là một tài khoản
> riêng chỉ để chương trình đăng nhập vào database. Nhầm hai cái này là lỗi
> phổ biến nhất khi kết nối lần đầu.

1. **Username**: `iot_user`
2. **Password**: bấm **Autogenerate Secure Password** rồi **Copy** — lát nữa
   cần dán vào.

   > 💡 Nếu tự đặt mật khẩu thì **chỉ dùng chữ và số**. Ký tự đặc biệt
   > (`@ : / ? # [ ] %`) sẽ làm hỏng chuỗi kết nối vì chúng trùng với ký tự
   > phân cách của URL, và lỗi báo ra rất khó hiểu.
   >
   > Lỡ đặt rồi thì mã hoá URL trước khi dán:
   > ```bash
   > python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" 'mật_khẩu_của_bạn'
   > ```

3. Bấm **Create Database User**.

Nếu không thấy hộp thoại: vào menu trái → **Database Access** → **Add New
Database User**. Quyền để mặc định (`Read and write to any database`).

---

## Bước 4 — Mở Network Access ⚠️ BƯỚC HAY QUÊN NHẤT

Atlas **chặn mọi địa chỉ IP theo mặc định**. Quên bước này thì chương trình
treo rồi báo timeout mà không nói rõ lý do.

1. Menu trái → **Network Access** → **Add IP Address**.
2. Bấm **ALLOW ACCESS FROM ANYWHERE** (Atlas tự điền `0.0.0.0/0`).
3. Bấm **Confirm**.
4. **Chờ trạng thái chuyển từ `Pending` sang `Active`** (~1–2 phút). Chưa
   Active thì vẫn bị chặn.

> **Vì sao chọn "Anywhere" chứ không khai IP của mình?** Mạng nhà và mạng
> trường đều cấp IP động — cắm lại router là IP đổi, và đang demo trước lớp
> mà chết kết nối thì không kịp sửa. Đổi lại, ai có chuỗi kết nối đều vào
> được database, nên **chuỗi đó tuyệt đối không được đẩy lên GitHub** (đã
> có `.gitignore` chặn file `.env`).
>
> Hệ thống chạy thật thì phải khai đúng dải IP của máy chủ.

---

## Bước 5 — Lấy chuỗi kết nối

1. Menu trái → **Database** → bấm **Connect** ở cluster vừa tạo.
2. Chọn **Drivers**.
3. Driver **Python**, version **3.12 or later**.
4. Copy chuỗi ở mục 3, dạng:

   ```
   mongodb+srv://iot_user:<db_password>@iot-buoi8.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=iot-buoi8
   ```

5. **Thay `<db_password>`** bằng mật khẩu thật ở Bước 3 — xoá luôn cả dấu
   `<` và `>`.

---

## Bước 6 — Điền vào file `.env`

```bash
cd buoi_8/server
cp .env.example .env
nano .env
```

Điền hai dòng:

```ini
MONGODB_URI=mongodb+srv://iot_user:matkhauthat@iot-buoi8.xxxxx.mongodb.net/?retryWrites=true&w=majority
API_KEY=<dán khoá sinh ở lệnh dưới>
```

Sinh `API_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

> Khoá này phải **giống hệt** biến `IOT_BUOI8_API_KEY` đặt trên Raspberry Pi.

---

## Bước 7 — Kiểm tra kết nối

```bash
cd buoi_8/server
../.venv/bin/python kiem_tra_atlas.py
```

Chạy đúng thì in:

```
[v] Ket noi Atlas THANH CONG
[v] Tao index thanh cong (quyen ghi OK)
[v] Ghi thu thanh cong, ID = ...
[v] Doc lai thanh cong: 28.5 C, 70.0 %, luc ...
[v] Ban ghi trong Atlas KHONG chua API_KEY (dung yeu cau de bai)
[v] Da xoa ban ghi thu, database sach
```

Script này tự ghi một bản ghi thử, đọc lại, kiểm tra API_KEY không bị lưu,
rồi xoá bản ghi thử đi — database vẫn sạch sau khi chạy.

---

## Ba lỗi hay gặp

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| Treo ~30 giây rồi `ServerSelectionTimeoutError` | Chưa mở Network Access, hoặc trạng thái còn `Pending` | Bước 4, chờ tới `Active` |
| `bad auth : Authentication failed` | Sai user/mật khẩu **database** (hay nhầm với mật khẩu tài khoản Atlas) | Database Access → Edit → Edit Password |
| `InvalidURI` / chuỗi bị cắt giữa chừng | Mật khẩu có ký tự đặc biệt chưa mã hoá URL, hoặc còn nguyên `<db_password>` | Bước 3 — đổi mật khẩu chỉ gồm chữ và số |

Cả ba lỗi này `kiem_tra_atlas.py` đều nhận diện và in sẵn cách sửa.

---

## Xem dữ liệu trên giao diện Atlas

Menu trái → **Database** → **Browse Collections** → database `iot_buoi8` →
collection `du_lieu_cam_bien`.

Chỗ này **chụp màn hình đưa vào báo cáo rất tốt**: nhìn thấy tận mắt mỗi bản
ghi có đủ `_id`, `thoi_gian_gui`, `ten_thiet_bi`, `nhiet_do`, `do_am`,
`led1/2/3` — và **không có trường nào chứa API_KEY**, đúng yêu cầu đề.
