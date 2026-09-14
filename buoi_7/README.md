# Buổi 7 - Mức độ 3 (10 điểm) - Nhóm 3

Hệ thống IoT 2 thành phần trao đổi dữ liệu qua **UDP** (nhóm 3 là nhóm lẻ nên
theo đề bắt buộc dùng UDP), có **CRC** trong frame:

- **Master** = chạy trên **máy tính** (đề cho phép thay Raspberry bằng máy
  tính). Không có GPIO — chỉ làm mạng + hiển thị Terminal + gửi ThingSpeak.
- **Slave** = chạy trên **Raspberry Pi**, gắn cảm biến DHT, LCD 16x2, 3 LED.

```
buoi_7/
  protocol.py                    # Frame + CRC dùng chung 2 bên (copy kèm theo mỗi script khi triển khai)
  slave/chuong_trinh_slave_pi.py # Chạy trên Raspberry Pi (Slave)
  master/chuong_trinh_master_pc.py # Chạy trên máy tính (Master)
```

## Sơ đồ nối dây (Slave - Raspberry Pi)

Lấy đúng theo các file cũ trong repo (buổi 1, buổi 6):

| Thiết bị        | Chân/cổng     | Ghi chú                                   |
|-----------------|---------------|--------------------------------------------|
| DHT (nhiệt độ, độ ẩm) | D5 (GPIO5) | giống `buoi_6/raspberry/chuong_trinh_pi.py` |
| LCD 16x2 (JHD1802)    | I2C-1: 0x3E (màn hình) + 0x62 (đèn nền) | giống `buoi_6/raspberry/chuong_trinh_pi.py` |
| LED đỏ    | D16 (GPIO16) | giống `buoi_1/muc_do_3.py` (module 1) |
| LED vàng  | D22 (GPIO22) | đã test thực tế trên pi4-tdbao ngày 2026-09-14, đổi chỗ với GPIO24 |
| LED xanh  | D24 (GPIO24) | đã test thực tế trên pi4-tdbao ngày 2026-09-14, đổi chỗ với GPIO22 |

Ảnh đề có chụp thêm 1 module nút nhấn (button) cạnh cảm biến DHT, nhưng nội
dung đề mức độ 3 không mô tả chức năng nào cho nút nhấn ở Slave nên chưa nối/
dùng tới trong code. Nếu cần dùng, thêm theo đúng mẫu
`from gpiozero import Button` như `buoi_1/muc_do_3.py`.

Master chạy trên máy tính nên không cần GPIO gì cả.

## Cấu trúc Frame (chi tiết trong `protocol.py`)

```
| STX (1B) | TYPE (1B) | SEQ (1B) | LEN (1B) | PAYLOAD (LEN byte) | CRC16 (2B) | ETX (1B) |
```

- `STX=0xAA`, `ETX=0x55`: đánh dấu biên frame.
- `TYPE`: `0x01` = SENSOR_DATA (Slave→Master), `0x02` = LED_CTRL (Master→Slave).
- `SEQ`: số thứ tự 0..255 (quay vòng) — phát hiện gói đến trễ/trùng lặp (UDP
  không đảm bảo thứ tự/không đảm bảo gửi tới).
- `LEN`: số byte của PAYLOAD.
- `CRC16`: CRC-16/CCITT tính trên `TYPE+SEQ+LEN+PAYLOAD`; sai thì hủy frame.
- Payload `SENSOR_DATA` (5 byte): `FLAGS(1B)` báo nhiệt độ/độ ẩm có hợp lệ
  không + `TEMP*10`, `HUMI*10` (mỗi cái 2 byte, số nguyên có dấu, cố định 1
  chữ số thập phân để tránh khác biệt định dạng số thực giữa các máy).
- Payload `LED_CTRL` (1 byte): `LED_MASK` — bit0 đỏ, bit1 vàng, bit2 xanh.

Giải thích đầy đủ ý nghĩa từng trường (để đưa vào báo cáo) nằm ở đầu file
`protocol.py`.

## Trước khi chạy thật

1. **Địa chỉ IP/cổng:**
   - `master/chuong_trinh_master_pc.py`: `SLAVE_IP` đã điền sẵn `192.168.44.211`
     (IP LAN của Pi `pi4-tdbao`, đã test thực tế 2026-09-14). Nếu Pi đổi IP
     (DHCP) hoặc máy Master ở mạng khác, đổi thành `pi4-tdbao.local` hoặc IP
     Tailscale `100.116.157.59`.
   - `slave/chuong_trinh_slave_pi.py`: `MASTER_IP` đã điền sẵn `192.168.44.206`
     (máy tính đã dùng để test thực tế 2026-09-14). Nếu đổi sang máy khác làm
     Master, đổi lại IP này cho đúng máy đó.
   - Cổng UDP mặc định: Slave→Master là `6001`, Master→Slave là `6002` (2 file
     đã khớp nhau sẵn, chỉ cần đổi cả 2 nếu muốn đổi cổng).
2. **ThingSpeak:** điền `THINGSPEAK_CHANNEL_ID` + `THINGSPEAK_WRITE_API_KEY`
   trong `master/chuong_trinh_master_pc.py` (channel dùng field1 = temperature,
   field2 = humidity) — để placeholder trong repo (public) vì key thật không
   nên commit lên GitHub công khai; đã test gửi thành công thực tế với
   channel riêng của nhóm trước khi để lại placeholder.
3. Copy `protocol.py` ra cùng thư mục với script tương ứng trên mỗi máy
   (Master trên PC, Slave trên Raspberry Pi) vì 2 máy không dùng chung ổ đĩa.

## Chạy

```bash
# Trên Raspberry Pi (Slave)
python3 chuong_trinh_slave_pi.py

# Trên máy tính (Master)
python3 chuong_trinh_master_pc.py
```
