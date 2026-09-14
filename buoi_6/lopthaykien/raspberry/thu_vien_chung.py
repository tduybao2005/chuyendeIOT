"""
Thu vien dung chung cho ca 4 chuong trinh Python cua buoi 6 (muc 15 diem).

Gom 4 phan viec ma CA BON chuong trinh deu can, de moi chuong trinh chi con
lo dung phan nghiep vu cua no:

    1. tao_log_he_thong()  - log VAN HANH ra journal (khoi dong, loi, restart)
       tao_log_du_lieu()   - log DU LIEU vao file (2 logfile de bai yeu cau)
    2. TheoDoiSucKhoe      - dem loi lien tiep -> tu thoat de systemd dung lai
    3. doc_lenh_moi_nhat() - doc channel LENH, tra ve gia tri moi nhat tung field
    4. gui_du_lieu()       - ghi len channel CAM BIEN, co tu thu lai
    5. VongLapDinhNhip     - giu dung chu ky (1s/2s/5s) ke ca khi request cham

Viet mot lan o day thay vi chep 4 lan: sua logic tu phuc hoi hay cach doc
ThingSpeak thi ca 4 chuong trinh cung duoc sua theo.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from time import monotonic, sleep

import requests

import cau_hinh as cfg


# =========================================================================
# 1. HAI LOAI LOG - TACH BACH HOAN TOAN
#
# De bai chi doi DUNG HAI logfile, va moi file chi chua dung loai du lieu cua
# no. Vi vay chia lam 2 duong ghi rieng biet:
#
#   tao_log_du_lieu()   -> GHI VAO FILE. Chi chua du lieu doc ve tu server.
#                          Khong ban dong khoi dong, khong ban cau hinh, khong
#                          ban thong bao loi mang. Mo file ra la thay ngay
#                          "server tra ve gi, Pi lam gi" - khong phai loc.
#
#   tao_log_he_thong()  -> GHI RA STDOUT (journal cua systemd). Chua moi thu
#                          con lai: khoi dong, cau hinh, loi cam bien, loi
#                          mang, ly do tu khoi dong lai. Xem bang
#                          `journalctl -u iot-ct3-led -f`.
#
# Hai duong khong giao nhau: mot dong log chi di vao DUNG MOT trong hai cho.
# =========================================================================
def tao_log_he_thong(ten_chuong_trinh):
    """Log VAN HANH -> stdout, systemd gom vao journal. KHONG ghi ra file."""
    logger = logging.getLogger(f"{ten_chuong_trinh}.he_thong")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger

    ghi_man_hinh = logging.StreamHandler(sys.stdout)
    ghi_man_hinh.setFormatter(logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(ghi_man_hinh)
    logger.info("KHOI DONG chuong trinh '%s' (PID %d)", ten_chuong_trinh, os.getpid())
    return logger


def tao_log_du_lieu(ten_file, mo_ta):
    """Log DU LIEU -> ghi vao file, KHONG in ra man hinh.

    ten_file: ten file trong thu muc log, vi du "logfile1_nut_nhan.log".
    mo_ta:    mot dong duy nhat ghi o dau file moi khi chuong trinh khoi dong,
              de nguoi doc biet file nay chua gi.

    Tu xoay vong khi qua 2 MB (giu 5 file cu). Khong xoay vong thi chay lien
    tuc nhieu ngay se lam day the nho -> Pi treo, dung dung luc quay video.
    """
    os.makedirs(cfg.THU_MUC_LOG, exist_ok=True)
    duong_dan = os.path.join(cfg.THU_MUC_LOG, ten_file)

    logger = logging.getLogger(f"du_lieu.{ten_file}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger

    ghi_file = RotatingFileHandler(
        duong_dan,
        maxBytes=cfg.LOG_KICH_THUOC_TOI_DA,
        backupCount=cfg.LOG_SO_FILE_GIU_LAI,
        encoding="utf-8",
    )
    # Moc thoi gian co MILI GIAY de doi chieu do tre voi log cua Node-RED.
    ghi_file.setFormatter(logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(ghi_file)
    logger.info("--- %s ---", mo_ta)
    return logger


# =========================================================================
# 2. TU PHUC HOI: dem loi LIEN TIEP -> thoat de systemd dung lai
# =========================================================================
class TheoDoiSucKhoe:
    """Dem so lan loi LIEN TIEP cua cam bien va cua mang.

    De bai yeu cau chuong trinh "tu reset/khoi dong lai khi xay ra loi cam
    bien, rot mang". Cach lam:

        - Loi le te  -> try/except nuot, chay tiep (khong reset vo co).
        - Loi LIEN TIEP vuot nguong -> thoat ma 1, systemd dung lai tien trinh
          sach sau RestartSec=10 giay.

    Moi lan thanh cong deu goi cam_bien_ok()/mang_ok() de dua bo dem ve 0,
    nen chuoi loi bi ngat quang se khong bao gio cong don den nguong.
    """

    def __init__(self, logger, don_dep=None):
        self.logger = logger
        # Ham tat thiet bi truoc khi thoat. os._exit() BO QUA khoi finally nen
        # neu khong tu tat o day thi LED/relay se giu nguyen trang thai vat ly
        # sau khi tien trinh chet.
        self.don_dep = don_dep
        self.loi_cam_bien = 0
        self.loi_mang = 0

    def cam_bien_ok(self):
        self.loi_cam_bien = 0

    def cam_bien_loi(self, mo_ta=""):
        self.loi_cam_bien += 1
        n = self.loi_cam_bien
        self.logger.warning(
            "LOI CAM BIEN (%d/%d lan lien tiep) %s", n, cfg.NGUONG_LOI_CAM_BIEN, mo_ta
        )
        if n >= cfg.NGUONG_LOI_CAM_BIEN:
            self.tu_thoat(f"cam bien loi {n} lan lien tiep")

    def mang_ok(self):
        self.loi_mang = 0

    def mang_loi(self, mo_ta=""):
        self.loi_mang += 1
        n = self.loi_mang
        self.logger.warning(
            "LOI MANG (%d/%d lan lien tiep) %s", n, cfg.NGUONG_LOI_MANG, mo_ta
        )
        if n >= cfg.NGUONG_LOI_MANG:
            self.tu_thoat(f"rot mang {n} lan lien tiep")

    def tu_thoat(self, ly_do):
        """Ket thuc HAN tien trinh de systemd dung lai.

        PHAI dung os._exit() chu khong phai sys.exit(): sys.exit() chi nem
        SystemExit, ma cac vong lap ben duoi deu boc trong 'except Exception'
        ... thuc te SystemExit khong ke thua Exception nen khong bi nuot, NHUNG
        neu sau nay ai do doi thanh 'except BaseException' hoac goi ham nay tu
        mot luong phu thi sys.exit() se chi ket thuc dung luong do, tien trinh
        van song trong trang thai que quat. os._exit() ket thuc ca tien trinh
        tu bat ky dau.

        Buoc don dep nam trong try/finally de DU CO LOI GI van thoat duoc.
        """
        try:
            self.logger.error("TU KHOI DONG LAI: %s -> thoat de systemd dung lai", ly_do)
            if self.don_dep:
                self.don_dep()
            logging.shutdown()
        finally:
            os._exit(1)


# =========================================================================
# 3. DOC CHANNEL LENH
# =========================================================================
def doc_lenh_moi_nhat(logger, suc_khoe, cac_field):
    """Doc channel LENH, tra ve dict {ten: gia_tri_chuoi} moi nhat.

    cac_field: dict {ten_de_dung: so_field}, vi du {"led1": 1, "led2": 2}.

    CACH LAM: mot lan GET /feeds.json?results=10 lay ve 10 ban ghi gan nhat
    roi quet NGUOC tu moi den cu, lay gia tri KHONG null dau tien cho TUNG
    field. Ly do phai quet nguoc chu khong lay moi dong cuoi: neu Web (hoac
    curl) ghi le mot field thi ThingSpeak van tao mot dong moi va dat null cho
    cac field con lai - chi nhin dong cuoi se tuong cac field kia da bi xoa.

    Tra ve None (chu khong phai dict rong) khi goi API that bai, de ben goi
    phan biet duoc "mang loi" voi "chua co lenh nao".
    """
    tham_so = {
        "api_key": cfg.CHANNEL_LENH_READ_KEY,
        "results": cfg.SO_BAN_GHI_DOC_VE,
    }
    try:
        phan_hoi = requests.get(cfg.URL_DOC_LENH, params=tham_so, timeout=cfg.HTTP_TIMEOUT)
        phan_hoi.raise_for_status()
        danh_sach = phan_hoi.json().get("feeds") or []
    except (requests.RequestException, ValueError) as loi:
        suc_khoe.mang_loi(f"doc channel LENH that bai: {loi}")
        return None

    suc_khoe.mang_ok()

    ket_qua = {ten: None for ten in cac_field}
    for ban_ghi in reversed(danh_sach):          # moi -> cu
        for ten, so in cac_field.items():
            if ket_qua[ten] is not None:
                continue
            gia_tri = ban_ghi.get(f"field{so}")
            if gia_tri not in (None, ""):
                ket_qua[ten] = gia_tri
        if all(v is not None for v in ket_qua.values()):
            break
    return ket_qua


def sang_bool(gia_tri):
    """Doi gia tri ThingSpeak (chuoi "0"/"1", so, None) thanh True/False."""
    try:
        return float(gia_tri) >= 1
    except (TypeError, ValueError):
        return False


# =========================================================================
# 4. GHI LEN CHANNEL CAM BIEN
# =========================================================================
def gui_du_lieu(logger, suc_khoe, **cac_field):
    """Ghi 1 ban ghi len channel CAM BIEN, tu thu lai toi da 3 lan.

    BAY QUAN TRONG: khi bi tu choi vi chua du ~15 giay ke tu lan ghi truoc,
    ThingSpeak KHONG tra ve loi HTTP - no tra ve 200 kem noi dung {"entry_id":0}
    (hoac so 0 tran). Vi vay khong the chi dua vao raise_for_status(), phai
    kiem tra entry_id trong noi dung tra ve.
    """
    du_lieu = {"api_key": cfg.CHANNEL_CAM_BIEN_WRITE_KEY}
    du_lieu.update(cac_field)

    for lan in range(1, 4):
        try:
            phan_hoi = requests.post(cfg.URL_GHI, json=du_lieu, timeout=cfg.HTTP_TIMEOUT)
            phan_hoi.raise_for_status()
            ket_qua = phan_hoi.json()
        except (requests.RequestException, ValueError) as loi:
            logger.warning("Gui ThingSpeak loi (lan %d/3): %s", lan, loi)
            ket_qua = None

        if isinstance(ket_qua, dict) and ket_qua.get("entry_id"):
            suc_khoe.mang_ok()
            logger.info("DA GUI len channel CAM BIEN: %s (entry_id=%s)",
                        cac_field, ket_qua["entry_id"])
            return True

        if lan < 3:
            sleep(5)   # nhieu kha nang dang vuong gioi han 15s, doi roi thu lai

    suc_khoe.mang_loi("gui ThingSpeak that bai sau 3 lan thu")
    return False


# =========================================================================
# 5. VONG LAP DINH NHIP
# =========================================================================
class VongLapDinhNhip:
    """Giu dung CHU KY mong muon, khong phai "nghi N giay sau moi vong".

    Neu chi sleep(1) sau moi vong thi chu ky thuc te = 1s + thoi gian request
    (0.3-0.9s) = 1.3-1.9s, cham gan gap doi. Lop nay tru di thoi gian vua lam
    viec nen chu ky luon dung bang nhip da dat.

    Dung nhu mot context manager:

        nhip = VongLapDinhNhip(1)
        while True:
            with nhip:
                lam_viec()
    """

    def __init__(self, chu_ky, nghi_toi_thieu=0.05):
        self.chu_ky = chu_ky
        self.nghi_toi_thieu = nghi_toi_thieu
        self._bat_dau = 0.0

    def __enter__(self):
        self._bat_dau = monotonic()
        return self

    def __exit__(self, *_):
        con_lai = self.chu_ky - (monotonic() - self._bat_dau)
        sleep(max(self.nghi_toi_thieu, con_lai))
        return False   # khong nuot ngoai le
