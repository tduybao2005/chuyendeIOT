# Lưu đồ `apply_outputs()` — dòng 338

```mermaid
flowchart TD
    START([Bắt đầu]) --> MODE{"state['mode']<br/>== 'manual'?"}

    MODE -- "Có" --> MLED{"state['led_cmd']<br/>== true?"}
    MLED -- "Có" --> LEDON["led.on()"] --> MBUZ
    MLED -- "Không" --> LEDOFF["led.off()"] --> MBUZ
    MBUZ{"state['buzzer_cmd']<br/>== true?"}
    MBUZ -- "Có" --> BUZON["buzzer.on()"] --> MREL
    MBUZ -- "Không" --> BUZOFF["buzzer.off()"] --> MREL
    MREL{"state['relay_cmd']<br/>== true?"}
    MREL -- "Có" --> RELON["relay.on()"] --> ENDM([Kết thúc — return])
    MREL -- "Không" --> RELOFF["relay.off()"] --> ENDM

    MODE -- "Không (Auto)" --> HOUR["hour = giờ hệ thống hiện tại"]
    HOUR --> HCHK{"18 &le; hour &lt; 22?"}
    HCHK -- "Có" --> AUTOLEDON["led.on()"] --> TEMP
    HCHK -- "Không" --> AUTOLEDOFF["led.off()"] --> TEMP

    TEMP{"state['temp']<br/>có giá trị?"}
    TEMP -- "Không" --> HUMI
    TEMP -- "Có" --> TCHK{"temp &gt; 40?"}
    TCHK -- "Có" --> BUZON2["buzzer.on()"] --> HUMI
    TCHK -- "Không" --> TCHK2{"temp &lt; 30?"}
    TCHK2 -- "Có" --> BUZOFF2["buzzer.off()"] --> HUMI
    TCHK2 -- "Không (30-40)" --> KEEPB["giữ nguyên trạng thái Buzzer"] --> HUMI

    HUMI{"state['humi']<br/>có giá trị?"}
    HUMI -- "Không" --> ENDA([Kết thúc])
    HUMI -- "Có" --> HCHK2{"humi &gt; 70?"}
    HCHK2 -- "Có" --> RELON2["relay.on()"] --> ENDA
    HCHK2 -- "Không" --> HCHK3{"humi &lt; 40?"}
    HCHK3 -- "Có" --> RELOFF2["relay.off()"] --> ENDA
    HCHK3 -- "Không (40-70)" --> KEEPR["giữ nguyên trạng thái Relay"] --> ENDA
```

Đúng nguyên văn điều kiện đề bài (giữ nguyên từ buổi 5 lớp thầy Thanh): LED
sáng khung giờ cố định 18h-22h; Buzzer/Relay có **vùng đệm giữ nguyên**
(30-40°C cho Buzzer, 40-70% cho Relay) để tránh nhấp nháy liên tục quanh
ngưỡng.
