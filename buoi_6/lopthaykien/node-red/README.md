# CT1 — Giao diện Web bằng Node-RED

Node-RED chạy **trong Docker ngay trên Raspberry Pi**. Giao diện là HTML/CSS/JS
tự viết nhúng qua **đúng một** node `ui_template` — không dùng widget dựng sẵn
của `node-red-dashboard`, để kiểm soát được bố cục "gọn đúng một khung hình".

## Sơ đồ khối của flow

```
0 · CẤU HÌNH
     [CAU HINH THINGSPEAK]        ← điền API key ở tab Setup, không nối dây

1 · ĐỌC CẢM BIẾN (channel A, mỗi 20s)
     [inject 20s] → [dựng URL] → [GET feeds.json] → [phân tích → đồ thị] ─┐
                                                                          ├→ 3 · DASHBOARD
2 · ĐỌC TRẠNG THÁI LỆNH (channel B, mỗi 5s)                               │        │
     [inject 5s]  → [dựng URL] → [GET feeds.json] → [lấy giá trị mới] ────┘        │
                                                                                   │
4 · GHI LỆNH LÊN SERVER (mỗi lần 1 nút, khoá 15 giây)                              │
                                                                                   │
     [inject nhịp 1s] ──'tick'──┐        tick CHỈ để đếm ngược                      │
                                ▼                                                  │
     [ĐIỀU PHỐI GHI] ←──────────┴──'lệnh'──────────────────────────────────────────┘
        │   ▲
        │   └──'kết quả'── [kiểm tra kết quả] ← [POST update.json]
        ├──→ [POST update.json]      bắn NGAY khi nhận 'lệnh', không chờ tick
        └──→ [DASHBOARD]             khoá / mở 10 nút + đếm ngược
```

Dashboard vừa là **nguồn phát** lệnh (`scope.send` khi bấm nút) vừa là **đích
nhận** dữ liệu — nên có dây chạy vòng về. Đó là vòng lặp bình thường của flow,
không phải nối nhầm.

## Cài đặt

Xem [`../docker/README.md`](../docker/README.md) — Node-RED chạy bằng
`docker compose`, không cài trực tiếp lên Pi.

## Nạp flow

`flows.json` đã được chép sẵn vào `~/iot_buoi6/node-red-data/` (thư mục được
mount làm `/data` của container) nên container tự nạp khi khởi động.

Nếu cần nạp lại bằng tay:

```bash
# sao lưu flow đang có
cp ~/iot_buoi6/node-red-data/flows.json ~/iot_buoi6/node-red-data/flows.json.bak.$(date +%s)

cp flows.json ~/iot_buoi6/node-red-data/flows.json
docker restart iot_buoi6_web
```

Hoặc nạp qua editor: mở `http://<ip-pi>:1880/` → menu ☰ → **Import** → dán nội
dung `flows.json` → **Deploy**.

## Điền API key ThingSpeak

Toàn bộ thông tin ThingSpeak nằm ở **một node duy nhất**:

1. Mở editor `http://<ip-pi>:1880/`
2. Nháy đúp node **`CAU HINH THINGSPEAK`** (khung tím, góc trên bên trái)
3. Chuyển sang tab **Setup** (không phải tab *On Message*)
4. Điền 5 giá trị:

   | Trường | Ý nghĩa |
   |---|---|
   | `camBienId` | Channel ID của channel CẢM BIẾN |
   | `camBienReadKey` | Read key — để trống nếu channel đặt Public |
   | `lenhId` | Channel ID của channel LỆNH |
   | `lenhReadKey` | Read key của channel LỆNH |
   | `lenhWriteKey` | **Write key** của channel LỆNH — bắt buộc, Web dùng key này để ghi |

5. **Done** → **Deploy**

Phải khớp với `../raspberry/cau_hinh.py` bên Pi.

> Node này để trống đầu vào là cố ý: toàn bộ mã nằm ở tab **Setup** (On Start),
> Node-RED chạy nó ngay khi flow khởi động — trước mọi message. Nhờ vậy các node
> khác luôn đọc được cấu hình, không bị đua nhau lúc mới deploy.

## Sửa giao diện

**Không sửa thẳng trong `flows.json`** — HTML nằm trong đó dưới dạng chuỗi JSON
đã escape, không đọc nổi. Quy trình:

```bash
nano dashboard_template.html   # sửa cho dễ nhìn
python3 tao_flows.py           # dựng lại flows.json
```

Hoặc sửa trực tiếp trong editor Node-RED rồi chép ngược nội dung node
`ui_template` về `dashboard_template.html`.

## Giao diện đáp ứng yêu cầu nào

| Yêu cầu của đề | Chỗ đáp ứng |
|---|---|
| 6 nút nhấn điều khiển 3 LED | Panel *ĐIỀU KHIỂN LED* — 3 hàng × (Bật / Tắt) |
| Hiển thị giá trị nhiệt độ, độ ẩm | 2 thẻ số lớn + 2 đồ thị SVG bấm xem được từng điểm |
| Hiển thị trạng thái LED | Đèn báo đổi màu + nhãn BẬT/TẮT + viền trái từng hàng |
| Hẹn giờ bật tắt relay *(nâng cao)* | Panel *RELAY & HẸN GIỜ* — công tắc + 2 ô chọn giờ + dòng giải thích khung giờ đang hiệu lực |
| Nhập text tối đa 16×2 ký tự *(nâng cao)* | Panel *TEXT LÊN LCD 16x2* — 2 ô `maxlength=16`, đếm ký tự, màn hình xem trước mô phỏng LCD |

Ô chọn giờ dùng **2 thẻ `<select>`** (giờ / phút) chứ không dùng
`<input type="time">`: AngularJS bắt `input[type=time]` phải nhận một `Date`
object, đưa chuỗi `"18:00"` vào là lỗi `ngModel:datefmt`; mà dùng `Date` thì lại
vướng bẫy múi giờ (Angular đọc giờ theo UTC nên 18:00 hiện thành 01:00).

Thanh dưới cùng hiện trạng thái hàng đợi ghi, đếm ngược tới lần ghi kế tiếp, và
mốc thời gian của 3 lần gọi API gần nhất — để đối chiếu khi quay video minh chứng.

## Quy tắc bấm nút: mỗi lần một nút, khoá 15 giây

Bấm một nút → gửi ngay → **cả 10 thao tác gửi bị khoá 15 giây** → mới bấm được
nút tiếp theo. Đồng hồ khoá nằm ở **Node-RED**, không nằm ở trình duyệt, nên mở
2 tab hay 2 máy cùng lúc thì cả hai đều thấy chung một đồng hồ.

Khoá chỉ chặn việc **gửi**, không chặn việc **gõ**: trong 15 giây chờ vẫn chỉnh
được khung giờ hẹn và gõ được text, đến lúc mở khoá bấm một phát là xong.

**Không cần hàng đợi hay cơ chế thử lại:** channel LỆNH chỉ có Web ghi, mà Web
tự khoá 15 giây, nên không bao giờ chạm giới hạn ~15s/lần ghi của ThingSpeak.
Ghi hỏng thì khoá 5 giây rồi mở lại cho bấm lại — bấm lại ngay lập tức thì cũng
bị ThingSpeak từ chối tiếp.

## Ràng buộc độ trễ dưới 2 giây

POST được bắn **ngay trong message nhận lệnh**, không đi qua nhịp tick — chờ
nhịp 1 giây là mất oan nửa ngân sách. Cộng với CT3 poll chu kỳ cố định 0,5s:

| Chặng | Thời gian |
|---|---|
| Bấm → POST rời Node-RED | ~5 ms |
| POST → ThingSpeak lưu xong | 0,3 – 0,9 s |
| Chờ vòng poll kế tiếp của CT3 | ≤ 0,5 s |
| GET của CT3 đi và về | 0,3 – 0,5 s |
| **Xấu nhất** | **≈ 1,9 s** |

## Vì sao giao diện đổi ngay khi bấm, trước cả khi server nhận

Bấm nút là nút đổi màu **ngay lập tức** (cập nhật lạc quan). Nếu chờ ThingSpeak
xác nhận mới đổi thì người dùng nhìn nút đứng im cả giây — tưởng bấm hỏng.

Cứ mỗi 5 giây, nhánh 2 đọc lại channel LỆNH và đồng bộ giao diện với giá trị
**thật** trên server. Nếu lệnh có rơi mất thì sau tối đa 5 giây nút sẽ tự trả về
đúng trạng thái thật — nhưng **chỉ đồng bộ khi không có lệnh đang bay**, nếu
không nút vừa bấm sẽ bị nhảy ngược về giá trị cũ.
