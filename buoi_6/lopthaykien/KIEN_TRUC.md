# Kiến trúc hệ thống — Buổi 6 lớp thầy Kiên, mức 15 điểm

## 1. Sơ đồ tổng thể

```mermaid
flowchart TB
    subgraph PI["🍓 Raspberry Pi 4 — pi4-hnc"]
        direction TB

        subgraph DOCKER["🐳 Docker · container iot_buoi6_web"]
            CT1["<b>CT1 · Node-RED</b><br/>Giao diện Web :1880/ui<br/>6 nút → 3 LED<br/>relay + hẹn giờ<br/>nhập text 16×2<br/>đồ thị nhiệt độ / độ ẩm"]
        end

        subgraph NATIVE["⚙️ systemd · 4 tiến trình Python riêng biệt"]
            direction TB
            CT2["<b>CT2</b> ct2_cam_bien.py<br/>đọc DHT mỗi 1s<br/>gửi trung bình mỗi 20s"]
            CT3["<b>CT3</b> ct3_led.py<br/>đọc lệnh mỗi 1s<br/>điều khiển 3 LED"]
            CT4["<b>CT4</b> ct4_relay.py<br/>đọc lệnh mỗi 2s<br/>relay + lịch hẹn giờ"]
            CT5["<b>CT5</b> ct5_lcd.py<br/>đọc text mỗi 5s<br/>hiện lên LCD 16×2"]
        end

        subgraph HW["🔌 Phần cứng qua Grove Base Hat"]
            direction LR
            DHT["🌡 DHT<br/>D22"]
            LEDS["💡💡💡 3 LED<br/>D5 · D16 · D18"]
            RELAY["🔌 Relay<br/>D24"]
            LCD["🖵 LCD 16×2<br/>I2C 0x3E"]
        end

        LOG[("📄 Logfile riêng từng chương trình<br/>~/iot_buoi6/logs/*.log<br/>xoay vòng 2 MB × 5")]

        DHT --> CT2
        CT3 --> LEDS
        CT4 --> RELAY
        CT5 --> LCD
        CT2 -.-> LOG
        CT3 -.-> LOG
        CT4 -.-> LOG
        CT5 -.-> LOG
    end

    subgraph TS["☁️ ThingSpeak — 2 channel tách riêng"]
        direction TB
        CA["<b>Channel A · CẢM BIẾN</b><br/>field1 Nhiệt độ TB<br/>field2 Độ ẩm TB"]
        CB["<b>Channel B · LỆNH</b><br/>field1·2·3 LED 1/2/3<br/>field4 Relay<br/>field5 Text 16×2<br/>field6 Lịch hẹn giờ"]
    end

    USER["🖥️ Trình duyệt<br/>laptop · điện thoại · iPad"]

    CT2 -- "POST update.json<br/>mỗi 20s" --> CA
    CA -- "GET feeds.json<br/>mỗi 20s" --> CT1
    CT1 -- "POST update.json<br/>hàng đợi ≥16s/lần" --> CB
    CB -- "GET feeds.json<br/>mỗi 5s (đồng bộ giao diện)" --> CT1
    CB -- "GET · 1s" --> CT3
    CB -- "GET · 2s" --> CT4
    CB -- "GET · 5s" --> CT5

    CT1 <-- "http://ip-pi:1880/ui" --> USER

    classDef pi     fill:#0e1830,stroke:#38bdf8,color:#e9f0fa;
    classDef cloud  fill:#16223a,stroke:#fbbf24,color:#e9f0fa;
    classDef web    fill:#16223a,stroke:#2dd4bf,color:#e9f0fa;
    classDef hw     fill:#0e1830,stroke:#a78bfa,color:#e9f0fa;
    classDef user   fill:#0e1830,stroke:#f87171,color:#e9f0fa;
    class CT2,CT3,CT4,CT5 pi;
    class CA,CB cloud;
    class CT1 web;
    class DHT,LEDS,RELAY,LCD,LOG hw;
    class USER user;
```

## 2. Sơ đồ kết nối phần cứng

Toàn bộ thiết bị cắm qua **Grove Base Hat for Raspberry Pi** — không hàn, không
breadboard, mỗi module một cáp Grove 4 chân vào đúng cổng in sẵn trên hat.

```mermaid
flowchart LR
    subgraph HAT["Grove Base Hat for Raspberry Pi (gắn trên 40 chân GPIO của Pi 4)"]
        direction TB
        D5["Cổng <b>D5</b><br/>GPIO5"]
        D16["Cổng <b>D16</b><br/>GPIO16"]
        D18["Cổng <b>D18</b><br/>GPIO18"]
        D22["Cổng <b>D22</b><br/>GPIO22"]
        D24["Cổng <b>D24</b><br/>GPIO24"]
        I2C["Cổng <b>I2C</b><br/>SDA GPIO2 · SCL GPIO3"]
    end

    D5  --- L1["💡 Grove LED 1"]
    D16 --- L2["💡 Grove LED 2"]
    D18 --- L3["💡 Grove LED 3"]
    D22 --- DHT["🌡 Grove DHT11/DHT22<br/>nhiệt độ + độ ẩm"]
    D24 --- RL["🔌 Grove Relay"]
    I2C --- LCD["🖵 Grove LCD 16×2 JHD1802<br/>0x3E hiển thị · 0x62 đèn nền"]

    classDef cong fill:#1e293b,stroke:#38bdf8,color:#e2e8f0;
    classDef mod  fill:#0f172a,stroke:#a78bfa,color:#e2e8f0;
    class D5,D16,D18,D22,D24,I2C cong;
    class L1,L2,L3,DHT,RL,LCD mod;
```

Mỗi cáp Grove mang 4 dây: `GND`, `VCC (3.3V/5V)`, `SIG`, `NC` — hat đã nối sẵn
nguồn và mass, chương trình chỉ làm việc với chân `SIG`.

| Module | Cổng | Chân BCM | Chương trình dùng | Kiểu |
|---|---|---|---|---|
| DHT11 / DHT22 | D22 | GPIO22 | CT2 | vào — 1 dây, giao thức riêng |
| LED 1 | D5 | GPIO5 | CT3 | ra — mức cao là sáng |
| LED 2 | D16 | GPIO16 | CT3 | ra |
| LED 3 | D18 | GPIO18 | CT3 | ra |
| Relay | D24 | GPIO24 | CT4 | ra — mức cao là đóng tiếp điểm |
| LCD 16×2 JHD1802 | I2C | GPIO2/GPIO3 | CT5 | I2C `0x3E` + `0x62` |

**Ba tiến trình không tranh chấp nhau** vì mỗi tiến trình giữ một nhóm chân
riêng: CT3 giữ GPIO5/16/18, CT4 giữ GPIO24, CT5 giữ bus I2C. CT2 chỉ đọc GPIO22.

## 3. Vòng đời một lệnh — bấm "Bật LED 2"

Quy tắc vận hành: **mỗi lần chỉ bấm được một nút**, bấm xong cả 10 nút bị khoá
15 giây. Nhưng riêng lệnh vừa bấm phải tới được Pi **dưới 2 giây**.

Hai con số này đo hai quãng khác nhau nên không mâu thuẫn:

```
bấm ─┬──────────────── dưới 2 giây ─────────────────┐
     │  POST ~0,5s   ThingSpeak lưu   CT3 poll 0,5s │
     └──────────────────────────────────────────────┘
     └──────────────────── khoá 15 giây ────────────────────┤ mới bấm được nút tiếp
```

```mermaid
sequenceDiagram
    autonumber
    participant U as 🖥️ Người dùng
    participant D as Dashboard<br/>(ui_template)
    participant Q as Node ĐIỀU PHỐI GHI
    participant TS as ☁️ ThingSpeak<br/>channel LỆNH
    participant P as CT3<br/>(poll 0,5s)
    participant G as 💡 LED 2<br/>(GPIO16)

    U->>D: bấm nút "Bật" của LED 2
    D->>D: khoá ngay cả 10 nút<br/>+ đổi màu nút (lạc quan)
    Note over D: khoá tại chỗ, không chờ<br/>Node-RED xác nhận — nếu chờ thì<br/>vài chục ms đó vẫn bấm được nút thứ 2
    D->>Q: topic 'lệnh' + cả 6 field

    Q->>Q: ghi log "NHAN LENH TU WEB lúc HH:MM:SS.mmm"
    Note over Q: POST bắn NGAY trong chính<br/>message này — không qua nhịp tick,<br/>nếu qua thì mất oan tới 1 giây
    Q->>TS: POST update.json (6 field)
    TS-->>Q: entry_id = 142
    Q->>Q: ghi log "GHI THANH CONG lúc HH:MM:SS.mmm"
    Q->>D: khoá 15s, bắt đầu đếm ngược

    P->>TS: GET feeds.json (vòng poll kế tiếp, ≤0,5s sau)
    TS-->>P: field2 = 1
    P->>G: led2.on()
    P->>P: ghi log "DA AP DUNG XONG lúc HH:MM:SS.mmm"

    Note over U,G: Độ trễ thật = mốc CT3 trừ mốc Node-RED<br/>(cùng đồng hồ Pi) — điển hình 1,2–1,6s
```

### Ngân sách 2 giây

| Chặng | Thời gian | Ghi chú |
|---|---|---|
| Bấm → POST rời Node-RED | ~5 ms | bắn thẳng, không qua nhịp tick |
| POST → ThingSpeak lưu xong | 0,3 – 0,9 s | phụ thuộc đường truyền |
| Chờ vòng poll kế tiếp của CT3 | ≤ 0,5 s | = `CT3_NHIP_DOC` |
| GET của CT3 đi và về | 0,3 – 0,5 s | |
| `led.on()` | < 1 ms | |
| **Xấu nhất** | **≈ 1,9 s** | ✅ đạt |

Nếu để `CT3_NHIP_DOC = 1` như ban đầu thì xấu nhất là `0,9 + 1,0 + 0,5 = 2,4s` —
**vỡ mốc**. Đó là lý do nhịp poll của CT3 phải là **0,5 giây**, và phải là
**chu kỳ cố định** (trừ đi thời gian request) chứ không phải `sleep(0.5)` sau mỗi
request — nếu không chu kỳ thật thành `0,5 + 0,4 = 0,9s` và lại vỡ.

### Đo độ trễ thật để quay video

Hai mốc, cùng đồng hồ của Pi (Node-RED chạy trong Docker trên chính Pi, đã đặt
`TZ=Asia/Ho_Chi_Minh`), cả hai đều có mili giây:

```bash
docker logs -f iot_buoi6_web | grep -E "NHAN LENH TU WEB|GHI THANH CONG"
tail -f ~/iot_buoi6/logs/ct3_led.log | grep "DA AP DUNG XONG"
```

Độ trễ = mốc `DA AP DUNG XONG` − mốc `NHAN LENH TU WEB`.

## 4. Máy trạng thái của node ĐIỀU PHỐI GHI

```mermaid
stateDiagram-v2
    [*] --> Mở

    Mở --> ĐangGửi: nhận 'lệnh'<br/>→ POST NGAY LẬP TỨC
    ĐangGửi --> Khoá15s: 'kết quả' ok<br/>entry_id > 0
    ĐangGửi --> Khoá5s: 'kết quả' hỏng<br/>(bị từ chối / rớt mạng)
    Khoá15s --> Mở: hết 15 giây
    Khoá5s --> Mở: hết 5 giây

    Mở --> Mở: 'tick' mỗi 1s<br/>(chỉ cập nhật đếm ngược)
    Khoá15s --> Khoá15s: 'tick'
    ĐangGửi --> ĐangGửi: 'lệnh' khác<br/>→ từ chối, báo "chờ một chút"

    note right of ĐangGửi
        Giao diện đã disable cả 10 nút
        nên nhánh từ chối này chỉ là
        chốt chặn cuối — phòng khi mở
        2 trình duyệt cùng lúc.
    end note

    note right of Khoá5s
        Bấm lại NGAY sau khi bị từ chối
        thì cũng bị từ chối tiếp (vẫn
        trong cửa sổ 15s của ThingSpeak).
        Chờ 5 giây rồi mới mở nút.
    end note
```

**Vì sao không cần hàng đợi:** channel LỆNH chỉ có Web ghi, mà Web tự khoá 15
giây giữa hai lần ghi, nên không bao giờ chạm giới hạn của ThingSpeak → không bị
từ chối → không phải xếp hàng, không phải thử lại.

Đồng hồ khoá nằm ở **Node-RED**, không nằm ở trình duyệt — mở 2 tab hay 2 máy
cùng lúc thì cả hai đều thấy chung một đồng hồ, không ai lách được.

## 5. Cơ chế tự phục hồi

Đề bắt buộc *"chương trình phải tự reset/khởi động lại khi có lỗi phát sinh"*.
Hai tầng:

```mermaid
flowchart TB
    A["Một vòng lặp của CT2/3/4/5"] --> B{"Thao tác<br/>thành công?"}
    B -- "có" --> C["Đưa bộ đếm lỗi về 0<br/>(cam_bien_ok / mang_ok)"]
    C --> A
    B -- "không" --> D["try/except nuốt lỗi<br/>ghi log, tăng bộ đếm"]
    D --> E{"Đã đủ<br/>ngưỡng<br/>liên tiếp?"}
    E -- "chưa" --> A
    E -- "rồi" --> F["Tắt LED / ngắt relay<br/>ghi log lý do"]
    F --> G["os._exit(1)"]
    G --> H["systemd thấy tiến trình chết<br/>Restart=always<br/>RestartSec=10"]
    H --> I["Dựng lại tiến trình sạch<br/>sau 10 giây"]
    I --> A

    classDef ok   fill:#064e3b,stroke:#34d399,color:#e9f0fa;
    classDef bad  fill:#4c1d24,stroke:#f87171,color:#e9f0fa;
    classDef sys  fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    class C ok;
    class D,E,F,G bad;
    class H,I sys;
```

| Bộ đếm | Tăng khi | Ngưỡng | Chương trình dùng |
|---|---|---|---|
| `loi_cam_bien` | DHT không ra giá trị hợp lệ / ghi LCD hỏng | 30 lần liên tiếp | CT2, CT5 |
| `loi_mang` | Gọi ThingSpeak thất bại | 20 lần liên tiếp | CT2, CT3, CT4, CT5 |

**Mỗi lần thành công đều đưa bộ đếm về 0**, nên lỗi lẻ tẻ ngắt quãng không bao
giờ cộng dồn tới ngưỡng — chỉ lỗi *liên tiếp* mới khiến chương trình khởi động
lại. Đúng tinh thần đề: lỗi vặt thì `try/except` chạy tiếp, lỗi thật thì reset.

Hai chi tiết dễ sai:

- Dùng `os._exit(1)` chứ không phải `sys.exit()`. `sys.exit()` chỉ ném
  `SystemExit`; nếu hàm thoát được gọi từ một luồng phụ thì chỉ luồng đó chết,
  tiến trình vẫn sống trong trạng thái què quặt.
- `os._exit()` **bỏ qua khối `finally`**, nên phải tự tắt LED / ngắt relay
  *trước* khi gọi — GPIO không tự về mức thấp khi tiến trình chết.

## 6. Tự khởi động khi bật nguồn

```mermaid
flowchart LR
    A["⚡ Cấp nguồn Pi"] --> B["systemd khởi động"]
    B --> C["network-online.target<br/>(chờ Wi-Fi thật sự lên)"]
    C --> D1["iot-ct2-cambien.service"]
    C --> D2["iot-ct3-led.service"]
    C --> D3["iot-ct4-relay.service"]
    C --> D4["iot-ct5-lcd.service"]
    B --> E["docker.service<br/>(đã enable)"]
    E --> F["container iot_buoi6_web<br/>restart: unless-stopped"]
    F --> G["Node-RED :1880/ui"]

    classDef sys fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    classDef app fill:#0e1830,stroke:#34d399,color:#e9f0fa;
    class A,B,C,E sys;
    class D1,D2,D3,D4,F,G app;
```

Các unit khai báo `Wants=network-online.target` + `After=network-online.target`.
Lúc mới cấp nguồn, Wi-Fi lên **chậm hơn** systemd — không chờ thì lần chạy đầu
sẽ rớt mạng ngay, đốt bộ đếm lỗi vô cớ rồi restart liên tục vài vòng.

`StartLimitIntervalSec=0` để systemd **không bao giờ bỏ cuộc**: mặc định nó
ngừng thử sau 5 lần restart trong 10 giây, mất mạng cả tiếng là service chết
hẳn — trong khi đề đòi thiết bị phải tự sống lại.
