# Lưu đồ `send_to_thingspeak(**fields)` — dòng 510

```mermaid
flowchart TD
    START([Bắt đầu<br/>attempt = 0..2<br/>tối đa 3 lần thử]) --> LOOP{{"Với attempt<br/>= 0, 1, 2"}}
    LOOP --> POST["POST update.json<br/>{api_key, ...fields}"]
    POST --> EXC{"Lỗi mạng /<br/>JSON không hợp lệ?"}
    EXC -- "Có" --> LOGERR["In lỗi lần thử này<br/>result = 0"] --> CHKID
    EXC -- "Không" --> PARSE["result = response.json()"] --> CHKID{"result là dict<br/>VÀ có entry_id<br/>(khác 0/None)?"}

    CHKID -- "Có (thành công)" --> NETOK["note_network_ok()"] --> RETTRUE([Trả về True])
    CHKID -- "Không" --> LASTTRY{"Đây là<br/>lần thử cuối<br/>(attempt == 2)?"}
    LASTTRY -- "Chưa" --> WAIT["sleep(3 giây)<br/>(có thể đang trúng<br/>giới hạn 15s/lần ghi)"] --> LOOP
    LASTTRY -- "Rồi" --> FAIL["In: gửi thất bại<br/>sau nhiều lần thử"] --> NETFAIL["note_network_fail()"] --> RETFALSE([Trả về False])
```

**Lưu ý quan trọng:** ThingSpeak khi từ chối ghi (do chưa đủ ~15 giây kể từ
lần ghi trước lên **cùng 1 channel**) vẫn trả về **HTTP 200** nhưng nội dung
là số `0`, KHÔNG phải lỗi HTTP — nên `response.raise_for_status()` không đủ
để phát hiện, bắt buộc phải kiểm tra `entry_id` trong nội dung trả về.
