# CT5 — Đọc text 16×2 từ server, hiển thị lên LCD

File: [`../raspberry/ct5_lcd.py`](../raspberry/ct5_lcd.py) · phần **13 điểm**

> *"Đọc dữ liệu text 16x2 từ server, hiển thị giá trị lên LCD 16x2. Có logfile
> riêng; chương trình cũng tự khởi động như các chương trình khác."*

```mermaid
flowchart TB
    START([Bắt đầu]) --> LOG["Tạo logger riêng<br/>ct5_lcd.log"]
    LOG --> LCDINIT["Khởi tạo LCD JHD1802<br/>I2C 0x3E + đèn nền 0x62"]
    LCDINIT --> LCDOK{"LCD có<br/>trả lời<br/>trên I2C?"}
    LCDOK -- "không" --> EXIT1A["Ghi log 'không thấy LCD'<br/>thoát mã 1<br/>→ systemd thử lại sau 10s<br/>(cắm dây vào là chạy)"]
    LCDOK -- "có" --> HELLO["Hiện 'IoT Buoi 6'<br/>'Cho du lieu...'"]

    HELLO --> LOOP["⏱ Bắt đầu một vòng<br/>(chu kỳ cố định 5 giây)"]
    LOOP --> GET["GET channel LỆNH<br/>lấy field5"]
    GET --> NETOK{"Gọi API<br/>thành công?"}
    NETOK -- "không" --> NETFAIL["Đếm lỗi mạng<br/>GIỮ NGUYÊN màn hình"]
    NETFAIL --> NETCHK{"20 lần<br/>liên tiếp?"}
    NETCHK -- "rồi" --> EXIT1["os._exit(1)"]
    NETCHK -- "chưa" --> SLEEP

    NETOK -- "có" --> EMPTY{"field5 đã từng<br/>được ghi chưa?"}
    EMPTY -- "chưa" --> CLOCK["Hiện 'IoT Buoi 6'<br/>+ đồng hồ HH:MM:SS<br/>(để nhìn biết màn hình còn sống)"]
    EMPTY -- "rồi" --> SPLIT["Tách chuỗi theo dấu |<br/>→ dòng 1, dòng 2"]
    SPLIT --> STRIP["Bỏ dấu tiếng Việt<br/>chuẩn hoá NFD, loại ký tự dấu<br/>đ→d, Đ→D, ngoài ASCII → ?"]
    STRIP --> CUT["Cắt đúng 16 ký tự mỗi dòng<br/>đệm khoảng trắng cho đủ"]

    CLOCK --> SAME
    CUT --> SAME{"Khác nội dung<br/>đang hiện?"}
    SAME -- "không" --> SLEEP
    SAME -- "có" --> WRITE["Ghi 2 dòng ra LCD qua I2C"]
    WRITE --> WOK{"Ghi I2C<br/>thành công?"}
    WOK -- "không" --> SFAIL["Đếm lỗi cảm biến"]
    SFAIL --> SCHK{"30 lần<br/>liên tiếp?"}
    SCHK -- "rồi" --> EXIT1
    SCHK -- "chưa" --> SLEEP
    WOK -- "có" --> LOGW["Đưa bộ đếm về 0<br/>ghi log nội dung vừa hiện"]
    LOGW --> SLEEP["Ngủ nốt phần còn lại<br/>để chu kỳ đúng 5 giây"]
    SLEEP --> LOOP

    classDef ok  fill:#064e3b,stroke:#34d399,color:#e9f0fa;
    classDef bad fill:#4c1d24,stroke:#f87171,color:#e9f0fa;
    classDef io  fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    class WRITE,LOGW ok;
    class EXIT1,EXIT1A,NETFAIL,SFAIL bad;
    class GET,LCDINIT io;
```

## Ba chỗ đáng chú ý

**Tự viết driver LCD thay vì dùng `grove.display.jhd1802`.** Thư viện Grove
**nuốt** lỗi I2C — LCD tuột dây mà chương trình vẫn báo "chạy bình thường",
không hiện gì. Không phát hiện được lỗi thì không thể tự khởi động lại, mà đó là
yêu cầu bắt buộc của đề. Driver tự viết để mọi lỗi ghi I2C ném thẳng ra ngoài
cho vòng lặp đếm.

**Bỏ dấu tiếng Việt.** LCD 16×2 chỉ có bảng ký tự ASCII, không có "ệ" hay "ộ".
Chuẩn hoá NFD tách chữ cái khỏi dấu rồi loại các ký tự dấu (category `Mn`);
riêng "đ"/"Đ" không tách được bằng NFD nên phải đổi tay. Ô xem trước trên Web
làm đúng phép biến đổi này nên nhìn trước là biết LCD sẽ hiện gì.

**Vẫn cắt lại 16 ký tự dù Web đã chặn.** Không bao giờ tin dữ liệu từ bên ngoài:
ai đó ghi tay bằng `curl` một chuỗi 100 ký tự thì LCD sẽ tràn sang dòng dưới và
hiện ra rác.

**Thoát mã 1 khi không thấy LCD, không phải mã 2.** Mã 2 là lỗi cấu hình (cần
người sửa file), systemd sẽ dựng lại vô ích. Ở đây chỉ là chưa cắm dây — để mã 1
cho systemd cứ thử lại đều đặn, cắm dây vào là chạy, không cần ai ssh vào.
