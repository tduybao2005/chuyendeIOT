# CT1 — Ba luồng của flow Node-RED

File: [`../node-red/flows.json`](../node-red/flows.json) · giao diện ở
[`../node-red/dashboard_template.html`](../node-red/dashboard_template.html)

> *"Chương trình 1 Giao diện Web node-red trên raspberry. Có 6 nút nhấn để điều
> khiển 3 LED, có giao diện hiển thị giá trị nhiệt độ, độ ẩm, trạng thái LED."*

## Luồng 1 · Đọc cảm biến (mỗi 20s)

```mermaid
flowchart LR
    A["inject<br/>mỗi 20s"] --> B["dựng URL<br/>channel CẢM BIẾN"]
    B --> C["GET feeds.json<br/>results=30"]
    C --> D{"HTTP 200?"}
    D -- "không" --> E["ok=false<br/>báo 'mất kết nối'"]
    D -- "có" --> F["Đổi 30 bản ghi thành<br/>mảng {nhiệt độ, độ ẩm, mốc}<br/>field thiếu → null"]
    F --> G["Quét ngược tìm<br/>giá trị mới nhất<br/>còn khác null"]
    G --> H["dashboard<br/>vẽ 2 đồ thị SVG<br/>+ 2 thẻ số"]
    E --> H

    classDef io fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    class C io;
```

Giữ `null` thay vì đổi thành 0: đồ thị bỏ qua điểm null, còn đổi thành 0 thì
đường vẽ tụt xuống đáy thành hình răng cưa.

## Luồng 2 · Đọc trạng thái lệnh (mỗi 5s)

```mermaid
flowchart LR
    A["inject<br/>mỗi 5s"] --> B["dựng URL<br/>channel LỆNH"]
    B --> C["GET feeds.json<br/>results=10"]
    C --> D["Quét NGƯỢC từng field<br/>lấy giá trị không null đầu tiên"]
    D --> E["dashboard"]
    E --> F{"Hàng đợi<br/>đang gửi?"}
    F -- "có" --> G["BỎ QUA<br/>(ghi đè lúc này sẽ làm nút<br/>vừa bấm nhảy ngược về cũ)"]
    F -- "không" --> H["Đồng bộ 6 nút<br/>với giá trị thật trên server"]

    classDef io fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    class C io;
```

Đây là cơ chế tự chữa: mở Web trên máy thứ hai, bấm F5, hay Node-RED vừa khởi
động lại — sau tối đa 5 giây giao diện tự khớp với trạng thái thật.

## Luồng 3 · Ghi lệnh (một nút, khoá 15 giây)

```mermaid
flowchart TB
    U(["Người dùng bấm nút"]) --> D["Dashboard:<br/>khoá ngay 10 nút<br/>+ đổi màu (lạc quan)"]
    D --> Q["ĐIỀU PHỐI GHI"]
    T["inject nhịp 1s<br/>(chỉ để đếm ngược)"] --> Q

    Q --> CHK{"Đang khoá?"}
    CHK -- "có" --> REJ["Từ chối, báo còn N giây<br/>(chốt chặn cuối — nút<br/>lẽ ra đã disable rồi)"]
    CHK -- "không" --> KEY{"Đã điền<br/>Write key?"}
    KEY -- "chưa" --> ERR["Báo lỗi cấu hình"]
    KEY -- "rồi" --> POST["POST update.json NGAY<br/>cả 6 field cùng lúc<br/>ghi log mốc ms"]

    POST --> RES{"entry_id<br/>&gt; 0?"}
    RES -- "có" --> OK["Khoá 15 giây<br/>ghi log 'GHI THANH CONG'<br/>+ độ trễ POST"]
    RES -- "không" --> FAIL["Khoá 5 giây<br/>ghi log lý do<br/>(bấm lại ngay cũng bị<br/>từ chối tiếp)"]

    OK --> BACK["dashboard: bắt đầu đếm ngược"]
    FAIL --> BACK2["dashboard: báo lỗi,<br/>xoá mốc đã-đồng-bộ để<br/>luồng 2 kéo về giá trị thật"]

    classDef ok  fill:#064e3b,stroke:#34d399,color:#e9f0fa;
    classDef bad fill:#4c1d24,stroke:#f87171,color:#e9f0fa;
    classDef io  fill:#1e3a5f,stroke:#38bdf8,color:#e9f0fa;
    class OK,BACK ok;
    class FAIL,REJ,ERR bad;
    class POST io;
```

**Vì sao POST bắn ngay chứ không chờ nhịp tick:** ngân sách "bấm → Pi xử lý" chỉ
có 2 giây, mà chờ nhịp 1 giây là mất oan nửa ngân sách. Nhịp tick ở đây chỉ để
cập nhật đồng hồ đếm ngược trên giao diện.

**Vì sao gửi cả 6 field dù chỉ đổi 1 nút:** dòng feed mới nhất trên ThingSpeak
luôn đầy đủ → Pi chỉ cần 1 request là đọc được toàn bộ trạng thái, thay vì 6.
