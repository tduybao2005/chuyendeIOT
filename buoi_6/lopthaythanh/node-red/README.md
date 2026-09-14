# Buổi 6 - Web bằng Node-RED

Dashboard chạy ngay trên Raspberry Pi (cùng máy với
`../raspberry/chuong_trinh_pi.py`), giao diện là **HTML/CSS/JS tự viết**
(không dùng widget dựng sẵn của `node-red-dashboard`) nhúng qua **một** node
`ui_template`.

## Cài đặt

```bash
# Node-RED v4 (tuong thich Node.js v20 co san tren Pi; v5 can Node >= 22.9)
sudo npm install -g --unsafe-perm node-red@4

# Chay lan dau de tao ~/.node-red, roi cai them dashboard
node-red &                 # Ctrl+C khi thay "Server now running"
cd ~/.node-red && npm install node-red-dashboard@3.6.6
```

## Nạp flow

```bash
# sao luu flow dang co truoc khi ghi de
cp ~/.node-red/flows.json ~/.node-red/flows.json.bak.$(date +%s)

cp flows.json ~/.node-red/flows.json
sudo systemctl restart nodered
```

Hoặc nạp qua editor: mở `http://<ip-cua-pi>:1880/` → menu ☰ → Import → dán nội
dung `flows.json` → Deploy.

### Nhập mật khẩu MQTT

Node-RED lưu user/password của node `mqtt-broker` trong `flows_cred.json` (đã
mã hoá), **không nằm trong `flows.json`**. Sau khi nạp flow phải nhập tay:

1. Mở editor, nháy đúp node **`ThingSpeak MQTT (channel LENH)`**.
2. Tab **Security**: Username `DIEN_MQTT_CLIENT_ID_CUA_BAN`,
   Password `DIEN_MQTT_PASSWORD_CUA_BAN`.
3. Done → **Deploy**.

Client ID (`DIEN_MQTT_CLIENT_ID_CUA_BAN`) đã có sẵn trong `flows.json`.

Kiểm tra đã kết nối: node `mqtt out` hiện chấm xanh **connected**, hoặc

```bash
sudo journalctl -u nodered | grep "Connected to broker"
```

## Sơ đồ khối

Flow chia 2 tầng, mỗi cụm nằm trong một khung nhóm có tên:

```
TANG 1 (doc du lieu, chay trai -> phai)
  1 · DOC CAM BIEN        [inject 15s] -> [prep URL] -> [GET] -> [parse] --\
  2 · DOC TRANG THAI      [inject 5s]  -> [prep URL] -> [GET] -> [parse] --+--> 3 · DASHBOARD
                                                                           |
TANG 2 (gui lenh)                                                          |
  4 · DINH TUYEN     [switch] <---------------------------------------------/
       ├─ auto/manual --> 5a · [prep MQTT] -> [mqtt out]
       └─ else        --> 5b · [prep HTTP] -> [POST update.json] -> [check]
                                                    ^                  |
                                                    └─── [doi 3s] <────┘
```

- **Nhóm 5a — 2 nút MQTT**: Auto, Manual. Publish lên
  `channels/DIEN_CHANNEL_ID_LENH_CUA_BAN/publish/fields/field4`.
- **Nhóm 5b — 6 nút HTTP**: LED / Relay / Buzzer, Bật và Tắt. `POST
  update.json` lên channel LỆNH, tự thử lại tối đa 10 lần × 3s nếu bị
  ThingSpeak từ chối do giới hạn ~17s/lần ghi.

Dashboard vừa là **nguồn phát** lệnh (`scope.send` khi bấm nút) vừa là **đích
nhận** dữ liệu, nên có một dây phản hồi từ nhóm 5b quay về — đó là vòng lặp
bình thường của flow, không phải nối nhầm.

## Giao diện

Nền tối, 2 cột, neo `position:fixed` để luôn gói đúng **một khung hình, không
có thanh cuộn** (yêu cầu của đề khi quay video trên iPad).

| Yêu cầu của đề mức độ 3 | Chỗ đáp ứng |
|---|---|
| Nút chọn Auto / Manual | Thanh 2 nút ở panel *CHẾ ĐỘ HOẠT ĐỘNG* |
| Nút bật/tắt LED (tự quyết số lượng) | 6 nút Bật/Tắt cho LED, Buzzer, Relay |
| Đồ thị nhiệt độ và độ ẩm | 2 biểu đồ SVG xếp dọc ở cột phải, bấm vào điểm xem giá trị |
| Biểu tượng trạng thái LED/Buzzer/Relay | Icon 💡 🔊 🔌 + nhãn ON/OFF + viền trái đổi màu |
| Biểu tượng chế độ Auto/Manual | Pill 🤖 AUTO / ✋ MANUAL trên thanh tiêu đề |
| Cửa sổ nhiệt độ, độ ẩm lần cập nhật cuối | 4 ô lớn (nhiệt độ, độ ẩm, điện áp, khoảng cách) |
| Cửa sổ thời gian hiện tại | Đồng hồ góc phải trên, cập nhật mỗi giây |

Chống bấm chồng lệnh: khi đang chờ một lệnh xử lý xong thì **cả 8 nút bị
khoá** (`cmdPending`), vì cả 8 nút cùng ghi lên một channel có giới hạn
~17s/lần ghi. Nhánh MQTT tự mở khoá sau 3s (publish là fire-and-forget, không
có xác nhận); nhánh HTTP mở khoá ngay khi nhận `cmd_ok`.

## Đối chiếu độ trễ

Cả hai phía đều in mốc thời gian có mili giây, dùng chung đồng hồ của Pi:

- **Node-RED** (`sudo journalctl -u nodered -f`): `GUI LENH MQTT` (lúc gửi) và
  `GUI THANH CONG len ThingSpeak` (lúc xác nhận ghi thành công).
- **Pi** (`sudo journalctl -u iot-buoi6 -f`): `NHAN LENH` và `DA AP DUNG XONG`.

Độ trễ = mốc `DA AP DUNG XONG` trừ mốc gửi tương ứng.
