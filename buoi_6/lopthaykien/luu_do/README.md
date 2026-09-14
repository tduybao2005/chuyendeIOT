# Lưu đồ thuật toán

Đề bài yêu cầu báo cáo trình bày **lưu đồ giải thuật** (chiếm 20% điểm cùng với
code và sơ đồ kết nối phần cứng). Mỗi chương trình một file riêng:

| File | Chương trình | Nội dung |
|---|---|---|
| [`01_ct2_cam_bien.md`](01_ct2_cam_bien.md) | CT2 | Đọc DHT mỗi 1s, gửi trung bình mỗi 20s |
| [`02_ct3_led.md`](02_ct3_led.md) | CT3 | Đọc lệnh mỗi 0,5s, điều khiển 3 LED |
| [`03_ct4_relay.md`](03_ct4_relay.md) | CT4 | Relay theo nút tay hoặc theo lịch hẹn giờ |
| [`04_ct5_lcd.md`](04_ct5_lcd.md) | CT5 | Đọc text 16×2, hiển thị lên LCD |
| [`05_ct1_node_red.md`](05_ct1_node_red.md) | CT1 | Ba luồng của flow Node-RED |
| [`06_tu_phuc_hoi.md`](06_tu_phuc_hoi.md) | chung | Cơ chế tự phục hồi dùng chung cho CT2–CT5 |

Lưu đồ viết bằng **Mermaid** — GitHub tự vẽ ra hình khi mở file. Muốn xuất ảnh
để dán vào báo cáo Word/PDF: mở [mermaid.live](https://mermaid.live), dán khối
code trong dấu ```` ```mermaid ```` vào, chọn **Actions → PNG/SVG**.

Sơ đồ kiến trúc tổng thể và sơ đồ nối dây nằm ở [`../KIEN_TRUC.md`](../KIEN_TRUC.md).
