# Lưu đồ đọc cảm biến — `read_temp_humi()`, `read_voltage()`, `read_distance()`

Cả 3 hàm dùng chung một khuôn mẫu: đọc phần cứng → bắt lỗi → lọc theo dải
hợp lệ.

```mermaid
flowchart TD
    START([Bắt đầu]) --> KIND{"Hàm nào?"}

    KIND -- "read_temp_humi()<br/>dòng 230" --> RDHT["Đọc DHT (D5 / GPIO5)<br/>humi_raw, temp_raw"]
    RDHT --> EDHT{"Exception khi<br/>đọc / ép kiểu int?"}
    EDHT -- "Có" --> NDHT["In lỗi<br/>return None, None"] --> ENDA([Kết thúc])
    EDHT -- "Không" --> VDHT["temp = temp_raw nếu<br/>0 &le; temp_raw &le; 100,<br/>ngược lại None<br/>humi = humi_raw nếu<br/>20 &le; humi_raw &le; 95,<br/>ngược lại None"]
    VDHT --> RETDHT([Trả về temp, humi])

    KIND -- "read_voltage()<br/>dòng 242" --> RADC["Đọc ADC I2C 0x08,<br/>kênh 2, chia 1000<br/>(mV -> V)"]
    RADC --> EADC{"Exception?"}
    EADC -- "Có" --> NADC["In lỗi<br/>return None"] --> ENDB([Kết thúc])
    EADC -- "Không" --> VADC{"0 &le; voltage &le; 3.3?"}
    VADC -- "Có" --> RETV1([Trả về voltage])
    VADC -- "Không" --> RETV0([Trả về None])

    KIND -- "read_distance()<br/>dòng 251" --> RUS["Đọc cảm biến<br/>siêu âm (D16 / GPIO16)"]
    RUS --> EUS{"Exception?"}
    EUS -- "Có" --> NUS["In lỗi<br/>return None"] --> ENDC([Kết thúc])
    EUS -- "Không" --> VUS{"2 &le; distance &le; 350?"}
    VUS -- "Có" --> RETD1([Trả về distance])
    VUS -- "Không" --> RETD0([Trả về None])
```

`None` được coi là "không đọc được / dữ liệu bất thường" — nơi gọi các hàm
này (`main()`) sẽ **loại bỏ**, không cộng vào `window[]` và không gửi lên
Server, đúng yêu cầu đề bài.
