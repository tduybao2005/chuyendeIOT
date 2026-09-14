# Lưu đồ thuật toán từng hàm — `chuong_trinh_pi.py`

Mỗi file `.md` dưới đây vẽ **lưu đồ thuật toán (flowchart)** cho đúng logic
bên trong một (hoặc một nhóm) hàm của
[`../raspberry/chuong_trinh_pi.py`](../raspberry/chuong_trinh_pi.py), dùng cú
pháp Mermaid — GitHub tự render trực tiếp khi mở file, không cần cài gì.

Khác với [`../KIEN_TRUC.md`](../KIEN_TRUC.md) (kiến trúc tổng thể toàn hệ
thống) và [`../so_do_ham_pi.drawio`](../so_do_ham_pi.drawio) (sơ đồ ai gọi
ai), các file trong thư mục này đi sâu vào **bên trong từng hàm chạy như thế
nào** — có nhánh rẽ (quyết định), vòng lặp, giá trị trả về.

## Bản draw.io — mỗi hàm 1 file riêng (khuyên dùng)

Thư mục **[`drawio/`](drawio/)** chứa **11 file `.drawio` độc lập**, mỗi file
đúng 1 lưu đồ của 1 hàm/nhóm hàm — bấm vào từng file trên GitHub là thấy đúng
lưu đồ đó, không lẫn với hàm khác:

| File draw.io | Hàm |
|---|---|
| [drawio/01_main.drawio](drawio/01_main.drawio) | `main()` |
| [drawio/02_sync_initial_state.drawio](drawio/02_sync_initial_state.drawio) | `sync_initial_state()` |
| [drawio/03_control_poll_loop.drawio](drawio/03_control_poll_loop.drawio) | `control_poll_loop()` |
| [drawio/04_poll_http_commands.drawio](drawio/04_poll_http_commands.drawio) | `poll_http_commands()` |
| [drawio/05_send_window_average.drawio](drawio/05_send_window_average.drawio) | `send_window_average()` |
| [drawio/06_send_to_thingspeak.drawio](drawio/06_send_to_thingspeak.drawio) | `send_to_thingspeak()` |
| [drawio/07_apply_outputs.drawio](drawio/07_apply_outputs.drawio) | `apply_outputs()` |
| [drawio/08_doc_cam_bien.drawio](drawio/08_doc_cam_bien.drawio) | `read_temp_humi()`, `read_voltage()`, `read_distance()` |
| [drawio/09_lcd_jhd1802.drawio](drawio/09_lcd_jhd1802.drawio) | `show_lcd()`, class `JHD1802` |
| [drawio/10_tu_phuc_hoi.drawio](drawio/10_tu_phuc_hoi.drawio) | `fail_exit()`, `note_sensor_fail()`, `note_network_fail()`, `cleanup_outputs()` |
| [drawio/11_ham_phu_tro.drawio](drawio/11_ham_phu_tro.drawio) | `log_event()`, `is_valid()`, `to_bool()`, `note_sensor_ok()`, `note_network_ok()` |

Mở/sửa trực tiếp: bấm vào file trên GitHub → **Open with app.diagrams.net**
(hoặc vào [app.diagrams.net](https://app.diagrams.net/) → File → Open from →
GitHub → chọn đúng file). Đã canh lưới cẩn thận để **không có ô nào đè lên ô
khác, không có đường nào cắt qua ô hay nội dung** — kể cả đường "lặp lại" của
vòng lặp đều đi vòng ra ngoài theo làn riêng.

**[`luu_do_ham.drawio`](luu_do_ham.drawio)** là bản gộp cả 11 lưu đồ trên
thành 1 file 11 trang (tab) — tiện khi mở bằng app.diagrams.net để lướt qua
lần lượt, nhưng xem trực tiếp trên GitHub **chỉ thấy trang đầu tiên** (giới
hạn của bản xem trước GitHub, không phải lỗi file) — nếu muốn xem đúng 1 hàm
cụ thể trên GitHub, dùng file riêng trong `drawio/` ở trên.

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
