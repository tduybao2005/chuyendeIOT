# Buổi 6 — Lớp thầy Kiên — Mức 15 điểm

Đề bài: [`IOT-Bai-6.pdf`](IOT-Bai-6.pdf) — làm mức **Nâng cao (13 điểm)** cộng
**+2 điểm dùng Docker**.

```
buoi_6/lopthaykien/
├── IOT-Bai-6.pdf              # đề bài
├── README.md                  # file này
├── KIEN_TRUC.md               # sơ đồ kiến trúc + sơ đồ nối dây (Mermaid)
├── luu_do/                    # lưu đồ thuật toán từng chương trình (Mermaid)
├── raspberry/                 # 4 chương trình Python chạy trên Pi
│   ├── cau_hinh.py            #   ← CHỈ SỬA FILE NÀY để điền API key
│   ├── thu_vien_chung.py      #   log, tự phục hồi, gọi ThingSpeak
│   ├── ct2_cam_bien.py        #   CT2 · đọc DHT, gửi trung bình 20s
│   ├── ct3_led.py             #   CT3 · đọc lệnh → 3 LED
│   ├── ct4_relay.py           #   CT4 · relay + hẹn giờ
│   └── ct5_lcd.py             #   CT5 · text 16x2 → LCD
├── node-red/                  # CT1 · giao diện Web
│   ├── dashboard_template.html#   toàn bộ HTML/CSS/JS của dashboard
│   ├── tao_flows.py           #   script sinh flows.json từ file HTML trên
│   ├── flows.json             #   flow hoàn chỉnh, nạp thẳng vào Node-RED
│   └── README.md              #   hướng dẫn nạp flow + điền API key
├── docker/
│   ├── docker-compose.yml     #   Node-RED chạy trong Docker (+2 điểm)
│   └── README.md
└── systemd/                   # 4 unit tự khởi động khi bật nguồn
    ├── iot-ct2-cambien.service
    ├── iot-ct3-led.service
    ├── iot-ct4-relay.service
    └── iot-ct5-lcd.service
```

## Đề yêu cầu gì, đáp ứng ở đâu

### Mức độ 3 (10 điểm)

| Yêu cầu của đề | Đáp ứng ở |
|---|---|
| Viết 03 chương trình, tự khởi động khi bật nguồn | CT1 (Docker) + CT2, CT3 (systemd) |
| Tự reset/khởi động lại khi lỗi cảm biến, rớt mạng | `TheoDoiSucKhoe` trong `thu_vien_chung.py` + `Restart=always` |
| **CT1** Giao diện Web Node-RED trên Raspberry | `node-red/` — chạy trong Docker trên chính Pi |
| **CT1** 6 nút nhấn điều khiển 3 LED | Panel *ĐIỀU KHIỂN LED* — 3 hàng × (Bật / Tắt) |
| **CT1** Hiển thị nhiệt độ, độ ẩm | 2 thẻ số lớn + 2 đồ thị SVG |
| **CT1** Hiển thị trạng thái LED | Đèn báo + nhãn BẬT/TẮT từng LED |
| **CT2** Đọc nhiệt độ, độ ẩm mỗi 1s | `ct2_cam_bien.py`, `CT2_NHIP_DOC = 1` |
| **CT2** Gửi trung bình mỗi 20s | `gui_trung_binh()`, `CT2_NHIP_GUI = 20` |
| **CT3** Đọc nút nhấn từ server, điều khiển LED | `ct3_led.py`, poll channel LỆNH mỗi **0,5s** |
| Có logfile ghi lại hoạt động | `~/iot_buoi6/logs/<tên>.log`, tự xoay vòng 2 MB × 5 |

### Nâng cao (13 điểm)

| Yêu cầu của đề | Đáp ứng ở |
|---|---|
| Web thêm giao diện hẹn giờ bật tắt relay | Panel *RELAY & HẸN GIỜ* — công tắc + 2 ô chọn giờ |
| Web thêm giao diện nhập text tối đa 16×2 ký tự | Panel *TEXT LÊN LCD 16x2* — 2 ô `maxlength=16` + màn hình xem trước |
| **CT4** Điều khiển relay theo giá trị đọc từ server | `ct4_relay.py` — đọc field4 (tay) + field6 (lịch) |
| **CT5** Đọc text 16×2 từ server, hiện lên LCD 16x2 | `ct5_lcd.py` — đọc field5, tự bỏ dấu tiếng Việt |
| Có logfile riêng | `ct4_relay.log`, `ct5_lcd.log` — mỗi chương trình một file |
| Chương trình cũng tự khởi động như các chương trình khác | `iot-ct4-relay.service`, `iot-ct5-lcd.service` |

### +2 điểm Docker

Node-RED chạy trong container `nodered/node-red:4.0`, `restart: unless-stopped`,
`docker.service` đã `enable` nên tự lên khi bật nguồn. Xem [`docker/README.md`](docker/README.md).

## Phần cứng

| Thiết bị | Cổng Grove | GPIO (BCM) |
|---|---|---|
| Cảm biến DHT11/DHT22 (nhiệt độ, độ ẩm) | D22 | 22 |
| LED 1 | D5 | 5 |
| LED 2 | D16 | 16 |
| LED 3 | D18 | 18 |
| Relay | D24 | 24 |
| LCD 16x2 JHD1802 | I2C bất kỳ | — (I2C `0x3E` + `0x62`) |

Sơ đồ nối dây đầy đủ: [`KIEN_TRUC.md`](KIEN_TRUC.md).

## Hai channel ThingSpeak

| Channel | Field | Ai ghi | Ai đọc |
|---|---|---|---|
| **A · CẢM BIẾN** | `field1` Nhiệt độ TB, `field2` Độ ẩm TB | CT2 (mỗi 20s) | Web (mỗi 20s) |
| **B · LỆNH** | `field1-3` LED 1/2/3 | Web | CT3 (mỗi 0,5s) |
| | `field4` Relay | Web | CT4 (mỗi 2s) |
| | `field5` Text `"dòng1\|dòng2"` | Web | CT5 (mỗi 5s) |
| | `field6` Lịch `"1\|18:00\|22:00"` | Web | CT4 (mỗi 2s) |

Cả hai channel, cả hai chiều đọc và ghi, **đều thuần HTTP** — không dùng MQTT ở
bất kỳ đâu. Đề thầy Kiên không yêu cầu MQTT, và MQTT cũng không thoát được giới
hạn ghi của ThingSpeak (giới hạn tính theo channel, không theo giao thức).

**Vì sao phải tách 2 channel?** ThingSpeak gói miễn phí chặn mọi lần ghi cách
lần trước dưới ~15 giây **trên cùng một channel**. CT2 bắt buộc ghi mỗi 20 giây
theo đề — nếu để lệnh nút nhấn chung channel đó thì mỗi chu kỳ chỉ còn vài giây
trống, bấm nút bị từ chối liên tục. Tách ra thì channel LỆNH luôn rảnh.

## Hai ràng buộc vận hành của giao diện

| Ràng buộc | Cách đáp ứng |
|---|---|
| Mỗi lần chỉ bấm được **1 nút**, rồi chờ **15 giây** | Node `ĐIỀU PHỐI GHI` giữ đồng hồ khoá; cả 10 nút bị disable, thanh trên đếm ngược |
| Từ lúc bấm đến lúc Pi xử lý **dưới 2 giây** | POST bắn ngay khi bấm (không qua nhịp tick) + CT3 poll **chu kỳ cố định 0,5s** |

Hai con số này đo hai quãng khác nhau nên không mâu thuẫn. Ngân sách 2 giây:
POST `0,3–0,9s` + chờ vòng poll `≤0,5s` + GET của CT3 `0,3–0,5s` = **xấu nhất
1,9s**. Nếu để CT3 poll 1 giây thì xấu nhất là 2,4s — vỡ mốc.

Đo độ trễ thật (hai mốc cùng đồng hồ Pi, đều có mili giây):

```bash
docker logs -f iot_buoi6_web | grep -E "NHAN LENH TU WEB|GHI THANH CONG"
tail -f ~/iot_buoi6/logs/ct3_led.log | grep "DA AP DUNG XONG"
```

## Giao diện chạy vừa một khung hình trên mọi máy

Bố cục dùng **CSS Grid theo vùng**, tự sắp lại theo cả chiều rộng lẫn chiều cao —
đã đo không tràn, không chồng lấn, không thanh cuộn ở:

| Bố cục | Áp dụng cho | Sắp xếp |
|---|---|---|
| **A** | ≥1200×880 (1920×1080, 1600×950, 1440×900, iPad Pro 12.9 ngang) | 2 cột · phải: LED, Relay, Text |
| **B** | ≥1200 rộng nhưng <880 cao (1366×768, 1536×864, 1280×720) | 3 cột · Text tách sang cột 3 |
| **C** | 900–1199 (iPad ngang 1024×768 → 1194×834) | 2 cột · Text xuống dưới trái |
| **D** | 600–899 (iPad dọc 768×1024 → 834×1194) | Cảm biến + đồ thị full, LED \| Relay, Text full |
| **E** | <600 (điện thoại) | 1 cột, đây là cỡ **duy nhất** cho phép cuộn dọc |

Khoảng cách cũng tự thu gọn ở màn hình thấp (`max-height: 880px` và `760px`),
tiết kiệm ~110px mỗi cột.

## Cài đặt

### 1. Điền API key (2 chỗ, phải khớp nhau)

```bash
nano ~/iot_buoi6/raspberry/cau_hinh.py     # 6 dòng đầu phần THINGSPEAK
```

Bên Node-RED: mở `http://<ip-pi>:1880` → nháy đúp node **`CAU HINH THINGSPEAK`**
→ tab **Setup** → điền → **Deploy**.

### 2. Chạy Web (Docker)

```bash
cd ~/iot_buoi6/docker && docker compose up -d
```

Mở `http://<ip-pi>:1880/ui`.

### 3. Chạy 4 chương trình Python (systemd)

```bash
sudo cp ~/iot_buoi6/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now iot-ct2-cambien iot-ct3-led iot-ct4-relay iot-ct5-lcd
```

## Kiểm tra

| Hạng mục | Lệnh |
|---|---|
| 4 chương trình đang chạy | `systemctl status 'iot-ct*' --no-pager` |
| Tiến trình thật trong task manager | `ps -ef \| grep ct[2345]_` |
| Logfile | `tail -f ~/iot_buoi6/logs/*.log` |
| Log qua journal | `journalctl -u iot-ct3-led -f` |
| Web trong Docker | `docker compose -f ~/iot_buoi6/docker/docker-compose.yml ps` |
| **Tự phục hồi** | `sudo systemctl kill iot-ct3-led` → phải tự lên lại sau ~10s |
| **Tự khởi động** | `sudo reboot` → cả 4 service lẫn container phải tự chạy |
