# CT2 — Đọc cảm biến và gửi trung bình lên server

File: [`../raspberry/ct2_cam_bien.py`](../raspberry/ct2_cam_bien.py)

> *"Chương trình 2 đọc dữ liệu nhiệt độ, độ ẩm mỗi 1s, gửi lên server giá trị
> nhiệt độ, độ ẩm trung bình mỗi 20s."*

```mermaid
flowchart TB
    START([Bắt đầu]) --> LOG["Tạo logger riêng<br/>ct2_cam_bien.log"]
    LOG --> CFG{"Đã điền<br/>Channel ID +<br/>Write key?"}
    CFG -- "chưa" --> EXIT2["Ghi log lỗi cấu hình<br/>thoát mã 2"]
    CFG -- "rồi" --> INIT["Khởi tạo cảm biến DHT<br/>trên GPIO22"]
    INIT --> OK1{"Khởi tạo<br/>được?"}
    OK1 -- "không" --> EXIT2
    OK1 -- "có" --> RESET["Cửa sổ rỗng<br/>số vòng = 0"]

    RESET --> LOOP["⏱ Bắt đầu một vòng<br/>(chu kỳ cố định 1 giây)"]
    LOOP --> READ["Đọc DHT<br/>nhiệt độ, độ ẩm"]
    READ --> VALID{"Giá trị trong<br/>dải hợp lệ?<br/>0–100°C · 20–95%"}

    VALID -- "không cái nào hợp lệ" --> FAILS["Tăng bộ đếm lỗi cảm biến<br/>ghi log"]
    FAILS --> CHECK{"Đã 30 lần<br/>liên tiếp?"}
    CHECK -- "rồi" --> EXIT1["Ghi log lý do<br/>os._exit(1)<br/>→ systemd dựng lại"]
    CHECK -- "chưa" --> COUNT

    VALID -- "có ít nhất 1 giá trị" --> ADD["Đưa giá trị hợp lệ<br/>vào cửa sổ 20s<br/>(giá trị lỗi bị LOẠI, không gửi)"]
    ADD --> OKS["Đưa bộ đếm lỗi về 0"]
    OKS --> COUNT["Số vòng += 1"]

    COUNT --> FULL{"Đã đủ<br/>20 vòng?"}
    FULL -- "chưa" --> SLEEP
    FULL -- "rồi" --> AVG["Tính trung bình<br/>của các giá trị hợp lệ"]

    AVG --> HAS{"Có giá trị<br/>nào không?"}
    HAS -- "không" --> SKIP["Ghi log 'bỏ qua kỳ này'<br/>KHÔNG gửi số bịa lên server"]
    HAS -- "có" --> POST["POST update.json<br/>field1 = nhiệt độ TB<br/>field2 = độ ẩm TB"]

    POST --> RES{"entry_id > 0?"}
    RES -- "có" --> NETOK["Đưa bộ đếm lỗi mạng về 0<br/>ghi log đã gửi"]
    RES -- "không" --> RETRY{"Đã thử<br/>3 lần?"}
    RETRY -- "chưa" --> WAIT5["Chờ 5 giây<br/>(có thể đang vướng<br/>giới hạn 15s)"]
    WAIT5 --> POST
    RETRY -- "rồi" --> NETFAIL["Tăng bộ đếm lỗi mạng"]
    NETFAIL --> NETCHK{"Đã 20 lần<br/>liên tiếp?"}
    NETCHK -- "rồi" --> EXIT1
    NETCHK -- "chưa" --> CLEAR

    NETOK --> CLEAR["Xoá cửa sổ<br/>số vòng = 0"]
    SKIP --> CLEAR
    CLEAR --> SLEEP["Ngủ nốt phần còn lại<br/>để chu kỳ đúng 1 giây"]
    SLEEP --> LOOP

    classDef ok   fill:#064e3b,stroke:#34d399,color:#e9f0fa;
    classDef bad  fill:#4c1d24,stroke:#f87171,color:#e9f0fa;
    classDef io   fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    class NETOK,OKS,ADD ok;
    class EXIT1,EXIT2,FAILS,NETFAIL,SKIP bad;
    class POST,READ io;
```

## Ba chỗ đáng chú ý

**Lọc trước khi cộng, không lọc sau.** Đề ghi *"nếu dữ liệu cảm biến bị lỗi thì
không được gửi lên Server mà phải đọc lại"*. Giá trị ngoài dải bị loại ngay tại
chỗ đọc, không bao giờ vào cửa sổ trung bình — nếu để lọt một số 0 vào rồi mới
lọc thì trung bình đã sai.

**DHT hỏng thường trả về đúng `0.0/0.0`**, rơi vào đây bị loại luôn vì độ ẩm 0%
nằm ngoài dải 20–95%.

**Đếm vòng chứ không đo đồng hồ.** Chu kỳ đã được giữ chính xác 1 giây, nên đếm
20 vòng đơn giản hơn và không bị trôi so với việc so mốc `datetime.now()`.
