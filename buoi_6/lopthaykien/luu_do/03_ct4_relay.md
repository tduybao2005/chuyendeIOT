# CT4 — Điều khiển relay theo lệnh và theo lịch hẹn giờ

File: [`../raspberry/ct4_relay.py`](../raspberry/ct4_relay.py) · phần **13 điểm**

> *"Thêm chương trình Điều khiển bật/tắt thiết bị relay theo giá trị đọc về từ
> server"* · *"Giao diện Web thêm giao diện để người dùng hẹn giờ bật tắt thiết
> bị relay"*

```mermaid
flowchart TB
    START([Bắt đầu]) --> LOG["Tạo logger riêng<br/>ct4_relay.log"]
    LOG --> INIT["Khởi tạo relay GPIO24<br/>initial_value=False"]
    INIT --> LOOP["⏱ Bắt đầu một vòng<br/>(chu kỳ cố định 2 giây)"]

    LOOP --> GET["GET channel LỆNH<br/>lấy field4 (nút tay)<br/>và field6 (lịch)"]
    GET --> NETOK{"Gọi API<br/>thành công?"}
    NETOK -- "không" --> NETFAIL["Đếm lỗi mạng<br/>GIỮ NGUYÊN relay"]
    NETFAIL --> NETCHK{"20 lần<br/>liên tiếp?"}
    NETCHK -- "rồi" --> EXIT1["Ngắt relay<br/>os._exit(1)"]
    NETCHK -- "chưa" --> SLEEP

    NETOK -- "có" --> PARSE["Tách field6<br/>'bật|giờ bật|giờ tắt'"]
    PARSE --> FMT{"Đúng 3 phần,<br/>giờ hợp lệ<br/>00:00–23:59?"}
    FMT -- "sai" --> WARN["Ghi log cảnh báo<br/>coi như TẮT lịch"]
    WARN --> MANUAL
    FMT -- "đúng" --> CHANGED{"Lịch khác<br/>lần đọc trước?"}
    CHANGED -- "có" --> LOGSCH["Ghi log lịch mới"]
    CHANGED -- "không" --> MODE
    LOGSCH --> MODE{"Lịch<br/>đang bật?"}

    MODE -- "không" --> MANUAL["Relay theo field4<br/>(nút bấm tay trên Web)"]
    MODE -- "có" --> NOW["Đổi giờ hiện tại<br/>sang phút kể từ nửa đêm"]
    NOW --> WRAP{"giờ bật<br/>&lt; giờ tắt?"}
    WRAP -- "có · khung trong ngày" --> IN1{"bật ≤ nay &lt; tắt?"}
    WRAP -- "không · khung vắt<br/>qua nửa đêm" --> IN2{"nay ≥ bật<br/>HOẶC nay &lt; tắt?"}
    IN1 -- "đúng" --> ON["Mong muốn = ĐÓNG"]
    IN1 -- "sai" --> OFF["Mong muốn = NGẮT"]
    IN2 -- "đúng" --> ON
    IN2 -- "sai" --> OFF

    MANUAL --> DIFF
    ON --> DIFF{"Khác trạng thái<br/>hiện tại?"}
    OFF --> DIFF
    DIFF -- "không" --> SLEEP
    DIFF -- "có" --> ACT["relay.on() / relay.off()<br/>ghi log kèm LÝ DO<br/>(theo lịch hay theo nút tay)"]
    ACT --> SLEEP["Ngủ nốt phần còn lại<br/>để chu kỳ đúng 2 giây"]
    SLEEP --> LOOP

    classDef ok  fill:#064e3b,stroke:#34d399,color:#e9f0fa;
    classDef bad fill:#4c1d24,stroke:#f87171,color:#e9f0fa;
    classDef io  fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    class ACT,ON ok;
    class EXIT1,NETFAIL,WARN bad;
    class GET io;
```

## Ba chỗ đáng chú ý

**Khung giờ vắt qua nửa đêm.** `22:00 → 06:00` nghĩa là bật từ 22h hôm nay đến
6h sáng hôm sau. Nếu chỉ viết `bật ≤ nay < tắt` thì `1320 ≤ nay < 360` không bao
giờ đúng — relay sẽ không bao giờ đóng. Phải tách riêng thành
`nay ≥ bật HOẶC nay < tắt`.

**Giờ bật trùng giờ tắt** cho khung rỗng → luôn ngắt. Không thể vừa bật vừa tắt
tại cùng một thời điểm, nên chọn trạng thái an toàn. Giao diện Web cũng cảnh báo
trước khi gửi.

**Chuỗi lịch sai định dạng thì rơi về chế độ tay**, không kẹt cứng ở một trạng
thái khó đoán. Ai đó ghi tay bằng `curl` một chuỗi rác thì relay vẫn còn điều
khiển được bằng nút bấm.

**Vì sao gửi lịch lên server thay vì hẹn giờ ngay trong Node-RED.** Đề yêu cầu
rõ chương trình này *"điều khiển relay theo giá trị đọc về từ server"*. Đặt lịch
trên server còn thêm hai cái lợi thật: lịch sống sót qua cả lần khởi động lại
Node-RED, và người chấm mở channel lên là thấy được lịch đang đặt.
