# Lưu đồ các hàm phụ trợ (một dòng logic, dùng chung nhiều nơi)

`log_event()` (127), `is_valid()` (139), `to_bool()` (370),
`note_sensor_ok()` (197), `note_network_ok()` (209).

```mermaid
flowchart TD
    A0([log_event message]) --> A1["now_str = giờ:phút:giây.mili giây<br/>hiện tại"]
    A1 --> A2["print '[now_str] message'"]
    A2 --> A3([Kết thúc])

    B0([is_valid value, min, max]) --> B1{"value là None?"}
    B1 -- "Có" --> B2([Trả về False])
    B1 -- "Không" --> B3{"min &le; value &le; max?"}
    B3 -- "Có" --> B4([Trả về True])
    B3 -- "Không" --> B2

    C0([to_bool value]) --> C1{"ép value<br/>sang float<br/>thành công?"}
    C1 -- "Không (lỗi kiểu)" --> C2([Trả về False])
    C1 -- "Có" --> C3{"float(value) &ge; 1?"}
    C3 -- "Có" --> C4([Trả về True])
    C3 -- "Không" --> C2

    D0([note_sensor_ok]) --> D1["health['sensor_fail'] = 0"] --> D2([Kết thúc])
    E0([note_network_ok]) --> E1["health['network_fail'] = 0"] --> E2([Kết thúc])
```

**Vì sao `to_bool` dùng `>= 1` thay vì so sánh `== 1`?** ThingSpeak trả field
dạng chuỗi (`"1"`, `"0"`, có khi `"1.0"`) — ép sang `float` rồi so sánh
`>= 1` chịu được cả các biến thể định dạng số này, tránh so sánh chuỗi trực
tiếp dễ sai (`"1" == 1` là `False` trong Python).
