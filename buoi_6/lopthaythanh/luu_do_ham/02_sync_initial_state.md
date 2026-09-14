# Lưu đồ `sync_initial_state()` — dòng 443

Đọc trạng thái lệnh **hiện tại** (không phải lịch sử) ngay lúc chương trình
vừa khởi động/khởi động lại, để không bị "quên mất" chế độ Manual đã chọn từ
trước.

```mermaid
flowchart TD
    START([Bắt đầu]) --> TARGETS["4 field cần đồng bộ:<br/>Mode, LED, Buzzer, Relay"]
    TARGETS --> LOOP{{"Với mỗi field<br/>trong 4 field trên"}}

    LOOP --> GET["GET /channels/&lt;id&gt;/fields/&lt;n&gt;/last.json<br/>(giá trị CUỐI CÙNG của field này,<br/>bất kể cũ bao lâu)"]
    GET --> ERR{"Lỗi mạng /<br/>JSON không hợp lệ?"}
    ERR -- "Có" --> SKIP["In lỗi, bỏ qua field này<br/>(giữ giá trị mặc định)"] --> LOOP
    ERR -- "Không" --> EMPTY{"Giá trị là<br/>None / '' / -1 / '-1'?<br/>(field chưa từng có dữ liệu)"}
    EMPTY -- "Có" --> LOOP
    EMPTY -- "Không" --> ISMODE{"Field này<br/>là Mode?"}
    ISMODE -- "Có" --> SETMODE["state['mode'] =<br/>'manual' nếu to_bool(value)<br/>ngược lại 'auto'"] --> LOOP
    ISMODE -- "Không (LED/Buzzer/Relay)" --> SETVAL["state[key] = to_bool(value)"] --> LOOP

    LOOP -- "Hết 4 field" --> PRINT["In ra: trạng thái ban đầu<br/>mode / led / buzzer / relay"]
    PRINT --> APPLY["apply_outputs()<br/>(áp trạng thái vừa đồng bộ<br/>ra GPIO thật ngay)"]
    APPLY --> END([Kết thúc])
```

**Vì sao không dùng `poll_http_commands()` cho việc này?** Hàm đó chỉ quét
30 bản ghi gần nhất trên channel LỆNH; vì Pi ghi cảm biến (channel khác) mỗi
20s không ảnh hưởng ở đây, nhưng nếu một lệnh (vd chọn Manual) đã được bấm từ
30 phút trước thì nó đã "trôi" ra ngoài 30 bản ghi gần nhất — Pi sẽ hiểu nhầm
là chưa có lệnh nào và quay về mặc định Auto. `sync_initial_state()` dùng
API riêng của ThingSpeak (`fields/<n>/last.json`) trả về đúng giá trị cuối
cùng của từng field, bất kể cũ bao lâu, nên không bị lỗi này.
