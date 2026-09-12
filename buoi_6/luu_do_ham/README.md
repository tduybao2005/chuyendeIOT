# Lưu đồ thuật toán từng hàm — `chuong_trinh_pi.py`

Mỗi file `.md` dưới đây vẽ **lưu đồ thuật toán (flowchart)** cho đúng logic
bên trong một (hoặc một nhóm) hàm của
[`../raspberry/chuong_trinh_pi.py`](../raspberry/chuong_trinh_pi.py), dùng cú
pháp Mermaid — GitHub tự render trực tiếp khi mở file, không cần cài gì.

Khác với [`../KIEN_TRUC.md`](../KIEN_TRUC.md) (kiến trúc tổng thể toàn hệ
thống) và [`../so_do_ham_pi.drawio`](../so_do_ham_pi.drawio) (sơ đồ ai gọi
ai), các file trong thư mục này đi sâu vào **bên trong từng hàm chạy như thế
nào** — có nhánh rẽ (quyết định), vòng lặp, giá trị trả về.

## Bản draw.io (chỉnh sửa/thêm được trực tiếp trên app.diagrams.net)

**[`luu_do_ham.drawio`](luu_do_ham.drawio)** là bản vẽ đúng nội dung 11 lưu đồ
bên dưới nhưng ở định dạng draw.io — **11 trang (tab) riêng biệt**, mỗi trang
một hàm/nhóm hàm, dùng đúng ký hiệu lưu đồ chuẩn (oval bắt đầu/kết thúc, hình
thoi quyết định, chữ nhật xử lý). Đã canh lưới cẩn thận để **không có ô nào
đè lên ô khác, không có đường thẳng nào cắt qua ô hay nội dung** — kể cả các
đường "lặp lại" của vòng lặp đều đi vòng ra ngoài theo làn riêng.

Mở và sửa: [app.diagrams.net](https://app.diagrams.net/) → **File → Open
from → GitHub** → chọn repo, nhánh `main`, file
`buoi_6/luu_do_ham/luu_do_ham.drawio`. Thư mục
[`drawio/`](drawio/) chứa từng trang dưới dạng file `.drawio` riêng lẻ (để
dễ so sánh/chỉnh từng hàm mà không phải tải cả file lớn).

| File | Hàm | Dòng trong `chuong_trinh_pi.py` |
|---|---|---|
| [01_main.md](01_main.md) | `main()` | 561 |
| [02_sync_initial_state.md](02_sync_initial_state.md) | `sync_initial_state()` | 443 |
| [03_control_poll_loop.md](03_control_poll_loop.md) | `control_poll_loop()` | 482 |
| [04_poll_http_commands.md](04_poll_http_commands.md) | `poll_http_commands()` | 383 |
| [05_send_window_average.md](05_send_window_average.md) | `send_window_average()` | 539 |
| [06_send_to_thingspeak.md](06_send_to_thingspeak.md) | `send_to_thingspeak()` | 510 |
| [07_apply_outputs.md](07_apply_outputs.md) | `apply_outputs()` | 338 |
| [08_doc_cam_bien.md](08_doc_cam_bien.md) | `read_temp_humi()`, `read_voltage()`, `read_distance()` | 230, 242, 251 |
| [09_lcd_jhd1802.md](09_lcd_jhd1802.md) | `show_lcd()`, class `JHD1802` | 309, 263 |
| [10_tu_phuc_hoi.md](10_tu_phuc_hoi.md) | `fail_exit()`, `note_sensor_fail()`, `note_network_fail()`, `cleanup_outputs()` | 174, 201, 213, 161 |
| [11_ham_phu_tro.md](11_ham_phu_tro.md) | `log_event()`, `is_valid()`, `to_bool()`, `note_sensor_ok()`, `note_network_ok()` | 127, 139, 370, 197, 209 |
