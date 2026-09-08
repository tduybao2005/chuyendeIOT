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
| `DIEN_CHANNEL_ID_CUA_BAN` | Channel ID (dùng chung 1 channel) | `n_fn_prep_http`, `n_fn_prep_mqtt_cmd` |
| `DIEN_READ_API_KEY_CUA_BAN` | Read API Key | `n_fn_prep_http` |
| `DIEN_WRITE_API_KEY_CUA_BAN` | Write API Key | `n_fn_prep_http_cmd` |
| `DIEN_MQTT_CLIENT_ID_CUA_BAN` | MQTT Client ID | node cấu hình `bk5_mqtt_broker` |
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

- Card "Chế độ hoạt động": 2 nút Auto/Manual (nhãn MQTT).
- Card "Thời gian hiện tại": đồng hồ + ngày (cập nhật mỗi giây, phía client).
- Card "Giá trị mới nhất từ Server": nhiệt độ, độ ẩm, điện áp, khoảng cách -
  giá trị lần cập nhật cuối cùng (đọc qua HTTP).
- Card "Điều khiển thiết bị": 3 hàng LED/Buzzer/Relay, mỗi hàng 2 nút Bật/Tắt,
  mỗi nút có nhãn MQTT/HTTP riêng theo đúng bảng chia giao thức.
- 2 card đồ thị Nhiệt độ, Độ ẩm: có lưới giá trị min/giữa/max và bấm vào
  điểm để xem giá trị cụ thể (tự vẽ SVG, không dùng thư viện chart mặc định).

## Đã kiểm tra trên phần cứng thật (Raspberry Pi `pi4-tdbao`)

Xem log kiểm tra chi tiết trong báo cáo nộp kèm.
