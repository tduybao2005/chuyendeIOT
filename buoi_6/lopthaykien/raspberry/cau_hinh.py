"""
Cau hinh chung cho CA 4 chuong trinh Python cua buoi 6 - muc 15 diem.

=========================================================================
CHI CAN SUA DUY NHAT FILE NAY khi doi channel / API key ThingSpeak.
Bon chuong trinh ct2/ct3/ct4/ct5 deu import tu day, khong chuong trinh nao
tu chua API key rieng - tranh sua mot cho quen mot cho.
=========================================================================

VI SAO PHAI TACH 2 CHANNEL THINGSPEAK
    ThingSpeak (goi mien phi) chi cho GHI 1 lan moi ~15-17 giay tren CUNG
    MOT channel. Chuong trinh 2 phai ghi trung binh cam bien moi 20 giay
    (yeu cau de bai). Neu de lenh nut nhan chung channel do thi moi chu ky
    20s chi con vai giay trong cho lenh -> bam nut bi ThingSpeak tu choi
    lien tuc. Tach ra thi channel LENH luon ranh cho Web ghi.

SO DO FIELD

    CHANNEL A - CAM BIEN   (CT2 ghi moi 20s, Web doc de ve do thi)
        field1  Nhiet do trung binh 20s      (o C)
        field2  Do am trung binh 20s         (%)

    CHANNEL B - LENH       (Web ghi, CT3/CT4/CT5 doc)
        field1  LED 1          0 = tat, 1 = bat
        field2  LED 2          0 = tat, 1 = bat
        field3  LED 3          0 = tat, 1 = bat
        field4  Relay (tay)    0 = tat, 1 = bat
        field5  Text 16x2      "dong1|dong2", moi dong toi da 16 ky tu
        field6  Lich hen gio   "<bat_lich>|<gio_bat>|<gio_tat>"
                               vi du "1|18:00|22:00" = bat lich, ON 18h, OFF 22h
                               "0|18:00|22:00"        = tat lich, relay theo field4
"""

# =========================================================================
# 1. THINGSPEAK  --  DIEN THONG TIN THAT CUA BAN VAO 6 DONG DUOI DAY
# =========================================================================
# Channel A - CAM BIEN: CT2 chi GHI nen chi can Write key.
#                       (Read key chi can neu muon tu kiem tra bang curl.)
CHANNEL_CAM_BIEN_ID = ""          # vi du "3486158"
CHANNEL_CAM_BIEN_WRITE_KEY = ""   # vi du "4SKAEBDEVNTK4TRU"
CHANNEL_CAM_BIEN_READ_KEY = ""

# Channel B - LENH: CT3/CT4/CT5 chi DOC nen chi can Read key.
#                   (Write key la de Node-RED dung - khai bao ben Node-RED.)
CHANNEL_LENH_ID = ""              # vi du "3486161"
CHANNEL_LENH_READ_KEY = ""
CHANNEL_LENH_WRITE_KEY = ""

# Duong dan API (khong can sua)
URL_GHI = "https://api.thingspeak.com/update.json"
URL_DOC_LENH = f"https://api.thingspeak.com/channels/{CHANNEL_LENH_ID}/feeds.json"

# So ban ghi gan nhat lay ve moi lan doc lenh.
#
# VI SAO CAN > 1: moi lan Web ghi, ThingSpeak tao 1 DONG moi; field nao khong
# gui trong lan do se la null tren dong do. Quet nguoc 10 dong roi lay gia tri
# KHONG null dau tien cho TUNG field thi du kien moi truong hop - ke ca khi ai
# do ghi tay 1 field le bang curl.
#
# Channel LENH chi duoc ghi khi nguoi dung bam nut (khong bi CT2 ghi cam bien
# lam troi mat lich su) nen 10 dong da bao quat duoc 10 lenh gan nhat.
SO_BAN_GHI_DOC_VE = 10

# Timeout cho moi request HTTP (giay)
HTTP_TIMEOUT = 8

# =========================================================================
# 2. CHAN GPIO  (danh so theo chuan BCM, dung so in tren cong Grove Base Hat)
# =========================================================================
CHAN_DHT = 22          # cong D22 - cam bien nhiet do / do am
LOAI_DHT = "22"        # "11" cho DHT11, "22" cho DHT22 - sua cho khop module
                       #
                       # DAT SAI LOAI KHONG BAO LOI, CHI RA SO VO NGHIA:
                       # DHT22 ma hoa gia tri x10 tren 16 BIT, con trinh
                       # doc DHT11 chi lay BYTE CAO. Thuc te 26.4 C /
                       # 91.9 % -> DHT22 gui temp=264=0x0108, humi=919=
                       # 0x0397; doc kieu DHT11 se ra t=1, h=3. Da gap
                       # dung loi nay khi test: cam bien van "doc duoc"
                       # nhung ra 1 C va 3 %, bi dai hop le loai het.
CHAN_LED_1 = 5         # cong D5
CHAN_LED_2 = 16        # cong D16
CHAN_LED_3 = 18        # cong D18
CHAN_RELAY = 24        # cong D24
# LCD 16x2 JHD1802 dung I2C-1 (0x3E hien thi + 0x62 den nen), khong can khai chan

# =========================================================================
# 3. NHIP THOI GIAN (giay)
# =========================================================================
CT2_NHIP_DOC = 1       # de bai: doc nhiet do / do am moi 1 giay
CT2_NHIP_GUI = 20      # de bai: gui trung binh moi 20 giay

# Ba chuong trinh CT3/CT4/CT5 cung doc CHUNG channel LENH. Dat nhip khac nhau
# theo muc do can phan hoi nhanh, vua du nhanh vua do so luot goi API.
#
# ===========================================================================
# VI SAO CT3 PHAI LA 0.5 GIAY, KHONG PHAI 1 GIAY
# ===========================================================================
# Rang buoc: tu luc NGUOI DUNG BAM NUT tren Web den luc Pi bat den phai duoi
# 2 giay. Chia nho quang duong do:
#
#     Web POST len ThingSpeak .................. 0.3 - 0.9 s
#     Cho den vong poll ke tiep cua CT3 ........ toi da = nhip poll
#     GET cua CT3 di va ve ..................... 0.3 - 0.5 s
#     led.on() ................................. ~0 s
#
#   Nhip 1.0s  ->  xau nhat 0.9 + 1.0 + 0.5 = 2.4 s   VUOT MOC
#   Nhip 0.5s  ->  xau nhat 0.9 + 0.5 + 0.5 = 1.9 s   DAT
#
# Doi lai la so luot goi API tang gap doi (~172k/ngay). ThingSpeak khong tinh
# luot DOC vao han muc 3 trieu message/nam (han muc do chi dem luot GHI) nen
# chap nhan duoc.
#
# LUU Y: phai la CHU KY co dinh 0.5s (VongLapDinhNhip tru di thoi gian
# request), khong phai sleep(0.5) sau moi request. Neu chi sleep thi chu ky
# that = 0.5 + 0.4 = 0.9s va moc 2 giay lai vo.
# ===========================================================================
CT3_NHIP_DOC = 0.5     # LED - rang buoc <2s tu luc bam nut
CT4_NHIP_DOC = 2       # relay + lich hen gio, cham 2s khong anh huong gi
CT5_NHIP_DOC = 5       # text tren LCD, nguoi doc khong can nhanh hon 5s

# Web tu khoa 8 nut trong 15 giay sau moi lan gui thanh cong, dam bao khong
# bao gio cham gioi han ghi cua ThingSpeak. Hang so nay phai khop voi
# 'khoaSauKhiGhiMs' trong node CAU HINH THINGSPEAK ben Node-RED.
KHOA_NUT_SAU_KHI_GHI = 15

# =========================================================================
# 4. DAI GIA TRI HOP LE CUA CAM BIEN
#
# De bai: "du lieu cam bien bi loi thi KHONG duoc gui len Server ma phai doc
# lai". Gia tri ngoai dai duoi day bi loai ngay tai cho, khong vao trung binh.
# =========================================================================
DAI_NHIET_DO = (0, 100)   # o C
DAI_DO_AM = (20, 95)      # %

# =========================================================================
# 5. TU PHUC HOI  (yeu cau de bai: "tu reset khi loi cam bien, rot mang")
#
# Loi le te thi try/except cho chay tiep. Nhung neu loi LIEN TIEP qua nguong
# (cam bien tuot day, mat Wi-Fi lau) thi chay tiep vo nghia: chuong trinh thoat
# ma 1 de systemd (Restart=always) dung lai mot tien trinh hoan toan sach.
# Moi lan thanh cong deu reset bo dem ve 0 -> chi loi LIEN TIEP moi tinh.
# =========================================================================
NGUONG_LOI_CAM_BIEN = 30   # 30 lan lien tiep khong doc duoc cam bien (~30 giay)
NGUONG_LOI_MANG = 20       # 20 lan lien tiep goi ThingSpeak that bai

# =========================================================================
# 6. LOGFILE - DUNG HAI FILE, MOI FILE MOT LOAI DU LIEU
#
# De bai nhac logfile dung 2 lan, deu o so it:
#   Muc do 3 : "Co logfile ghi lai cac hoat dong tren Raspberry."
#   Nang cao : "Co logfile rieng; chuong trinh cung tu khoi dong..."
#
# Nen chi lam DUNG HAI file, va moi file chi chua dung loai du lieu cua no -
# khong tron lan thu khac vao:
#
#   LOG_1_NUT_NHAN  <- CT3 ghi. Du lieu NUT NHAN doc ve tu server (led1/2/3)
#                      va trang thai 3 LED sau khi ap dung.
#   LOG_2_TEXT      <- CT5 ghi. Du lieu TEXT nguoi dung go tren Web, doc ve
#                      tu server, dem hien len LCD 16x2.
#
# CT2 (cam bien) va CT4 (relay) KHONG co logfile: de bai chi yeu cau CT2 "gui
# len server gia tri trung binh moi 20s", khong yeu cau luu lai vao file. Moi
# hoat dong cua hai chuong trinh do van xem duoc qua journal cua systemd:
#       journalctl -u iot-ct2-cambien -f
#       journalctl -u iot-ct4-relay -f
#
# Ca 4 chuong trinh deu ghi phan VAN HANH (khoi dong, loi cam bien, rot mang,
# ly do tu khoi dong lai) ra journal - khong ban vao 2 file tren.
# =========================================================================
import os

THU_MUC_LOG = os.environ.get(
    "IOT_BUOI6_LOG_DIR",
    os.path.join(os.path.expanduser("~"), "iot_buoi6", "logs"),
)
LOG_1_NUT_NHAN = "logfile1_nut_nhan.log"   # CT3 ghi
LOG_2_TEXT = "logfile2_text_16x2.log"      # CT5 ghi

LOG_KICH_THUOC_TOI_DA = 2 * 1024 * 1024   # 2 MB moi file
LOG_SO_FILE_GIU_LAI = 5                   # giu 5 file cu -> toi da ~12 MB
