# Lưu đồ `send_window_average(window)` — dòng 539

```mermaid
flowchart TD
    START([Bắt đầu<br/>window = 4 danh sách giá trị<br/>trong 20 giây vừa qua]) --> AVG["Tính trung bình từng danh sách<br/>KHÔNG rỗng: temp, humi,<br/>voltage, distance"]
    AVG --> EMPTY{"Cả 4 danh sách<br/>đều rỗng?<br/>(20s qua không đọc được<br/>giá trị hợp lệ nào)"}
    EMPTY -- "Có" --> WARN["In cảnh báo,<br/>KHÔNG gửi gói tin này"] --> END1([Kết thúc])
    EMPTY -- "Không" --> BUILD["Làm tròn & gán vào field<br/>tương ứng CHỈ với đại lượng<br/>có dữ liệu (fields = {...})"]
    BUILD --> SEND["send_to_thingspeak(**fields)"]
    SEND --> OK{"Gửi<br/>thành công?"}
    OK -- "Có" --> LOG["In: đã gửi trung bình<br/>lên ThingSpeak"] --> END2([Kết thúc])
    OK -- "Không" --> END3([Kết thúc,<br/>lỗi đã in trong<br/>send_to_thingspeak])
```

Đây chính là cơ chế thực hiện đúng yêu cầu đề bài: *"nếu dữ liệu cảm biến bị
lỗi thì không được gửi lên Server mà phải đọc lại và gửi dữ liệu khác"* — chỉ
đại lượng nào **có ít nhất 1 giá trị hợp lệ** trong 20 giây mới được đưa vào
gói tin gửi đi; nếu tất cả đều lỗi thì bỏ hẳn gói tin đó thay vì gửi dữ liệu
rác.
