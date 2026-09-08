# Dashboard Node-RED - Buổi 5 (lớp thầy Kiến)

Dashboard HTML/CSS/JS tự viết (qua node `ui_template`), không dùng widget
dựng sẵn của `node-red-dashboard`. 1 channel ThingSpeak duy nhất — xem bảng
field và bảng chia giao thức ở `../README.md`.

## Cài đặt Node-RED (nếu Pi chưa có)

```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
node-red-stop 2>/dev/null; true
npm i -g --unsafe-perm node-red-dashboard@3.6.6 --prefix ~/.node-red
sudo systemctl enable nodered.service
sudo systemctl start nodered.service
```

## Điền placeholder trước khi import

Mở `flows.json`, tìm và thay các placeholder sau bằng giá trị thật (không
commit giá trị thật lên git):

| Placeholder | Giá trị | Xuất hiện ở node |
|---|---|---|
| `DIEN_CHANNEL_ID_CAM_BIEN_CUA_BAN` | Channel ID của channel **CẢM BIẾN** | `n_fn_prep_http` |
| `DIEN_READ_API_KEY_CAM_BIEN_CUA_BAN` | Read API Key của channel **CẢM BIẾN** | `n_fn_prep_http` |
| `DIEN_CHANNEL_ID_LENH_CUA_BAN` | Channel ID của channel **LỆNH** | `n_fn_prep_state`, `n_fn_prep_mqtt_cmd` |
| `DIEN_READ_API_KEY_LENH_CUA_BAN` | Read API Key của channel **LỆNH** | `n_fn_prep_state` |
| `DIEN_WRITE_API_KEY_LENH_CUA_BAN` | Write API Key của channel **LỆNH** | `n_fn_prep_http_cmd` |
| `DIEN_MQTT_CLIENT_ID_CUA_BAN` | MQTT Client ID (của channel LỆNH) | node cấu hình `bk5_mqtt_broker` |
| `DIEN_MQTT_USERNAME_CUA_BAN` | MQTT Username | node cấu hình `bk5_mqtt_broker` |
| `DIEN_MQTT_PASSWORD_CUA_BAN` | MQTT Password | node cấu hình `bk5_mqtt_broker` |

## Import flow

**Cách 1 - qua giao diện Node-RED editor:**
1. Mở `http://<ip-cua-pi>:1880`.
2. Menu (☰) → Import → dán nội dung `flows.json` đã điền placeholder thật.
3. Deploy.

**Cách 2 - qua Admin API:**
```bash
curl -X POST http://<ip-cua-pi>:1880/flows \
  -H "Content-Type: application/json" \
  -H "Node-RED-API-Version: v2" \
  -d "{\"flows\": $(cat flows.json)}"
```

Sau khi Deploy, mở dashboard tại `http://<ip-cua-pi>:1880/ui`.

## Kiến trúc flow (minh chứng giao thức bằng sơ đồ khối)

```
[inject 15s] -> [prep URL] -> [http request GET feeds.json] -> [parse] -> [ui_template]
                                                                                |
                                                                     (8 nút bấm, mỗi nút
                                                                      1 msg.topic riêng)
                                                                                v
                                                          [switch: phân loại theo giao thức]
                                                          /                                \
                          (auto/manual/led_on/buzzer_on)                      (led_off/buzzer_off/
                                       v                                        relay_on/relay_off)
                          [prep lệnh MQTT] -> [mqtt out]                                  v
                                                                       [prep lệnh HTTP] -> [http request POST]
                                                                                -> [kiểm tra kết quả, tự thử lại]
```

Node `switch` (`n_switch_protocol`) là bằng chứng trực quan nhất: 4 rule đầu
(`auto`, `manual`, `led_on`, `buzzer_on`) đi vào nhánh `mqtt out`; rule `else`
(gồm `led_off`, `buzzer_off`, `relay_on`, `relay_off`) đi vào nhánh
`http request`.

## Bố cục dashboard

Toàn bộ giao diện gói gọn trong **đúng 1 màn hình, không có thanh cuộn** (kể
cả trên iPad) - dùng đơn vị `vh`/`vw`/`clamp()` để co giãn cỡ chữ/khoảng cách
theo chiều cao màn hình, và `#bk-root` neo `position:fixed` phủ kín viewport
(bỏ qua cách tự tính chiều cao theo nội dung của thư viện masonry trong
node-red-dashboard).

- Card "Chế độ hoạt động": 2 nút Auto/Manual.
- Card "Thời gian hiện tại": đồng hồ + ngày (cập nhật mỗi giây, phía client).
- Card "Giá trị mới nhất từ Server": nhiệt độ, độ ẩm, điện áp, khoảng cách -
  giá trị lần cập nhật cuối cùng (đọc qua HTTP).
- Card "Điều khiển thiết bị": 3 hàng LED/Buzzer/Relay, mỗi hàng có badge
  ON/OFF + 2 nút Bật/Tắt gọn (giao thức MQTT/HTTP theo đúng bảng ở trên -
  không hiện nhãn trên giao diện, minh chứng xem trực tiếp trên sơ đồ khối
  Node-RED).
- 2 card đồ thị Nhiệt độ, Độ ẩm: có lưới giá trị min/giữa/max và bấm vào
  điểm để xem giá trị cụ thể (tự vẽ SVG, không dùng thư viện chart mặc định).

## Đã kiểm tra trên phần cứng thật (Raspberry Pi `pi4-tdbao`)

Xem log kiểm tra chi tiết trong báo cáo nộp kèm.
