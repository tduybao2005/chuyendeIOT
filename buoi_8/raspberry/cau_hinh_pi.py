"""
CAU HINH CHUONG TRINH RASPBERRY PI - buoi 8 muc do 3.

=========================================================================
CHI CAN SUA DUY NHAT FILE NAY khi doi dia chi server hay doi chan cam.
=========================================================================

=========================================================================
SO DO NOI DAY (Grove Base Hat tren Raspberry Pi 4)
=========================================================================

    Linh kien              Cong Grove      Chan BCM      Ghi chu
    ---------------------------------------------------------------------
    Cam bien DHT11         D5              GPIO5         nhiet do + do am
    LED do                 D16             GPIO16        bao "NONG"  (>=32 C)
    LED vang               D22             GPIO22        bao "AM"    (28-32 C)
    LED xanh               D24             GPIO24        bao "MAT"   (<28 C)

Bo chan nay lay theo buoi_7/slave/chuong_trinh_slave_pi.py - da chay thuc te
tren Pi 'pi4-tdbao' ngay 2026-09-14, khong phai doan tu so do.

CANH BAO NEU DUNG CON PI KHAC: buoi_6/lopthaykien chay tren 'pi4-hnc' voi bo
chan HOAN TOAN KHAC (DHT o D22, LED o D5/D16/D18). Cam theo so do buoi 6 roi
chay file nay thi cam bien va den deu khong hoat dong ma khong bao loi ro
rang. Kiem tra ky dang cam con nao truoc khi chay.

Cong Grove D5 thuc ra la mot cong DOI (co ca GPIO5 va GPIO6), D16 co ca
GPIO16 va GPIO17... Thu vien chi dung chan DAU cua moi cong, dung so ghi
tren cong la dung.
"""

import os

# =========================================================================
# 1. SERVER  --  SUA HAI DONG NAY TRUOC KHI CHAY
# =========================================================================

# Dia chi server FastAPI dang chay tren MAY TINH.
#
# CACH LAY DIA CHI: chay `hostname -I` tren may tinh chay server, lay dia chi
# dau tien (dang 192.168.x.x). Pi va may tinh phai CUNG MOT MANG Wi-Fi/LAN.
#
# KHONG DUNG 127.0.0.1 hay localhost o day: voi Pi thi 'localhost' la chinh
# no, request se khong bao gio ra khoi Pi.
#
# May tinh dung lam server buoi 7 (2026-09-14) co IP LAN 192.168.44.206 -
# neu van con o mang do thi dien lai chinh no. IP cap bang DHCP nen co the
# doi sau moi lan khoi dong lai router.
SERVER_URL = os.environ.get("IOT_BUOI8_SERVER", "http://192.168.1.100:8000")

# API_KEY - phai TRUNG voi API_KEY trong buoi_8/server/.env
#
# DOC TU BIEN MOI TRUONG, KHONG VIET THANG VAO DAY: repo nay cong khai tren
# GitHub, viet thang vao file .py la day khoa len mang. Tren Pi thi dat bang:
#
#     echo 'export IOT_BUOI8_API_KEY="khoa-that-cua-ban"' >> ~/.bashrc
#     source ~/.bashrc
#
# Neu chay bang systemd thi dat trong Environment= cua file .service.
API_KEY = os.environ.get("IOT_BUOI8_API_KEY", "")

# Ten thiet bi - de bai bat "du lieu luu vao Database phai co ... ten thiet
# bi gui len". Dat mac dinh la ten may (hostname) de khi co nhieu Pi cung gui
# len mot server thi tu phan biet duoc, khong phai sua tay tung con.
TEN_THIET_BI = os.environ.get("IOT_BUOI8_TEN_THIET_BI", os.uname().nodename)

# =========================================================================
# 2. CHAN GPIO  (danh so BCM, dung so in tren cong Grove Base Hat)
# =========================================================================
CHAN_DHT = 5           # cong D5  - cam bien nhiet do / do am
LOAI_DHT = "11"        # "11" cho DHT11, "22" cho DHT22 - PHAI khop module
                       #
                       # DAT SAI LOAI KHONG BAO LOI, CHI RA SO VO NGHIA:
                       # DHT22 ma hoa gia tri x10 tren 16 bit, con trinh doc
                       # DHT11 chi lay byte cao. Thuc te 26.4 C / 91.9 % ->
                       # doc kieu DHT11 se ra 1 C va 3 %. Da gap dung loi nay
                       # o buoi 6: cam bien van "doc duoc" nhung ra so vo
                       # nghia. cam_bien_hop_le() trong giao_tiep.py chan
                       # duoc, nhung sua cho dung ngay tu day van hon.
CHAN_LED_DO = 16       # cong D16 - LED1, bao muc NONG
CHAN_LED_VANG = 22     # cong D22 - LED2, bao muc AM
CHAN_LED_XANH = 24     # cong D24 - LED3, bao muc MAT

# =========================================================================
# 3. NHIP THOI GIAN (giay)
# =========================================================================
# Moi chu ky: doc cam bien -> bat den -> gui len server -> doc nguoc ve -> in.
#
# VI SAO 5 GIAY, KHONG PHAI 1 GIAY:
#   - DHT11 chi lay mau moi ~2 giay mot lan, goi nhanh hon thi no tra lai
#     dung gia tri cu -> ton request ma khong co so lieu moi.
#   - Moi chu ky ton 2 luot goi mang (1 gui + 1 doc). Nhip 1 giay -> 172
#     nghin luot/ngay, goi free M0 cua Atlas se cham tran.
#   - Terminal in 5 giay mot dong thi doc kip; 1 giay mot dong thi troi qua
#     qua nhanh, khong theo doi duoc luc demo.
NHIP_GUI = 5

# Timeout cho moi request HTTP (giay).
#
# Phai NHO HON NHIP_GUI: neu de lon hon, mot request treo se an sang chu ky
# ke tiep va nhip gui bi troi dan. 4 giay van du rong cho duong LAN.
HTTP_TIMEOUT = 4

# Cu moi bao nhieu chu ky thi doc ve N ban ghi gan nhat de in bang tong ket.
# De bai: "co the chon doc N du lieu gan nhat" - day la cho minh hoa no.
SO_CHU_KY_MOI_LAN_XEM_LICH_SU = 6      # 6 x 5s = 30 giay mot lan
SO_BAN_GHI_XEM_LICH_SU = 5

# =========================================================================
# 4. TU PHUC HOI
#
# Loi le te thi bo qua va chay tiep (cam bien doc hut, mang chop chop la
# chuyen thuong ngay). Nhung loi LIEN TIEP qua nguong thi chay tiep vo
# nghia: chuong trinh thoat ma 1, systemd (Restart=always) dung lai mot tien
# trinh hoan toan sach. Moi lan thanh cong deu dua bo dem ve 0 nen chuoi loi
# bi ngat quang khong bao gio cong don den nguong.
# =========================================================================
NGUONG_LOI_CAM_BIEN = 20   # 20 lan lien tiep khong doc duoc cam bien
NGUONG_LOI_MANG = 15       # 15 lan lien tiep goi server that bai (~75 giay)
