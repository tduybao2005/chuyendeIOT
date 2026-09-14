#!/usr/bin/env python3
"""
CHUONG TRINH 5 - DOC TEXT 16x2 TU SERVER, HIEN THI LEN LCD 16x2   (phan 13 diem)

Yeu cau de bai (muc nang cao):
    "Giao dien nhap gia tri gui du lieu toi da 16x2 ky tu gui len server"
    "Doc du lieu text 16x2 tu server, hien thi gia tri len LCD 16x2"
    "Co logfile rieng; chuong trinh cung tu khoi dong nhu cac chuong trinh khac"

Doc 1 field tren channel LENH:

    field5   "<dong 1>|<dong 2>"   moi dong toi da 16 ky tu

Web da chan do dai o o nhap, nhung chuong trinh nay VAN cat lai 16 ky tu:
khong bao gio tin du lieu tu ben ngoai - neu ai do ghi tay bang curl mot chuoi
dai 100 ky tu thi LCD se tran sang dong duoi va hien ra rac.

DAU TIENG VIET: LCD 16x2 chi co bang ky tu ASCII, khong co "ệ" hay "ộ". Chuong
trinh tu bo dau (Nhiet do thay vi Nhiet do co dau) thay vi de LCD hien o vuong.

Tu phuc hoi:
    - LCD roi rac loi (nhieu I2C) -> ghi log, chay tiep.
    - LCD hong / tuot day 30 lan lien tiep -> thoat ma 1 cho systemd
      (iot-ct5-lcd.service) dung lai sau 10 giay.

Phan cung: LCD JHD1802 cam vao bat ky cong I2C nao cua Grove Base Hat.
           Dia chi: 0x3E (hien thi ky tu) + 0x62 (den nen RGB).
"""

import sys
import unicodedata
from datetime import datetime

import smbus2

import cau_hinh as cfg
from thu_vien_chung import (
    TheoDoiSucKhoe,
    VongLapDinhNhip,
    doc_lenh_moi_nhat,
    tao_log_du_lieu,
    tao_log_he_thong,
)

TEN = "ct5_lcd"

CAC_FIELD = {"text": 5}

SO_COT = 16
SO_DONG = 2

DIA_CHI_HIEN_THI = 0x3E
DIA_CHI_DEN_NEN = 0x62


class ManHinhLCD:
    """Driver toi gian cho LCD 16x2 JHD1802 qua I2C.

    Tu viet thay vi dung grove.display.jhd1802 vi thu vien do NUOT loi I2C -
    LCD tuot day van "chay binh thuong" ma khong hien gi. Khong phat hien duoc
    loi thi khong the tu khoi dong lai, ma do la yeu cau bat buoc cua de bai.
    O day moi loi ghi I2C deu nem ra ngoai cho vong lap chinh dem.
    """

    def __init__(self):
        self.bus = smbus2.SMBus(1)
        self.dat_den_nen(255, 255, 255)
        self.lenh(0x38)   # function set: giao tiep 8 bit, 2 dong, font 5x8
        self.lenh(0x0C)   # display on, tat con tro, tat nhap nhay
        self.lenh(0x01)   # xoa man hinh
        self._cho_xoa_xong()

    @staticmethod
    def _cho_xoa_xong():
        # Lenh xoa man hinh cua HD44780 mat ~1.5ms; gui lenh tiep theo qua som
        # thi bi bo qua, man hinh ket o trang thai nua voi.
        from time import sleep
        sleep(0.05)

    def lenh(self, ma):
        self.bus.write_byte_data(DIA_CHI_HIEN_THI, 0x80, ma)

    def dat_con_tro(self, dong, cot):
        self.lenh((0x40 * dong) + (cot % 0x10) + 0x80)

    def viet(self, chuoi):
        for ky_tu in chuoi:
            self.bus.write_byte_data(DIA_CHI_HIEN_THI, 0x40, ord(ky_tu))

    def dat_den_nen(self, do, xanh_la, xanh_duong):
        """Den nen nam o chip rieng (0x62). Hong den nen KHONG phai loi nghiem
        trong - man hinh van doc duoc - nen nuot loi o day."""
        try:
            for thanh_ghi, gia_tri in (
                (0x00, 0x00), (0x01, 0x00), (0x08, 0xAA),
                (0x04, do), (0x03, xanh_la), (0x02, xanh_duong),
            ):
                self.bus.write_byte_data(DIA_CHI_DEN_NEN, thanh_ghi, gia_tri)
        except OSError:
            pass

    def hien_hai_dong(self, dong_1, dong_2):
        self.dat_con_tro(0, 0)
        self.viet(dong_1.ljust(SO_COT)[:SO_COT])
        self.dat_con_tro(1, 0)
        self.viet(dong_2.ljust(SO_COT)[:SO_COT])


def bo_dau(chuoi):
    """Doi "Nhiet do phong" co dau thanh khong dau, bo ky tu ngoai ASCII.

    LCD 16x2 chi co bang ky tu ASCII. Tach chuoi ra dang NFD (chu cai + dau
    roi nhau) roi bo cac ky tu dau (category Mn), phan con lai ep ve ASCII.
    """
    tach_dau = unicodedata.normalize("NFD", str(chuoi))
    khong_dau = "".join(c for c in tach_dau if unicodedata.category(c) != "Mn")
    # "đ"/"Đ" khong tach duoc bang NFD nen phai doi tay
    khong_dau = khong_dau.replace("đ", "d").replace("Đ", "D")
    return khong_dau.encode("ascii", "replace").decode("ascii")


def tach_hai_dong(chuoi_tho):
    """Doi "dong1|dong2" tu server thanh 2 dong da cat dung 16 ky tu.

    Tra ve None khi KHONG CO gi de hien - gom ca 3 truong hop:
      - field5 chua bao gio duoc ghi          (chuoi_tho is None)
      - field5 la chuoi rong                  ("")
      - field5 chi co dau phan cach, 2 dong deu trong  ("|")

    Truong hop thu 3 xay ra that: giao dien gui CA 6 field moi lan bam nut, ma
    o text mac dinh la "|" khi chua ai go gi. Bam mot nut LED la field5 thanh
    "|" -> neu cu the hien len thi LCD trang tron, nhin nhu man hinh chet,
    quay video khong chung minh duoc gi. Tra ve None de ben goi hien dong ho
    du phong cho thay man hinh van song.
    """
    if chuoi_tho in (None, ""):
        return None
    phan = str(chuoi_tho).split("|")
    dong_1 = bo_dau(phan[0])[:SO_COT]
    dong_2 = bo_dau(phan[1])[:SO_COT] if len(phan) > 1 else ""
    if not dong_1.strip() and not dong_2.strip():
        return None
    return dong_1, dong_2


def main():
    log = tao_log_he_thong(TEN)
    nhat_ky = tao_log_du_lieu(
        cfg.LOG_2_TEXT,
        "LOGFILE 2: du lieu TEXT 16x2 doc tu server, hien len LCD (CT5)",
    )

    log.info(
        "Cau hinh: LCD JHD1802 I2C 0x%02X | doc text moi %ds | channel LENH = %s",
        DIA_CHI_HIEN_THI, cfg.CT5_NHIP_DOC, cfg.CHANNEL_LENH_ID or "(CHUA DIEN)",
    )
    if not cfg.CHANNEL_LENH_ID or not cfg.CHANNEL_LENH_READ_KEY:
        log.error("Chua dien CHANNEL_LENH_ID / READ_KEY trong cau_hinh.py")
        sys.exit(2)

    try:
        lcd = ManHinhLCD()
    except OSError as loi:
        # Khong khoi tao duoc ngay tu dau nghia la LCD chua cam. Thoat ma 1
        # (khong phai 2) de systemd cu thu lai deu dan - cam day vao la chay,
        # khong can ai ssh vao bat tay.
        log.error("Khong thay LCD tren I2C 0x%02X (%s) -> thoat cho systemd thu lai",
                  DIA_CHI_HIEN_THI, loi)
        sys.exit(1)

    suc_khoe = TheoDoiSucKhoe(log)

    lcd.hien_hai_dong("IoT Buoi 6", "Cho du lieu...")
    log.info("LCD san sang, dang cho text tu server")

    dang_hien = None
    # -----------------------------------------------------------------------
    # TU LAM TUOI DINH KY
    #
    # Neu chi ghi LCD KHI NOI DUNG DOI thi man hinh bi treo vi nhieu I2C hay
    # sut ap se KHONG BAO GIO duoc ghi lai - no dung nguyen o noi dung cu (hoac
    # trang tron) mai mai, du server da doi text tu doi nao. Trieu chung dung
    # nhu nguoi dung mo ta: "ban dau chay sao thi chay vay luon, doi text
    # khong duoc".
    #
    # Cu moi SO_VONG_LAM_TUOI vong thi ghi lai nguyen noi dung dang hien, ke ca
    # khong co gi doi. Ghi lai la man hinh tu hoi phuc. KHONG ghi log lan nay -
    # day khong phai su kien moi, ban vao logfile 2 chi lam nhieu.
    # -----------------------------------------------------------------------
    SO_VONG_LAM_TUOI = 12          # 12 x 5 giay = lam tuoi moi 60 giay
    so_vong = 0

    # Dang o che do dong ho du phong (server chua co text). Can co bien nay vi
    # dong ho DOI MOI LAN DOC -> neu cu "khac cai dang hien thi ghi log" thi se
    # ghi 1 dong moi 5 giay = 17.280 dong/ngay, su kien that (nguoi dung gui
    # text moi) chim nghim giua dong rac va file xoay vong lam mat lich su.
    dang_o_che_do_dong_ho = False

    nhip = VongLapDinhNhip(cfg.CT5_NHIP_DOC)
    while True:
        with nhip:
            try:
                lenh = doc_lenh_moi_nhat(log, suc_khoe, CAC_FIELD)
                if lenh is None:
                    continue      # mang loi, da ghi log; giu nguyen man hinh

                text_tho = lenh["text"]
                hai_dong = tach_hai_dong(text_tho)

                if hai_dong is None:
                    # Chua ai gui text bao gio -> hien dong ho cho de nhin thay
                    # man hinh van song (huu ich khi quay video minh chung).
                    hai_dong = ("IoT Buoi 6", datetime.now().strftime("Time %H:%M:%S"))
                    # Chi ghi log LAN DAU buoc vao che do dong ho, khong ghi
                    # moi lan kim giay nhay.
                    ghi_log = not dang_o_che_do_dong_ho
                    mo_ta_log = "Server chua co text, hien dong ho du phong"
                    dang_o_che_do_dong_ho = True
                else:
                    # Text that tu server: chi ghi log khi NOI DUNG DOI.
                    ghi_log = (hai_dong != dang_hien) or dang_o_che_do_dong_ho
                    mo_ta_log = "TEXT doc tu server"
                    dang_o_che_do_dong_ho = False

                so_vong += 1
                den_luc_lam_tuoi = (so_vong % SO_VONG_LAM_TUOI == 0)

                if hai_dong == dang_hien and not den_luc_lam_tuoi:
                    continue
                if hai_dong == dang_hien:
                    ghi_log = False      # chi lam tuoi, khong phai su kien moi

                try:
                    lcd.hien_hai_dong(*hai_dong)
                except OSError as loi:
                    suc_khoe.cam_bien_loi(f"(ghi LCD that bai: {loi})")
                    dang_hien = None     # buoc ghi lai o vong sau
                    continue

                suc_khoe.cam_bien_ok()
                if ghi_log:
                    # DONG DUY NHAT di vao logfile 2: chuoi THO doc ve tu
                    # server, roi 2 dong da bo dau va cat 16 ky tu dang hien
                    # tren LCD.
                    nhat_ky.info('%s: %r  ->  LCD dong1=%r dong2=%r',
                                 mo_ta_log, text_tho, hai_dong[0], hai_dong[1])
                dang_hien = hai_dong

            except Exception as loi:
                log.exception("Loi khong luong truoc trong vong lap: %s", loi)


if __name__ == "__main__":
    main()
