# Hướng dẫn SSH vào Raspberry Pi từ máy Windows (cùng mạng LAN/Wi-Fi)

Áp dụng khi máy Windows và Raspberry Pi đang cắm chung 1 mạng (cùng Wi-Fi phòng lab, hoặc cùng switch/router).

## Bước 1: Tìm địa chỉ IP của Pi (thực hiện trực tiếp trên Pi, qua màn hình GUI)

Cắm màn hình/chuột/bàn phím vào Pi (hoặc dùng bộ có sẵn ở phòng lab), sau đó:

1. Mở **Terminal** trên desktop Raspberry Pi OS — click icon terminal (màn hình đen) trên thanh taskbar, hoặc bấm tổ hợp phím `Ctrl+Alt+T`.
2. Gõ lệnh:

```bash
hostname -I
```

Lệnh này in ra tất cả địa chỉ IP hiện tại của Pi, cách nhau bằng dấu cách (nếu Pi vừa nối Wi-Fi vừa nối dây LAN cùng lúc sẽ thấy 2 địa chỉ). Đây là cách nhanh và đơn giản nhất.

3. Nếu muốn xem chi tiết theo từng cổng mạng:

```bash
ip addr show wlan0   # nếu Pi đang dùng Wi-Fi
ip addr show eth0    # nếu Pi đang dùng dây mạng (Ethernet)
```

Tìm dòng có dạng `inet 192.168.x.x/24` — phần `192.168.x.x` chính là địa chỉ IP cần dùng.

> **Mẹo:** Nếu không muốn nhớ IP (IP có thể đổi mỗi lần Pi khởi động lại), có thể dùng tên máy dạng `<tên-may>.local` thay cho IP khi SSH (xem Bước 4). Xem tên máy bằng lệnh `hostname` (không có tham số) trên Pi. Cách này chỉ hoạt động nếu mạng lab hỗ trợ mDNS — nếu không được thì quay lại dùng IP.

## Bước 2: Đảm bảo Pi đã bật SSH

Trên Terminal của Pi, kiểm tra:

```bash
sudo raspi-config nonint get_ssh
```

Kết quả `0` nghĩa là SSH đã bật, `1` nghĩa là chưa bật. Nếu chưa bật, bật lên bằng:

```bash
sudo raspi-config nonint do_ssh 0
```

(hoặc mở `sudo raspi-config` → **Interface Options** → **SSH** → **Enable** bằng giao diện menu nếu muốn thao tác qua menu thay vì gõ lệnh).

## Bước 3: Chuẩn bị SSH client trên máy Windows

Windows 10 (bản 1809 trở lên) và Windows 11 đã có sẵn **OpenSSH Client** tích hợp sẵn trong hệ thống — thường không cần cài thêm phần mềm nào khác (không cần PuTTY).

Kiểm tra đã có sẵn chưa: mở **PowerShell** (bấm nút Start, gõ "PowerShell", Enter — không cần chạy quyền Administrator), rồi gõ:

```powershell
ssh
```

Nếu terminal hiện ra dòng hướng dẫn cách dùng lệnh `ssh` (usage) thì đã có sẵn, dùng được luôn, chuyển sang Bước 4.

Nếu báo lỗi kiểu `'ssh' is not recognized as an internal or external command`, cài bổ sung theo 1 trong 2 cách:

- **Qua giao diện:** Settings → Apps → Optional features → Add a feature → tìm **OpenSSH Client** → Install.
- **Qua PowerShell (mở với quyền Administrator):**

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

## Bước 4: Mở terminal trên Windows và chạy lệnh SSH

Mở **PowerShell**, **Windows Terminal**, hoặc **Command Prompt (cmd)** — cái nào cũng được, **không cần** mở quyền Administrator.

Gõ lệnh sau (thay `pi` bằng đúng username đăng nhập của Pi, thay IP bằng địa chỉ tìm được ở Bước 1):

```powershell
ssh pi@192.168.1.xx
```

Hoặc nếu dùng tên máy `.local` (xem mẹo ở Bước 1):

```powershell
ssh pi@ten-may-pi.local
```

Lần đầu kết nối tới một máy mới, terminal sẽ hỏi xác nhận fingerprint dạng:

```
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Gõ `yes` rồi Enter. Sau đó nhập mật khẩu của tài khoản Pi khi được hỏi `pi@192.168.1.xx's password:` — lưu ý khi gõ mật khẩu, terminal sẽ **không hiện ký tự hay dấu `*` nào cả**, đây là hành vi bình thường của SSH trên Linux, cứ gõ đúng rồi Enter.

Kết nối thành công, dấu nhắc lệnh sẽ đổi thành dạng `pi@<tên-máy>:~$` — lúc này đã ở trong Pi, gõ lệnh Linux bình thường.

## Xử lý sự cố thường gặp

| Lỗi | Nguyên nhân / Cách xử lý |
|---|---|
| `Could not resolve hostname ...local` | Mạng không hỗ trợ mDNS — chuyển sang dùng IP trực tiếp (Bước 1) thay vì tên `.local` |
| `Connection timed out` / `No route to host` | Windows và Pi không cùng mạng/subnet. Thử `ping <IP-cua-Pi>` từ PowerShell trước để kiểm tra kết nối mạng cơ bản |
| `Connection refused` | SSH server trên Pi chưa bật — quay lại Bước 2 |
| `Permission denied (publickey,password)` | Sai username hoặc sai mật khẩu — kiểm tra lại username (mặc định là `pi` nhưng có thể đã đổi), gõ lại mật khẩu cẩn thận |
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` | Pi từng có IP này trước đó với fingerprint khác (thường do cài lại hệ điều hành hoặc đổi thẻ nhớ) — nếu chắc chắn đúng là Pi của mình, xóa dòng cũ trong `C:\Users\<ten-user>\.ssh\known_hosts` tương ứng với IP đó rồi kết nối lại |
