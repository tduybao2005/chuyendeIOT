#!/usr/bin/env python3
"""
CHUONG TRINH RASPBERRY PI - buoi 8 muc do 3 (10 diem).

=========================================================================
MOT CHU KY LAM GI
=========================================================================
MOI CHU KY DUNG 1 GIAY, lam tron ven 5 viec:

    1. Tien mot buoc vong den SANG DUOI (logic_led.py), luon chi 1 den sang:
           buoc 0 -> LED do   (D16)
           buoc 1 -> LED vang (D22)
           buoc 2 -> LED xanh (D24)   roi quay lai buoc 0
    2. Doc DHT11 (cong D5) lay nhiet do + do am.
    3. Loai gia tri rac (cam_bien_hop_le trong giao_tiep.py).
    4. GUI len server: nhiet do, do am va trang thai ca 3 den.
    5. DOC NGUOC TU SERVER ve roi in ra terminal.

=========================================================================
VI SAO BUOC 5 PHAI DOC TU SERVER
=========================================================================
Terminal KHONG in bien cuc bo (nhiet do vua doc duoc, hay bien `led` vua
tinh ra), ma in du lieu LAY VE TU SERVER - ke ca nhan mau den. Lam vong nhu vay chung minh ca duong di lan duong ve deu song:

    Pi -> HTTP -> FastAPI -> MongoDB Atlas -> FastAPI -> HTTP -> Pi

In bien cuc bo thi man hinh van dep y het ke ca khi Atlas dang chet - khong
chung minh duoc gi ca.

=========================================================================
CACH CHAY
=========================================================================
Tren Pi:
    export IOT_BUOI8_API_KEY="khoa-giong-het-trong-server/.env"
    export IOT_BUOI8_SERVER="http://192.168.1.100:8000"    # IP may chay server
    python3 chuong_trinh_pi.py

Chung minh du 4 duong API cua de bai (gui POST/GET, doc GET/POST):
    python3 chuong_trinh_pi.py --kieu-gui json     --kieu-doc get     # mac dinh
    python3 chuong_trinh_pi.py --kieu-gui form     --kieu-doc post
    python3 chuong_trinh_pi.py --kieu-gui get

Chay thu khi CHUA CAM cam bien / chua co Pi (sinh so gia, khong dung GPIO):
    python3 chuong_trinh_pi.py --gia-lap

So do noi day day du: xem cau_hinh_pi.py.
"""

import argparse
import random
import sys
from time import monotonic, sleep

import requests

import cau_hinh_pi as cfg
from giao_tiep import (LoiCauHinh, LoiTamThoi, cam_bien_hop_le,
                       dinh_dang_ban_ghi, dinh_dang_danh_sach,
                       dung_goi_tin, kiem_tra_phan_hoi, tao_phien)
from logic_led import den_dang_sang, mo_ta_den
from nhat_ky_csv import NhatKyCsv


# =========================================================================
# LOP BOC PHAN CUNG
#
# Gom moi thu cham vao GPIO vao dung mot cho, va cho phep thay bang ban gia
# lap. Nho vay chay thu duoc toan bo luong tren may tinh khong co Pi
# (--gia-lap), khong phai sua code o cho nao khac.
# =========================================================================
class PhanCung:
    """Cam bien DHT11 + 3 LED that tren Grove Base Hat."""

    def __init__(self):
        # Import o day chu khong o dau file: hai thu vien nay CHI cai duoc
        # tren Raspberry Pi. De o dau file thi ca che do --gia-lap tren may
        # tinh cung khong chay noi, va `pytest` cung khong import duoc.
        from gpiozero import LED
        from seeed_dht import DHT

        self._cam_bien = DHT(cfg.LOAI_DHT, cfg.CHAN_DHT)
        # initial_value=False: den tat ngay tu luc khoi tao, khong nhap nhay
        # mot cai luc chuong trinh vua len.
        self._led = (
            LED(cfg.CHAN_LED_DO, initial_value=False),
            LED(cfg.CHAN_LED_VANG, initial_value=False),
            LED(cfg.CHAN_LED_XANH, initial_value=False),
        )

    def doc_cam_bien(self):
        """Tra ve (do_am, nhiet_do) - DUNG thu tu thu vien seeed_dht tra ve.

        Thu vien tra DO AM TRUOC roi moi den nhiet do. Dao nham thu tu se ra
        "nhiet do 70 C, do am 28 %" - khong bao loi gi ca, chi la so vo ly.
        """
        return self._cam_bien.read()

    def bat_led(self, trang_thai):
        for den, bat in zip(self._led, trang_thai):
            den.on() if bat else den.off()

    def tat_het(self):
        for den in self._led:
            den.off()


class PhanCungGiaLap:
    """Ban gia lap de chay thu khi chua cam Pi - sinh so ngau nhien hop ly."""

    def __init__(self):
        self._trang_thai = (0, 0, 0)

    def doc_cam_bien(self):
        # So quanh vung nhiet do phong, du de thay du lieu doi tung chu ky.
        return round(random.uniform(55, 85), 1), round(random.uniform(24, 32), 1)

    def bat_led(self, trang_thai):
        self._trang_thai = tuple(trang_thai)

    def tat_het(self):
        self._trang_thai = (0, 0, 0)


# =========================================================================
# GOI SERVER
#
# Mot lop rieng de moi cho biet URL va API_KEY nam dung o day. Khoa luon di
# theo HEADER 'X-API-Key', khong bao gio nam trong than goi tin.
# =========================================================================
class MayChu:
    def __init__(self, dia_chi, api_key, timeout):
        self._goc = dia_chi.rstrip("/") + "/api/v1/du-lieu"
        self._timeout = timeout
        # tao_phien() (trong giao_tiep.py) gan san header X-API-Key va cau
        # hinh thu lai khi ket noi keep-alive bi rot - xem giai thich day du
        # ve loi do o cuoi giao_tiep.py.
        self._phien = tao_phien(api_key)

    # -- GUI: ba duong, de bai bat "ho tro ca 2 giao thuc POST/GET" ---------
    def gui_json(self, goi_tin):
        return self._tra_ban_ghi(self._phien.post(
            self._goc, json=goi_tin, timeout=self._timeout))

    def gui_form(self, goi_tin):
        return self._tra_ban_ghi(self._phien.post(
            self._goc, data=goi_tin, timeout=self._timeout))

    def gui_get(self, goi_tin):
        return self._tra_ban_ghi(self._phien.get(
            f"{self._goc}/gui", params=goi_tin, timeout=self._timeout))

    # -- DOC: hai duong ----------------------------------------------------
    def doc_moi_nhat(self):
        phan_hoi = self._phien.get(
            f"{self._goc}/moi-nhat",
            params={"ten_thiet_bi": cfg.TEN_THIET_BI}, timeout=self._timeout,
        )
        return self._tra_ban_ghi(phan_hoi)

    def doc_n_gan_nhat_bang_get(self, so_luong):
        phan_hoi = self._phien.get(
            self._goc,
            params={"n": so_luong, "ten_thiet_bi": cfg.TEN_THIET_BI},
            timeout=self._timeout,
        )
        return kiem_tra_phan_hoi(phan_hoi)["ban_ghi"]

    def doc_n_gan_nhat_bang_post(self, so_luong):
        phan_hoi = self._phien.post(
            f"{self._goc}/doc",
            json={"n": so_luong, "ten_thiet_bi": cfg.TEN_THIET_BI},
            timeout=self._timeout,
        )
        return kiem_tra_phan_hoi(phan_hoi)["ban_ghi"]

    @staticmethod
    def _tra_ban_ghi(phan_hoi):
        """Kiem tra phan hoi roi lay ra ban ghi.

        kiem_tra_phan_hoi() (trong giao_tiep.py) phan loai loi thanh
        LoiCauHinh / LoiTamThoi - xem giai thich su khac biet o file do.
        """
        return kiem_tra_phan_hoi(phan_hoi)["ban_ghi"]


# =========================================================================
# GIU DUNG NHIP
# =========================================================================
class VongLapDinhNhip:
    """Giu chu ky dung NHIP_GUI giay ke ca khi request cham.

    Tru di thoi gian vua ton, khong phai sleep(NHIP_GUI) sau moi vong. Neu
    chi sleep thi chu ky that = NHIP_GUI + thoi gian request, va nhip gui
    troi dan ra - sau mot gio chay se lech thay ro tren do thi.
    """

    def __init__(self, chu_ky):
        self._chu_ky = chu_ky
        self._moc = None

    def __enter__(self):
        self._moc = monotonic()
        return self

    def __exit__(self, *loi):
        con_lai = self._chu_ky - (monotonic() - self._moc)
        if con_lai > 0:
            sleep(con_lai)
        return False


# =========================================================================
# DEM LOI LIEN TIEP -> tu thoat cho systemd dung lai
# =========================================================================
class TheoDoiSucKhoe:
    def __init__(self, phan_cung):
        self._phan_cung = phan_cung
        self.loi_cam_bien = 0
        self.loi_mang = 0

    def cam_bien_hong(self, ly_do):
        self.loi_cam_bien += 1
        print(f"  [!] Doc cam bien that bai ({self.loi_cam_bien}"
              f"/{cfg.NGUONG_LOI_CAM_BIEN}): {ly_do}")
        if self.loi_cam_bien >= cfg.NGUONG_LOI_CAM_BIEN:
            self._thoat("cam bien hong lien tuc - kiem tra day cam o cong D5")

    def mang_hong(self, ly_do):
        self.loi_mang += 1
        print(f"  [!] Goi server that bai ({self.loi_mang}"
              f"/{cfg.NGUONG_LOI_MANG}): {ly_do}")
        if self.loi_mang >= cfg.NGUONG_LOI_MANG:
            self._thoat(f"khong goi duoc server {cfg.SERVER_URL} lien tuc")

    def cam_bien_ok(self):
        self.loi_cam_bien = 0

    def mang_ok(self):
        self.loi_mang = 0

    def _thoat(self, ly_do):
        print(f"\n[DUNG] {ly_do}.")
        print("Thoat ma 1 de systemd khoi dong lai mot tien trinh sach.")
        self._phan_cung.tat_het()
        sys.exit(1)


# =========================================================================
# CHUONG TRINH CHINH
# =========================================================================
def doc_tham_so():
    bo_doc = argparse.ArgumentParser(
        description="Pi gui nhiet do / do am / trang thai 3 LED len HTTP "
                    "Server, roi doc nguoc tu server ve de in ra terminal.",
    )
    bo_doc.add_argument(
        "--kieu-gui", choices=["json", "form", "get"], default="json",
        help="Cach gui du lieu len server. json/form = POST (de bai: 'json "
             "hoac form-urlencoded'), get = gui bang giao thuc GET.",
    )
    bo_doc.add_argument(
        "--kieu-doc", choices=["get", "post"], default="get",
        help="Giao thuc dung cho API doc N ban ghi gan nhat.",
    )
    bo_doc.add_argument(
        "--gia-lap", action="store_true",
        help="Sinh so gia, khong cham GPIO - de chay thu khi chua co Pi.",
    )
    bo_doc.add_argument(
        "--so-vong", type=int, default=0,
        help="Chay bao nhieu vong roi dung (0 = chay mai).",
    )
    return bo_doc.parse_args()


def mot_chu_ky(so_vong, phan_cung, may_chu, suc_khoe, ham_gui,
               ham_doc_lich_su, tham_so, nhat_ky):
    """Doc cam bien -> bat den -> gui len server -> doc nguoc ve -> in.

    Tach thanh ham rieng (thay vi viet thang trong vong while) de cho nao bo
    qua chu ky thi dung `return`. Viet trong vong while thi phai dung
    `continue`, ma `continue` nhay qua luon dong kiem tra --so-vong.
    """
    # --- 1. Tien mot buoc vong duoi -------------------------------------
    #
    # BAT DEN TRUOC KHI DOC CAM BIEN, khong phai sau. Doc DHT ton 0.22 giay
    # (do thuc te tren pi4-tdbao); neu bat den sau thi thoi diem den chuyen
    # bi xe dich theo do tre cua cam bien va vong duoi nhin giat cuc. Bat
    # ngay dau chu ky thi den chuyen dung nhip 1 giay deu tam tap.
    #
    # `so_vong` bat dau tu 1 nen tru 1 de buoc dau tien la 0 (den do).
    led = den_dang_sang(so_vong - 1)
    phan_cung.bat_led(led)

    # --- 2. Doc cam bien ------------------------------------------------
    try:
        do_am, nhiet_do = phan_cung.doc_cam_bien()
    except Exception as loi:
        suc_khoe.cam_bien_hong(loi)
        return

    if not cam_bien_hop_le(nhiet_do, do_am):
        suc_khoe.cam_bien_hong(
            f"gia tri ngoai dai hop le (nhiet do={nhiet_do}, do am={do_am})")
        return
    suc_khoe.cam_bien_ok()

    # --- 3. Gui len server ----------------------------------------------
    #
    # LoiCauHinh (sai API_KEY) KHONG bat o day: no bay thang len main() de
    # dung chuong trinh ngay. Thu lai 15 lan trong 75 giay voi mot cai khoa
    # sai la vo ich, va no con che mat ly do that - nguoi dung ngoi nhin man
    # hinh dem loi ma khong hieu vi sao.
    try:
        ham_gui(dung_goi_tin(cfg.TEN_THIET_BI, nhiet_do, do_am, led))
    except LoiTamThoi as loi:
        suc_khoe.mang_hong(loi)
        return
    except requests.RequestException as loi:
        suc_khoe.mang_hong(loi)
        return

    # --- 4. DOC NGUOC TU SERVER roi in ----------------------------------
    try:
        tu_server = may_chu.doc_moi_nhat()
    except (LoiTamThoi, requests.RequestException) as loi:
        suc_khoe.mang_hong(f"gui duoc nhung doc lai khong duoc: {loi}")
        return
    suc_khoe.mang_ok()

    # Ca nhan den cung lay tu ban ghi SERVER tra ve, khong lay bien `led`
    # cuc bo o tren. De bai doi terminal hien du lieu DOC VE TU SERVER -
    # lay bien cuc bo thi man hinh van dep y het ke ca khi server ghi sai.
    led_tu_server = tuple(tu_server.get(f"led{so}", 0) for so in (1, 2, 3))
    print(f"[{so_vong:>4}] {mo_ta_den(led_tu_server):<12} | "
          f"{dinh_dang_ban_ghi(tu_server)}")
    try:
        nhat_ky.ghi(tu_server)
    except OSError as loi:
        print(f"  [!] Ghi log CSV that bai: {loi}")

    # --- 5. Dinh ky doc N ban ghi gan nhat ------------------------------
    # De bai: "co the chon doc N du lieu gan nhat".
    if so_vong % cfg.SO_CHU_KY_MOI_LAN_XEM_LICH_SU == 0:
        try:
            lich_su = ham_doc_lich_su(cfg.SO_BAN_GHI_XEM_LICH_SU)
            print(f"  --- {cfg.SO_BAN_GHI_XEM_LICH_SU} ban ghi gan nhat doc "
                  f"tu server bang {tham_so.kieu_doc.upper()}:")
            print(dinh_dang_danh_sach(lich_su))
        except (LoiTamThoi, requests.RequestException) as loi:
            print(f"  [!] Doc lich su that bai: {loi}")


def main():
    tham_so = doc_tham_so()

    if not cfg.API_KEY:
        print("[LOI CAU HINH] Chua dat bien moi truong IOT_BUOI8_API_KEY.")
        print('  export IOT_BUOI8_API_KEY="khoa-giong-het-trong-server/.env"')
        sys.exit(2)      # ma 2 = loi cau hinh, KHAC ma 1 (loi van hanh)

    phan_cung = PhanCungGiaLap() if tham_so.gia_lap else PhanCung()
    may_chu = MayChu(cfg.SERVER_URL, cfg.API_KEY, cfg.HTTP_TIMEOUT)
    suc_khoe = TheoDoiSucKhoe(phan_cung)
    nhat_ky = NhatKyCsv()

    ham_gui = {"json": may_chu.gui_json, "form": may_chu.gui_form,
               "get": may_chu.gui_get}[tham_so.kieu_gui]
    ham_doc_lich_su = {"get": may_chu.doc_n_gan_nhat_bang_get,
                       "post": may_chu.doc_n_gan_nhat_bang_post}[tham_so.kieu_doc]

    print("=" * 78)
    print("IoT buoi 8 - muc do 3 | Raspberry Pi gui du lieu len HTTP Server")
    print("=" * 78)
    print(f"  Server        : {cfg.SERVER_URL}")
    print(f"  Ten thiet bi  : {cfg.TEN_THIET_BI}")
    print(f"  Kieu gui      : {tham_so.kieu_gui}"
          f"{'  (POST)' if tham_so.kieu_gui in ('json', 'form') else '  (GET)'}")
    print(f"  Kieu doc      : {tham_so.kieu_doc.upper()}")
    print(f"  Nhip          : {cfg.NHIP_GUI} giay/lan "
          f"(sang duoi + doc + gui + in, tat ca cung nhip nay)")
    if tham_so.gia_lap:
        print("  Che do        : GIA LAP (khong cham GPIO, so lieu la so gia)")
    else:
        print(f"  DHT{cfg.LOAI_DHT}        : cong D{cfg.CHAN_DHT} (GPIO{cfg.CHAN_DHT})")
        print(f"  LED do/vang/xanh : D{cfg.CHAN_LED_DO} / "
              f"D{cfg.CHAN_LED_VANG} / D{cfg.CHAN_LED_XANH}")
    print("-" * 78)
    print("Terminal duoi day in DU LIEU DOC VE TU SERVER, khong phai bien cuc bo.")
    print("Nhan Ctrl+C de dung.\n")

    nhip = VongLapDinhNhip(cfg.NHIP_GUI)
    so_vong = 0

    try:
        while True:
            so_vong += 1
            # Than chu ky nam trong ham rieng, va ham do dung `return` de bo
            # qua chu ky hong. TRUOC DAY cho nay dung `continue` ngay trong
            # vong while, va `continue` nhay qua luon dong kiem tra --so-vong
            # ben duoi -> chi can mot chu ky loi la tham so --so-vong bi bo
            # qua hoan toan va chuong trinh chay mai. Da gap that luc chay
            # thu voi API_KEY sai.
            with nhip:
                mot_chu_ky(so_vong, phan_cung, may_chu, suc_khoe,
                           ham_gui, ham_doc_lich_su, tham_so, nhat_ky)

            if tham_so.so_vong and so_vong >= tham_so.so_vong:
                break

    except KeyboardInterrupt:
        print("\n[DUNG] Nguoi dung bam Ctrl+C.")

    except LoiCauHinh as loi:
        # Sai API_KEY / gui sai dinh dang: thu lai bao nhieu lan cung the.
        # Bao ngay va thoat ma 2 (loi cau hinh) chu KHONG phai ma 1 - neu
        # thoat ma 1 thi systemd se khoi dong lai vo han mot chuong trinh
        # chac chan khong bao gio chay duoc, ghi day log ma khong ai de y.
        print(f"\n[DUNG - LOI CAU HINH] {loi}")
        print("\n  Thu lai cung khong het. Kiem tra:")
        print("   1. IOT_BUOI8_API_KEY tren Pi co GIONG HET API_KEY trong")
        print("      buoi_8/server/.env khong (ke ca hoa thuong)?")
        print("   2. Da chay lai `export` sau khi sua chua?")
        print(f"   3. Dang goi dung server chua: {cfg.SERVER_URL}")
        phan_cung.tat_het()
        sys.exit(2)

    finally:
        # Tat den truoc khi thoat. Khong tat thi den giu nguyen trang thai
        # vat ly sau khi chuong trinh da chet - nhin vao tuong nhu van chay.
        phan_cung.tat_het()
        print("Da tat het 3 LED.")


if __name__ == "__main__":
    main()
