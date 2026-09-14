# CT3 — Đọc lệnh nút nhấn từ server, điều khiển 3 LED

File: [`../raspberry/ct3_led.py`](../raspberry/ct3_led.py)

> *"Chương trình 3 đọc dữ liệu nút nhấn từ server, điều khiển LED theo giá trị
> nhận được."*

```mermaid
flowchart TB
    START([Bắt đầu]) --> LOG["Tạo logger riêng<br/>ct3_led.log"]
    LOG --> CFG{"Đã điền<br/>Channel ID +<br/>Read key?"}
    CFG -- "chưa" --> EXIT2["Thoát mã 2<br/>(lỗi cấu hình)"]
    CFG -- "rồi" --> INIT["Khởi tạo 3 LED<br/>GPIO5 · GPIO16 · GPIO18<br/>initial_value=False"]
    INIT --> SEED["Trạng thái đang bật = None<br/>(chưa biết → lần đầu luôn ghi log)"]

    SEED --> LOOP["⏱ Bắt đầu một vòng<br/>(chu kỳ cố định 0,5 giây)"]
    LOOP --> GET["GET channels/&lt;B&gt;/feeds.json<br/>results=10"]

    GET --> NETOK{"Gọi API<br/>thành công?"}
    NETOK -- "không" --> NETFAIL["Tăng bộ đếm lỗi mạng<br/>GIỮ NGUYÊN trạng thái 3 LED"]
    NETFAIL --> NETCHK{"Đã 20 lần<br/>liên tiếp?"}
    NETCHK -- "rồi" --> EXIT1["Tắt cả 3 LED<br/>os._exit(1)<br/>→ systemd dựng lại"]
    NETCHK -- "chưa" --> SLEEP

    NETOK -- "có" --> SCAN["Quét NGƯỢC 10 bản ghi<br/>lấy giá trị KHÔNG null<br/>đầu tiên cho TỪNG field"]
    SCAN --> EACH["Với mỗi LED 1/2/3"]
    EACH --> NULL{"field<br/>chưa từng<br/>được ghi?"}
    NULL -- "rồi" --> OFF["Coi như TẮT<br/>(mặc định an toàn)"]
    NULL -- "chưa" --> CONV["Đổi sang True/False"]
    OFF --> DIFF
    CONV --> DIFF{"Khác trạng thái<br/>đang bật?"}

    DIFF -- "không" --> NEXT["LED tiếp theo"]
    DIFF -- "có" --> ACT["led.on() hoặc led.off()<br/>cập nhật trạng thái đang bật"]
    ACT --> NEXT
    NEXT --> DONE{"Hết 3 LED?"}
    DONE -- "chưa" --> EACH
    DONE -- "rồi" --> CHANGED{"Có LED nào<br/>vừa đổi?"}

    CHANGED -- "không" --> SLEEP
    CHANGED -- "có" --> LOG2["Ghi 2 dòng log có mili giây:<br/>'NHAN LENH TU SERVER'<br/>'DA AP DUNG XONG'"]
    LOG2 --> SLEEP["Ngủ nốt phần còn lại<br/>để chu kỳ đúng 0,5 giây"]
    SLEEP --> LOOP

    classDef ok   fill:#064e3b,stroke:#34d399,color:#e9f0fa;
    classDef bad  fill:#4c1d24,stroke:#f87171,color:#e9f0fa;
    classDef io   fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    class ACT,LOG2 ok;
    class EXIT1,EXIT2,NETFAIL bad;
    class GET io;
```

## Ba chỗ đáng chú ý

**Vì sao 0,5 giây chứ không phải 1 giây.** Ràng buộc: từ lúc bấm nút trên Web
đến lúc đèn sáng phải dưới 2 giây.

| Chặng | Thời gian |
|---|---|
| Web POST lên ThingSpeak | 0,3 – 0,9 s |
| Chờ vòng poll kế tiếp | ≤ nhịp poll |
| GET của CT3 đi và về | 0,3 – 0,5 s |

Nhịp 1s cho xấu nhất `0,9 + 1,0 + 0,5 = 2,4s` → **vỡ mốc**.
Nhịp 0,5s cho xấu nhất `0,9 + 0,5 + 0,5 = 1,9s` → **đạt**.

**Phải là chu kỳ cố định.** `VongLapDinhNhip` trừ đi thời gian vừa tốn cho
request. Nếu chỉ `sleep(0.5)` sau mỗi request thì chu kỳ thật là
`0,5 + 0,4 = 0,9s` và mốc 2 giây lại vỡ.

**Vì sao quét ngược từng field.** Mỗi lần ghi, ThingSpeak tạo một dòng mới và đặt
`null` cho field không gửi trong lần đó. Chỉ nhìn dòng cuối sẽ tưởng các field
kia đã bị xoá.

**Chỉ tác động GPIO khi có thay đổi.** Gọi `led.on()` mỗi 0,5 giây cũng không
hỏng gì, nhưng logfile sẽ đầy rác và không còn dùng để đối chiếu độ trễ được nữa.
