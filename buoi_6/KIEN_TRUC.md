# Kiến trúc hệ thống — Buổi 6

Sơ đồ dưới đây phản ánh đúng những gì đang chạy thật trên `pi4-tdbao`
(`chuong_trinh_pi.py` qua systemd `iot-buoi6`) và Node-RED (chạy được cả
trên Pi lẫn trên máy khác, cùng đọc/ghi 2 channel ThingSpeak thật).

```mermaid
flowchart TB
    subgraph PI["🍓 Raspberry Pi — chuong_trinh_pi.py (systemd: iot-buoi6)"]
        direction TB
        SENS["Cảm biến (đọc mỗi 1s)<br/>DHT nhiệt độ/độ ẩm — D5<br/>Siêu âm khoảng cách — D16<br/>Biến trở điện áp — ADC I2C 0x08"]
        LCD["LCD 16x2 (I2C 0x3E)<br/>Time HH:MM:SS<br/>MODE L B R"]
        MAIN["Luồng CHÍNH<br/>gom trung bình 20s<br/>apply_outputs() Auto/Manual"]
        POLL["Luồng ĐỌC LỆNH<br/>chu kỳ cố định 1s<br/>control_poll_loop()"]
        OUT["Thiết bị điều khiển<br/>💡 LED — D18<br/>🔊 Buzzer — D24<br/>🔌 Relay — D26"]
        RECOVER["Tự phục hồi<br/>sensor_fail ≥30 lần liên tiếp<br/>network_fail ≥20 lần liên tiếp<br/>→ os._exit(1)"]

        SENS --> MAIN
        MAIN --> LCD
        MAIN --> OUT
        POLL --> MAIN
        MAIN -. lỗi liên tiếp .-> RECOVER
        POLL -. lỗi liên tiếp .-> RECOVER
    end

    subgraph TS["☁️ ThingSpeak — 2 channel tách riêng"]
        direction TB
        C1["📡 Channel CẢM BIẾN<br/>field1 Temperature<br/>field2 Humidity<br/>field3 Voltage<br/>field4 Distance"]
        C2["🎛️ Channel LỆNH<br/>field1 LED · field2 Relay<br/>field3 Buzzer · field4 Mode"]
    end

    subgraph NR["🟥 Node-RED (chạy trên Pi và/hoặc laptop)"]
        direction TB
        R1["GET feeds.json<br/>mỗi 15s"]
        R2["GET feeds.json<br/>mỗi 5s"]
        SW{{"switch<br/>2 nhánh giao thức"}}
        MQ["prep + mqtt out<br/>2 nút: Auto/Manual"]
        HT["prep + POST update.json<br/>6 nút: LED/Relay/Buzzer<br/>tự thử lại 10 lần × 3s"]
        DASH["ui_template<br/>Dashboard 1 khung hình"]

        R1 --> DASH
        R2 --> DASH
        DASH -- "bấm nút<br/>scope.send()" --> SW
        SW -- "auto / manual" --> MQ
        SW -- "6 nút thiết bị" --> HT
        HT -. "cmd_ok / cmd_failed" .-> DASH
    end

    BROWSER["🖥️ Trình duyệt (Web)<br/>iPad / laptop / điện thoại"]

    MAIN -- "HTTP POST<br/>trung bình mỗi 20s" --> C1
    POLL -- "HTTP GET<br/>poll mỗi 1s" --> C2

    C1 -- "HTTP GET mỗi 15s" --> R1
    C2 -- "HTTP GET mỗi 5s" --> R2
    MQ -- "MQTT publish<br/>(retain)" --> C2
    HT -- "HTTP POST<br/>update.json" --> C2

    DASH <-- "giao diện web<br/>:1880/ui" --> BROWSER

    classDef pi fill:#0e1830,stroke:#38bdf8,color:#e9f0fa;
    classDef cloud fill:#16223a,stroke:#fbbf24,color:#e9f0fa;
    classDef web fill:#16223a,stroke:#2dd4bf,color:#e9f0fa;
    classDef user fill:#0e1830,stroke:#f87171,color:#e9f0fa;
    class SENS,LCD,MAIN,POLL,OUT,RECOVER pi;
    class C1,C2 cloud;
    class R1,R2,SW,MQ,HT,DASH web;
    class BROWSER user;
```

## Vì sao tách 2 channel

ThingSpeak (gói miễn phí) chỉ cho ghi **1 lần / ~15-17 giây trên cùng một
channel**. Pi phải gửi trung bình cảm biến **mỗi 20 giây** — nếu dùng chung
1 channel với lệnh điều khiển thì mỗi chu kỳ chỉ còn vài giây trống cho nút
bấm, lệnh HTTP từ Web bị từ chối liên tục. Tách riêng thì channel LỆNH luôn
rảnh cho nút bấm, không tranh chấp với việc Pi ghi cảm biến.

## Vì sao Pi không subscribe MQTT

ThingSpeak chỉ cấp **một** bộ danh tính MQTT cho mỗi channel
(`client_id` = `username`). Nếu Web (publish) và Pi (subscribe) cùng mở kết
nối bằng chung client_id, broker sẽ đá kết nối cũ mỗi lần có kết nối mới,
làm rớt phần lớn lệnh. Giải pháp: chỉ Web giữ kết nối MQTT; Pi đọc lệnh
bằng **HTTP polling nhịp cố định 1 giây** — vẫn nhận đủ cả 8 nút vì
ThingSpeak lưu chung mọi lần ghi (bất kể giao thức) vào cùng 1 feed.

## Vì sao 2 nút Auto/Manual đi MQTT, 6 nút còn lại đi HTTP

Đề bài mức độ 3 (buổi 5 lớp thầy Thanh) ghi rõ: *"Bắt buộc nút nhấn chọn
chế độ phải sử dụng giao thức MQTT; nút nhấn điều khiển phải sử dụng giao
thức HTTP."* Node `switch` trong flow tách thẳng theo đúng ràng buộc này —
xem trực tiếp trên sơ đồ khối Node-RED (nhóm `5a` và `5b`).

## Vòng đời một lệnh Manual (ví dụ bấm "Tắt LED")

```mermaid
sequenceDiagram
    participant U as Người dùng
    participant D as Dashboard (Node-RED)
    participant TS as ThingSpeak (channel LỆNH)
    participant P as Pi (control_poll_loop, 1s)
    participant G as GPIO18 (LED)

    U->>D: bấm "Tắt"
    D->>D: khoá cả 8 nút (cmdPending)
    D->>TS: POST update.json field1=0
    alt bị từ chối (đang trong 15s)
        TS-->>D: entry_id rỗng
        D->>D: đợi 3s, thử lại (tối đa 10 lần)
        D->>TS: POST update.json field1=0
    end
    TS-->>D: entry_id > 0 (thành công)
    D->>D: cmd_ok, mở khoá nút
    P->>TS: GET feeds.json (đến vòng poll tiếp theo)
    TS-->>P: field1 = 0
    P->>G: đèn tắt (led.off())
    Note over U,G: Toàn bộ dưới 2 giây kể từ lúc<br/>dữ liệu lên Server thành công (yêu cầu đề bài)
```
