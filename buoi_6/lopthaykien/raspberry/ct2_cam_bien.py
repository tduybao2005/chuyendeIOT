#!/usr/bin/env python3
"""
CHUONG TRINH 2 - DOC CAM BIEN VA GUI TRUNG BINH LEN SERVER

Yeu cau de bai (muc do 3):
    "Chuong trinh 2 doc du lieu nhiet do, do am moi 1s, gui len server gia tri
     nhiet do, do am trung binh moi 20s."

Cach lam:
    - Moi 1 giay doc DHT mot lan, LOAI NGAY gia tri ngoai dai hop le
      (de bai: du lieu loi thi khong duoc gui len Server ma phai doc lai).
    - Gom cac gia tri hop le vao mot "cua so" 20 giay, het 20 giay thi tinh
      trung binh va ghi 1 ban ghi len channel CAM BIEN.
    - Neu ca cua so 20 giay khong co gia tri hop le nao thi BO QUA ky do,
      khong ghi bua len Server.

Tu phuc hoi:
    - Doc hut le te      -> ghi log, chay tiep.
    - Hut 30 lan lien tiep hoac goi ThingSpeak hong 20 lan lien tiep
      -> thoat ma 1, systemd (iot-ct2-cambien.service) dung lai sau 10 giay.

Phan cung: cam bien DHT cam vao cong D22 cua Grove Base Hat (GPIO22).
"""

import sys
from time import monotonic

from seeed_dht import DHT

import cau_hinh as cfg
from thu_vien_chung import (TheoDoiSucKhoe, VongLapDinhNhip, gui_du_lieu,
                            tao_log_he_thong)

TEN = "ct2_cam_bien"


def trong_dai(gia_tri, dai):
    return gia_tri is not None and dai[0] <= gia_tri <= dai[1]


def main():
    # KHONG co logfile rieng: de bai chi doi dung 2 file (nut nhan va text
    # 16x2). Moi hoat dong cua chuong trinh nay ghi ra journal cua systemd,
    # xem bang:  journalctl -u iot-ct2-cambien -f
    logger = tao_log_he_thong(TEN)
    suc_khoe = TheoDoiSucKhoe(logger)

    logger.info(
        "Cau hinh: DHT%s tren GPIO%d | doc moi %ds | gui trung binh moi %ds "
        "| channel CAM BIEN = %s",
        cfg.LOAI_DHT, cfg.CHAN_DHT, cfg.CT2_NHIP_DOC, cfg.CT2_NHIP_GUI,
        cfg.CHANNEL_CAM_BIEN_ID or "(CHUA DIEN)",
    )
    if not cfg.CHANNEL_CAM_BIEN_ID or not cfg.CHANNEL_CAM_BIEN_WRITE_KEY:
        logger.error("Chua dien CHANNEL_CAM_BIEN_ID / WRITE_KEY trong cau_hinh.py")
        sys.exit(2)     # ma 2 = loi cau hinh, KHAC ma 1 (loi van hanh)

    try:
        cam_bien = DHT(cfg.LOAI_DHT, cfg.CHAN_DHT)
    except Exception as loi:
        logger.error("Khong khoi tao duoc cam bien DHT: %s", loi)
        sys.exit(2)

    # Cua so gom du lieu cua 20 giay gan nhat
    cua_so_nhiet_do = []
    cua_so_do_am = []

    nhip = VongLapDinhNhip(cfg.CT2_NHIP_DOC)

    # ---------------------------------------------------------------------
    # CHOT CUA SO BANG DONG HO, KHONG BANG SO VONG
    #
    # Ban dau o day dem so vong (20 vong x 1 giay = 20 giay) cho gon. Sai:
    # DHT.read() la ham CHAN, va khi cam bien tuot day / doc hut thi thu vien
    # seeed_dht tu thu lai ben trong, mot lan goi ton toi ~2.3 giay. Luc do
    # VongLapDinhNhip khong con giu duoc nhip 1 giay nua (no chi tru bot thoi
    # gian cho, khong rut ngan duoc ham chan), chu ky thuc te len 3.3 giay
    # -> 20 vong = 66 giay moi gui mot lan, vo yeu cau "gui moi 20 giay".
    #
    # Do bang monotonic() thi du moi vong dai ngan the nao, goi tin van ra
    # dung moi 20 giay. Dung monotonic chu khong dung datetime.now() vi
    # monotonic khong bi nhay khi he thong dong bo lai gio qua NTP.
    # ---------------------------------------------------------------------
    moc_gui_cuoi = monotonic()

    while True:
        with nhip:
            try:
                # ----- doc cam bien -----
                nhiet_do = do_am = None
                try:
                    do_am_tho, nhiet_do_tho = cam_bien.read()
                    nhiet_do = float(nhiet_do_tho)
                    do_am = float(do_am_tho)
                except Exception as loi:
                    logger.warning("Khong doc duoc DHT: %s", loi)

                # -----------------------------------------------------------
                # LOC CA KHUNG, KHONG LOC TUNG GIA TRI
                #
                # DHT11/22 tra nhiet do VA do am trong CUNG MOT khung 40 bit.
                # Do am sai nghia la ca khung hong -> nhiet do trong chinh khung
                # do cung khong tin duoc, du no tinh co roi vao dai hop le.
                #
                # Da gap dung loi nay khi test: cam bien chua cam, chan GPIO
                # lo lung sinh nhieu ra cap (1.0, 0.0). Do am 0% bi dai 20-95
                # loai dung, nhung nhiet do 1.0 lot dai 0-100 -> chuong trinh
                # gui len Server "nhiet do trung binh = 1.0 C". Do thi tren Web
                # hien mot cham cam le loi, va do la dung cai de bai cam:
                # "du lieu cam bien bi loi thi khong duoc gui len Server".
                #
                # Vi vay: chi nhan khi CA HAI gia tri deu hop le.
                # -----------------------------------------------------------
                ca_hai_hop_le = (trong_dai(nhiet_do, cfg.DAI_NHIET_DO)
                                 and trong_dai(do_am, cfg.DAI_DO_AM))

                nhiet_do_ok = do_am_ok = ca_hai_hop_le
                if ca_hai_hop_le:
                    cua_so_nhiet_do.append(nhiet_do)
                    cua_so_do_am.append(do_am)

                if ca_hai_hop_le:
                    suc_khoe.cam_bien_ok()
                    logger.info("Doc duoc: nhiet do=%.1f C, do am=%.1f %%",
                                nhiet_do, do_am)
                else:
                    suc_khoe.cam_bien_loi(
                        f"(khung hong - nhiet do={nhiet_do}, do am={do_am}; "
                        f"dai hop le {cfg.DAI_NHIET_DO} C va {cfg.DAI_DO_AM} %)"
                    )

                # ----- het 20 giay thi gui trung binh -----
                if monotonic() - moc_gui_cuoi >= cfg.CT2_NHIP_GUI:
                    gui_trung_binh(logger, suc_khoe, cua_so_nhiet_do, cua_so_do_am)
                    cua_so_nhiet_do = []
                    cua_so_do_am = []
                    moc_gui_cuoi = monotonic()

            except Exception as loi:
                # Bat o muc vong lap de chuong trinh khong bao gio dung han vi
                # mot loi khong luong truoc. Loi keo dai van bi TheoDoiSucKhoe
                # bat va cho thoat.
                logger.exception("Loi khong luong truoc trong vong lap chinh: %s", loi)


def gui_trung_binh(logger, suc_khoe, cua_so_nhiet_do, cua_so_do_am):
    """Tinh trung binh cua so 20s va ghi 1 ban ghi len channel CAM BIEN."""
    cac_field = {}
    if cua_so_nhiet_do:
        cac_field["field1"] = round(sum(cua_so_nhiet_do) / len(cua_so_nhiet_do), 1)
    if cua_so_do_am:
        cac_field["field2"] = round(sum(cua_so_do_am) / len(cua_so_do_am), 1)

    if not cac_field:
        # De bai: du lieu loi thi KHONG duoc gui len Server. Tha bo mot ky con
        # hon gui len mot con so bia.
        logger.warning(
            "Ca %ds vua roi khong co gia tri hop le nao -> BO QUA ky nay, khong gui",
            cfg.CT2_NHIP_GUI,
        )
        return

    logger.info(
        "Trung binh %ds: nhiet do=%s (tu %d mau), do am=%s (tu %d mau)",
        cfg.CT2_NHIP_GUI,
        cac_field.get("field1", "-"), len(cua_so_nhiet_do),
        cac_field.get("field2", "-"), len(cua_so_do_am),
    )
    gui_du_lieu(logger, suc_khoe, **cac_field)


if __name__ == "__main__":
    main()
