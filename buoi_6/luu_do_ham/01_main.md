# Lưu đồ `main()` — dòng 561

```mermaid
flowchart TD
    START([Bắt đầu]) --> INIT["Xoá LCD<br/>sync_initial_state()"]
    INIT --> THREAD["Tạo & chạy luồng<br/>control_poll_loop(stop_event)<br/>(daemon, chạy song song)"]
    THREAD --> LOOP{{"Vòng lặp vô hạn<br/>(while True)"}}

    LOOP --> READ["Đọc cảm biến:<br/>read_temp_humi()<br/>read_voltage()<br/>read_distance()"]
    READ --> CHK{"Cả 4 giá trị<br/>đều None?"}
    CHK -- "Đúng (mất cảm biến)" --> SFAIL["note_sensor_fail()"]
    CHK -- "Sai (còn ít nhất 1)" --> SOK["note_sensor_ok()"]
    SFAIL --> ACC
    SOK --> ACC["Giá trị hợp lệ (khác None)<br/>-> cộng dồn vào window[]<br/>và cập nhật state['temp']/['humi']"]

    ACC --> APPLY["apply_outputs()<br/>(đánh giá lại Auto mỗi giây)"]
    APPLY --> LCD["show_lcd(mode, led, buzzer, relay)"]
    LCD --> WSTART{"window_start<br/>đã có chưa?"}
    WSTART -- "Chưa" --> SETWS["window_start = bây giờ"]
    WSTART -- "Rồi" --> ELAPSED
    SETWS --> ELAPSED{"đã trôi qua<br/>>= 20 giây?"}
    ELAPSED -- "Chưa" --> SLEEP
    ELAPSED -- "Rồi" --> SEND["send_window_average(window)<br/>reset window[] rỗng<br/>window_start = bây giờ"]
    SEND --> SLEEP["sleep(1 giây)"]

    SLEEP --> EXC{"Có lỗi (Exception)<br/>ở bất kỳ bước nào<br/>trong vòng lặp?"}
    EXC -- "Có" --> LOG["In lỗi ra console<br/>(KHÔNG dừng chương trình)"] --> LOOP
    EXC -- "Không" --> LOOP

    LOOP -.->|"Ctrl+C<br/>(KeyboardInterrupt)"| STOP["stop_event.set()<br/>(báo luồng poll dừng)"]
    STOP --> OFF["Tắt LED, Buzzer, Relay<br/>(finally — luôn chạy,<br/>kể cả khi có lỗi)"]
    OFF --> END([Kết thúc])
```

**Ghi chú:**
- Khối "Có lỗi" bọc toàn bộ thân vòng lặp bằng `try/except` — đúng gợi ý của
  đề: lỗi lẻ tẻ (cảm biến đọc lỗi 1 lần, mạng chập chờn) thì in log rồi
  **chạy tiếp**, không dừng hẳn chương trình.
- `note_sensor_fail()` chỉ **đếm dồn**; việc thoát hẳn chương trình (khi lỗi
  kéo dài liên tiếp) nằm trong `fail_exit()` — xem
  [10_tu_phuc_hoi.md](10_tu_phuc_hoi.md).
- Luồng `control_poll_loop()` chạy **song song, độc lập** với vòng lặp này —
  xem [03_control_poll_loop.md](03_control_poll_loop.md).
