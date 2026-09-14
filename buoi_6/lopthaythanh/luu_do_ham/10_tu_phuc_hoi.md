# Lưu đồ nhóm Tự phục hồi — tính năng thêm của buổi 6

`fail_exit()` (dòng 174), `note_sensor_fail()` (dòng 201),
`note_network_fail()` (dòng 213), `cleanup_outputs()` (dòng 161).

```mermaid
flowchart TD
    S1([note_sensor_fail<br/>được gọi]) --> INC1["health['sensor_fail'] += 1"]
    INC1 --> LOG1["In: n/30 lần liên tiếp"]
    LOG1 --> CHK1{"n &ge; 30?<br/>(SENSOR_FAIL_LIMIT)"}
    CHK1 -- "Chưa" --> END1([Kết thúc, chạy tiếp])
    CHK1 -- "Đủ" --> CALL1["fail_exit('cảm biến lỗi n lần liên tiếp')"]

    S2([note_network_fail<br/>được gọi]) --> INC2["health['network_fail'] += 1"]
    INC2 --> LOG2["In: n/20 lần liên tiếp"]
    LOG2 --> CHK2{"n &ge; 20?<br/>(NETWORK_FAIL_LIMIT)"}
    CHK2 -- "Chưa" --> END2([Kết thúc, chạy tiếp])
    CHK2 -- "Đủ" --> CALL1

    CALL1 --> T1{{"try"}}
    T1 --> LOG3["log_event('TU KHOI DONG LAI: ...')"]
    LOG3 --> CLEAN["cleanup_outputs():<br/>tắt LED, Buzzer, Relay<br/>(mỗi thiết bị bọc try/except riêng)"]
    CLEAN --> FLUSH["sys.stdout.flush()<br/>(đảm bảo log kịp ghi vào journal<br/>trước khi tiến trình chết)"]
    FLUSH --> T2{{"finally<br/>(LUÔN chạy dù bước trên<br/>có lỗi hay không)"}}
    T2 --> EXIT["os._exit(1)<br/>(kết thúc CẢ tiến trình<br/>ngay lập tức, bỏ qua mọi<br/>finally khác)"]
    EXIT --> SYSTEMD["systemd (iot-buoi6.service)<br/>Restart=always, RestartSec=10<br/>-> dựng lại 1 tiến trình HOÀN TOÀN SẠCH<br/>sau 10 giây"]
    SYSTEMD --> END3([Chương trình chạy lại từ đầu])
```

**Vì sao `os._exit()` thay vì `sys.exit()`?** `fail_exit()` có thể được gọi
từ **luồng đọc lệnh** (`control_poll_loop`, qua `note_network_fail()`) chứ
không chỉ luồng chính. `sys.exit()` trong một luồng phụ chỉ kết thúc đúng
luồng đó — tiến trình vẫn sống nhưng "què", không còn đọc lệnh nữa mà
không ai biết. `os._exit()` kết thúc **toàn bộ tiến trình** dù gọi từ luồng
nào.

**Vì sao bọc `try/finally`?** Đã gặp lỗi thật khi test: thiếu `import sys`
khiến `NameError` bên trong khối này bị `except Exception` của vòng lặp gọi
nó **nuốt mất** — bộ đếm lỗi cứ tăng (21/20, 22/20...) mà chương trình không
bao giờ thực sự thoát/khởi động lại. Đặt `os._exit(1)` trong `finally` đảm
bảo dù bước log/dọn dẹp phía trên có lỗi gì, tiến trình vẫn chắc chắn thoát.
