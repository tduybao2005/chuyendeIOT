# Docker — chạy CT1 (Web) trong container   (+2 điểm)

Đề ghi `+2 Nếu dùng Docker`. Ở đây **Node-RED chạy trong container**, còn 4
chương trình Python (CT2–CT5) chạy native qua systemd.

## Vì sao không đóng gói luôn cả 4 chương trình Python

| | Trong Docker | Native + systemd |
|---|---|---|
| Truy cập GPIO / I2C | phải cấp `/dev/gpiochip0`, `/dev/i2c-1`, thường phải `privileged` | dùng thẳng, không cần quyền đặc biệt |
| Đọc DHT | DHT truyền bit theo **timing từng micro giây**; thêm một lớp ảo hoá là tỉ lệ đọc hụt tăng rõ | ổn định |
| Tự khởi động lại khi lỗi | `restart: always` | `Restart=always` + `RestartSec` + `StartLimitIntervalSec=0` |
| Bằng chứng cho đề bài | `docker ps` | `systemctl status`, `journalctl`, `ps -ef` |

Web không đụng phần cứng nên đóng gói thoải mái — lấy trọn +2 điểm mà không đánh
đổi độ tin cậy của phần đọc cảm biến, vốn là thứ đề chấm nặng nhất.

## Cài đặt Docker (đã làm sẵn trên `pi4-hnc`)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi      # đăng nhập lại để có hiệu lực
```

## Chạy

```bash
cd ~/iot_buoi6/docker

docker compose up -d            # dựng và chạy nền
docker compose ps               # xem trạng thái
docker compose logs -f          # xem log Node-RED
docker compose restart          # nạp lại flow sau khi chép flows.json mới
docker compose down             # dừng hẳn
```

Mở `http://<ip-pi>:1880/ui`.

## Tự khởi động khi bật nguồn

Hai điều kiện, phải đủ cả hai:

```bash
sudo systemctl enable docker      # docker tự lên khi boot
# + restart: unless-stopped       # đã khai trong docker-compose.yml
```

Kiểm tra:

```bash
systemctl is-enabled docker       # phải in ra: enabled
docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' iot_buoi6_web
                                  # phải in ra: unless-stopped
```

## Ba chi tiết trong `docker-compose.yml` dễ bỏ sót

**1. Múi giờ.** Container mặc định chạy giờ UTC. Không đặt `TZ=Asia/Ho_Chi_Minh`
thì tính năng **hẹn giờ relay lệch đúng 7 tiếng** — đặt lịch 18:00 sẽ chạy lúc
1 giờ sáng.

**2. Mount ra thư mục thật.** `/data` được mount ra `~/iot_buoi6/node-red-data`
thay vì dùng volume ẩn của Docker, để chép `flows.json` vào và sao lưu bằng lệnh
thường. `flows_cred.json` (mật khẩu đã mã hoá) cũng nằm ở đó.

**3. Giới hạn bộ nhớ 512 MB.** Pi 4 bản 2 GB; để Node-RED ăn hết RAM thì OOM
killer sẽ giết 4 chương trình Python — đúng lúc đang quay video minh chứng.

## Bằng chứng cho video

```bash
docker ps                                  # container đang chạy
docker compose logs --tail 30              # log Node-RED
systemctl is-enabled docker                # tự lên khi boot
docker stats --no-stream iot_buoi6_web     # RAM/CPU thực tế
```
