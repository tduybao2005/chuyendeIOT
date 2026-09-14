#!/usr/bin/env python3
"""
CHUONG TRINH 3 - DOC LENH NUT NHAN TU SERVER, DIEU KHIEN 3 LED

Yeu cau de bai (muc do 3):
    "Chuong trinh 3 doc du lieu nut nhan tu server, dieu khien LED theo gia
     tri nhan duoc."

Cach lam:
    - Moi 0.5 giay goi 1 request doc channel LENH, lay gia tri moi nhat cua
      field1/field2/field3 (LED 1/2/3).
    - So voi trang thai dang bat, CHI khi co thay doi moi tac dong GPIO va
      ghi log - de logfile chi chua su kien that, de doi chieu khi cham diem.

RANG BUOC DO TRE: tu luc nguoi dung BAM NUT tren Web den luc den sang phai
duoi 2 GIAY. Quang duong do gom 3 chang:

    Web POST len ThingSpeak ............... 0.3 - 0.9 s
    Cho den vong poll ke tiep cua ham nay .. toi da = CT3_NHIP_DOC
    GET cua ham nay di va ve ............... 0.3 - 0.5 s

Nhip 1.0s cho xau nhat 2.4s (vo moc), nhip 0.5s cho xau nhat 1.9s (dat).
Vi vay CT3_NHIP_DOC = 0.5 - xem giai thich day du trong cau_hinh.py.

VongLapDinhNhip tru di thoi gian vua ton cho request nen CHU KY luon dung
0.5s. Neu chi sleep(0.5) sau moi request thi chu ky that = 0.5 + 0.4 = 0.9s
va moc 2 giay lai vo.

DO DO TRE THAT: doi chieu 2 moc thoi gian, ca hai deu theo dong ho cua Pi
(Node-RED chay trong Docker tren chinh Pi, da dat TZ=Asia/Ho_Chi_Minh):

    docker logs iot_buoi6_web | grep "NHAN LENH TU WEB"   <- luc bam nut
    grep "DA AP DUNG XONG" ~/iot_buoi6/logs/ct3_led.log   <- luc den sang

Vi sao doc bang HTTP polling chu khong subscribe MQTT:
    ThingSpeak cap DUNG MOT bo danh tinh MQTT cho moi thiet bi. Node-RED da
    giu ket noi do de ghi lenh; neu Pi mo them ket noi bang cung client_id thi
    theo chuan MQTT broker buoc phai da ket noi cu ra moi lan co ket noi moi
    -> hai ben da nhau lien tuc, roi phan lon lenh. Doc bang HTTP thi khong
    tranh chap gi va van nhan du moi lenh vi ThingSpeak luu chung moi lan ghi
    (HTTP hay MQTT) vao cung mot feed.

Tu phuc hoi:
    - Goi API hong le te -> ghi log, giu nguyen trang thai LED, chay tiep.
    - Hong 20 lan lien tiep -> tat LED roi thoat ma 1 cho systemd dung lai.

Phan cung: LED1 cong D5 (GPIO5), LED2 cong D16 (GPIO16), LED3 cong D18 (GPIO18).
"""

import sys

from gpiozero import LED

import cau_hinh as cfg
from thu_vien_chung import (
    TheoDoiSucKhoe,
    VongLapDinhNhip,
    doc_lenh_moi_nhat,
    sang_bool,
    tao_log_du_lieu,
    tao_log_he_thong,
)

TEN = "ct3_led"

# Ten -> so field tren channel LENH (xem so do field trong cau_hinh.py)
CAC_FIELD = {"led1": 1, "led2": 2, "led3": 3}


def main():
    # Hai duong ghi tach bach: 'log' la van hanh (ra journal), 'nhat_ky' la
    # DU LIEU (vao logfile 1). Mot dong chi di vao dung mot cho.
    log = tao_log_he_thong(TEN)
    nhat_ky = tao_log_du_lieu(
        cfg.LOG_1_NUT_NHAN,
        "LOGFILE 1: du lieu NUT NHAN doc tu server, dieu khien 3 LED (CT3)",
    )

    log.info(
        "Cau hinh: LED1=GPIO%d LED2=GPIO%d LED3=GPIO%d | doc lenh moi %ss "
        "| channel LENH = %s",
        cfg.CHAN_LED_1, cfg.CHAN_LED_2, cfg.CHAN_LED_3, cfg.CT3_NHIP_DOC,
        cfg.CHANNEL_LENH_ID or "(CHUA DIEN)",
    )
    if not cfg.CHANNEL_LENH_ID or not cfg.CHANNEL_LENH_READ_KEY:
        log.error("Chua dien CHANNEL_LENH_ID / READ_KEY trong cau_hinh.py")
        sys.exit(2)

    # initial_value=False: LED tat ngay tu luc khoi tao, khong nhap nhay mot
    # cai luc chuong trinh vua len.
    cac_led = {
        "led1": LED(cfg.CHAN_LED_1, initial_value=False),
        "led2": LED(cfg.CHAN_LED_2, initial_value=False),
        "led3": LED(cfg.CHAN_LED_3, initial_value=False),
    }

    def tat_het_led():
        """GPIO KHONG tu ve muc thap khi tien trinh chet - dang bat ma thoat
        ngang thi den se sang mai. Goi truoc moi lan thoat."""
        for led in cac_led.values():
            try:
                led.off()
            except Exception:
                pass

    suc_khoe = TheoDoiSucKhoe(log, don_dep=tat_het_led)

    # Trang thai Pi dang ap dung. Bat dau bang None (chua biet) chu khong phai
    # False, de lan doc dau tien luon ghi log day du ca 3 LED - lam moc "trang
    # thai ban dau" trong logfile.
    dang_bat = {"led1": None, "led2": None, "led3": None}

    nhip = VongLapDinhNhip(cfg.CT3_NHIP_DOC)
    while True:
        with nhip:
            try:
                lenh = doc_lenh_moi_nhat(log, suc_khoe, CAC_FIELD)
                if lenh is None:
                    continue        # mang loi, da ghi log; giu nguyen LED

                thay_doi = []
                for ten, led in cac_led.items():
                    # Field chua bao gio duoc ghi -> coi nhu TAT (mac dinh an toan)
                    mong_muon = sang_bool(lenh[ten]) if lenh[ten] is not None else False
                    if mong_muon == dang_bat[ten]:
                        continue
                    led.on() if mong_muon else led.off()
                    thay_doi.append(f"{ten.upper()}->{'BAT' if mong_muon else 'TAT'}")
                    dang_bat[ten] = mong_muon

                if thay_doi:
                    # DONG DUY NHAT di vao logfile 1: du lieu THO doc ve tu
                    # server, roi den trang thai 3 LED sau khi ap dung.
                    #
                    # Chi ghi KHI CO THAY DOI, khong ghi moi vong poll: nhip
                    # 0.5 giay ma ghi het thi ra 172.000 dong/ngay giong het
                    # nhau, file xoay vong vai tieng la mat sach lich su, va
                    # su kien that chim nghim giua dong rac.
                    #
                    # Moc thoi gian co mili giay -> tru thang cho moc
                    # "NHAN LENH TU WEB" cua Node-RED la ra do tre that tu
                    # luc bam nut den luc den sang.
                    nhat_ky.info(
                        "NUT NHAN doc tu server: led1=%s led2=%s led3=%s"
                        "  ->  LED1=%s LED2=%s LED3=%s",
                        lenh["led1"], lenh["led2"], lenh["led3"],
                        *("BAT" if dang_bat[t] else "TAT" for t in ("led1", "led2", "led3")),
                    )

            except Exception as loi:
                log.exception("Loi khong luong truoc trong vong lap: %s", loi)


if __name__ == "__main__":
    main()
