#!/usr/bin/env python3
"""
CHUONG TRINH 4 - DIEU KHIEN RELAY THEO LENH VA THEO LICH HEN GIO   (phan 13 diem)

Yeu cau de bai (muc nang cao):
    "Giao dien Web them giao dien de nguoi dung hen gio bat tat thiet bi relay"
    "Them chuong trinh Dieu khien bat/tat thiet bi relay theo gia tri doc ve
     tu server"
    "Co logfile rieng; chuong trinh cung tu khoi dong nhu cac chuong trinh khac"

Doc 2 field tren channel LENH:

    field4  Relay tay   "0" / "1"
    field6  Lich hen gio  "<bat_lich>|<gio_bat>|<gio_tat>"   vi du "1|18:00|22:00"

Quy tac quyet dinh:

    bat_lich = 1  ->  CHE DO HEN GIO: relay dong trong khoang [gio_bat, gio_tat),
                      ngoai khoang thi ngat. Field4 bi bo qua.
    bat_lich = 0  ->  CHE DO TAY: relay theo dung field4.

    Khoang gio QUA NUA DEM duoc xu ly dung: "22:00 -> 06:00" nghia la bat tu
    22h hom nay den 6h sang hom sau, khong phai mot khoang rong.

VI SAO GUI CA LICH LEN SERVER chu khong hen gio ngay trong Node-RED:
    De bai yeu cau ro chuong trinh nay "dieu khien relay theo gia tri DOC VE
    TU SERVER". Dat lich tren server con them 2 cai loi that: lich song sot
    qua ca lan khoi dong lai Node-RED, va nguoi cham diem mo channel len la
    thay duoc lich dang dat - minh chung ro rang.

Tu phuc hoi: goi API hong 20 lan lien tiep -> ngat relay roi thoat ma 1 cho
systemd (iot-ct4-relay.service) dung lai.

Phan cung: relay cam vao cong D24 cua Grove Base Hat (GPIO24).
"""

import sys
from datetime import datetime

from gpiozero import OutputDevice

import cau_hinh as cfg
from thu_vien_chung import (
    TheoDoiSucKhoe,
    VongLapDinhNhip,
    doc_lenh_moi_nhat,
    sang_bool,
    tao_log_he_thong,
)

TEN = "ct4_relay"

CAC_FIELD = {"relay_tay": 4, "lich": 6}

LICH_MAC_DINH = (False, None, None)   # (bat_lich, phut_bat, phut_tat)


def phan_tich_lich(chuoi, logger):
    """Doi chuoi "1|18:00|22:00" thanh (True, 1080, 1320).

    Tra ve so PHUT KE TU NUA DEM cho de so sanh (18:00 -> 18*60 = 1080).
    Chuoi sai dinh dang -> tra ve LICH_MAC_DINH (tat lich) va ghi log, de
    relay roi ve che do tay chu khong ket cung o mot trang thai kho doan.
    """
    if not chuoi:
        return LICH_MAC_DINH
    phan = str(chuoi).split("|")
    if len(phan) != 3:
        logger.warning("Chuoi lich sai dinh dang (can 3 phan): %r", chuoi)
        return LICH_MAC_DINH

    bat_lich = sang_bool(phan[0])
    try:
        gio_bat_h, gio_bat_m = (int(x) for x in phan[1].strip().split(":"))
        gio_tat_h, gio_tat_m = (int(x) for x in phan[2].strip().split(":"))
    except (ValueError, AttributeError):
        logger.warning("Chuoi lich sai dinh dang gio (can HH:MM): %r", chuoi)
        return LICH_MAC_DINH

    if not (0 <= gio_bat_h < 24 and 0 <= gio_bat_m < 60
            and 0 <= gio_tat_h < 24 and 0 <= gio_tat_m < 60):
        logger.warning("Gio trong lich nam ngoai 00:00-23:59: %r", chuoi)
        return LICH_MAC_DINH

    return bat_lich, gio_bat_h * 60 + gio_bat_m, gio_tat_h * 60 + gio_tat_m


def trong_khung_gio(phut_bat, phut_tat, phut_hien_tai):
    """True neu thoi diem hien tai nam trong khung gio hen.

    Hai truong hop:
        bat < tat  (18:00 -> 22:00): trong khung khi bat <= now < tat
        bat > tat  (22:00 -> 06:00): khung VAT QUA NUA DEM, trong khung khi
                                     now >= bat HOAC now < tat
        bat == tat: khung rong -> luon ngat (khong the vua bat vua tat)
    """
    if phut_bat == phut_tat:
        return False
    if phut_bat < phut_tat:
        return phut_bat <= phut_hien_tai < phut_tat
    return phut_hien_tai >= phut_bat or phut_hien_tai < phut_tat


def mo_ta_gio(phut):
    return "--:--" if phut is None else f"{phut // 60:02d}:{phut % 60:02d}"


def main():
    # KHONG co logfile rieng: de bai chi doi dung 2 file (nut nhan va text
    # 16x2). Moi hoat dong cua chuong trinh nay ghi ra journal cua systemd,
    # xem bang:  journalctl -u iot-ct4-relay -f
    logger = tao_log_he_thong(TEN)

    logger.info(
        "Cau hinh: relay=GPIO%d | doc lenh moi %ds | channel LENH = %s",
        cfg.CHAN_RELAY, cfg.CT4_NHIP_DOC, cfg.CHANNEL_LENH_ID or "(CHUA DIEN)",
    )
    if not cfg.CHANNEL_LENH_ID or not cfg.CHANNEL_LENH_READ_KEY:
        logger.error("Chua dien CHANNEL_LENH_ID / READ_KEY trong cau_hinh.py")
        sys.exit(2)

    relay = OutputDevice(cfg.CHAN_RELAY, active_high=True, initial_value=False)

    def ngat_relay():
        try:
            relay.off()
        except Exception:
            pass

    suc_khoe = TheoDoiSucKhoe(logger, don_dep=ngat_relay)

    dang_dong = None          # None = chua biet, de lan dau luon ghi log
    lich_da_ghi_log = None    # chi ghi log khi NGUOI DUNG doi lich
    lan_doc_dau = True        # phan biet "trang thai ban dau" voi "vua thay doi"

    nhip = VongLapDinhNhip(cfg.CT4_NHIP_DOC)
    while True:
        with nhip:
            try:
                lenh = doc_lenh_moi_nhat(logger, suc_khoe, CAC_FIELD)
                if lenh is None:
                    continue      # mang loi, da ghi log; giu nguyen relay

                bat_lich, phut_bat, phut_tat = phan_tich_lich(lenh["lich"], logger)

                if (bat_lich, phut_bat, phut_tat) != lich_da_ghi_log:
                    # Lan doc dau tien la TRANG THAI BAN DAU doc ve luc khoi
                    # dong, khong phai nguoi dung vua doi lich. Ghi nhap nhem
                    # hai thu nay thi doc log se tuong co nguoi thao tac.
                    logger.info(
                        "%s: lich hen gio %s | bat luc %s, tat luc %s",
                        "TRANG THAI BAN DAU DOC TU SERVER" if lan_doc_dau
                        else "NGUOI DUNG VUA DOI LICH TREN WEB",
                        "DANG BAT" if bat_lich else "DANG TAT",
                        mo_ta_gio(phut_bat), mo_ta_gio(phut_tat),
                    )
                    lich_da_ghi_log = (bat_lich, phut_bat, phut_tat)

                # ---- quyet dinh trang thai relay ----
                if bat_lich and phut_bat is not None:
                    bay_gio = datetime.now()
                    phut_hien_tai = bay_gio.hour * 60 + bay_gio.minute
                    mong_muon = trong_khung_gio(phut_bat, phut_tat, phut_hien_tai)
                    ly_do = (f"lich hen gio {mo_ta_gio(phut_bat)}-{mo_ta_gio(phut_tat)}, "
                             f"bay gio {bay_gio.strftime('%H:%M')}")
                else:
                    mong_muon = sang_bool(lenh["relay_tay"])
                    if lenh["relay_tay"] is None:
                        # Field chua bao gio duoc ghi - KHONG phai co nguoi bam
                        # nut Tat. Ghi "nut bam tay tren Web" o day la sai su
                        # that, doc log se tuong co nguoi vua thao tac.
                        ly_do = "chua co lenh nao tren server -> mac dinh NGAT cho an toan"
                    else:
                        ly_do = f"nut bam tay tren Web (field4={lenh['relay_tay']})"

                if mong_muon != dang_dong:
                    relay.on() if mong_muon else relay.off()
                    logger.info("RELAY -> %s | ly do: %s",
                                "DONG (BAT)" if mong_muon else "NGAT (TAT)", ly_do)
                    dang_dong = mong_muon

                lan_doc_dau = False

            except Exception as loi:
                logger.exception("Loi khong luong truoc trong vong lap: %s", loi)


if __name__ == "__main__":
    main()
