"""
Buoi 11+12 - LOGIC cua MASTER, tach rieng khoi MQTT/HTTP/Mongo de test duoc.

HeThong giu: du lieu doc ve tu 2 slave, nut bam tren web (thu_cong), lich
Light/Alarm Light, bang nguong. Moi khi co thay doi thi tinh lai lenh cho 7
dau ra va publish (chi khi khac lan truoc) len buoi11/dieu_khien.

"Set" tren web = THAY TOAN BO cai dat cu bang ban moi (khong tron voi ban
cu, o trong / bo tick deu co nghia) -> khong bao gio "ket o lan luu truoc".
"""

import copy
import json
import re
import threading
from datetime import datetime, timedelta, timezone

VN = timezone(timedelta(hours=7))

SLAVE1_TRUNG_BINH = "buoi11/slave1/trung_binh"
SLAVE1_TRANG_THAI = "buoi11/slave1/trang_thai"
SLAVE2_TRUNG_BINH = "buoi11/slave2/trung_binh"
SLAVE2_TRANG_THAI = "buoi11/slave2/trang_thai"
DIEU_KHIEN = "buoi11/dieu_khien"
TOPIC_NHAN = {
    SLAVE1_TRUNG_BINH: ("slave1", "trung_binh"),
    SLAVE1_TRANG_THAI: ("slave1", "trang_thai"),
    SLAVE2_TRUNG_BINH: ("slave2", "trung_binh"),
    SLAVE2_TRANG_THAI: ("slave2", "trang_thai"),
}

DAU_RA = ("led1", "led2", "led3", "buzzer", "relay", "light", "alarm")
DEN_NODE = ("light", "alarm")
LED_NGUONG = ("led1", "led2", "led3")
MAT_KET_NOI_GIAY = 5  # qua 5 giay khong nhan trang_thai -> web bao mat ket noi
_GIO = re.compile(r"([01]\d|2[0-3]):[0-5]\d")


class LoiDuLieu(ValueError):
    """Du lieu gui len sai -> web nhan HTTP 400, cai dat cu giu nguyen."""


def trong_khung(bat, tat, bay_gio):
    if bat <= tat:
        return bat <= bay_gio < tat
    return bay_gio >= bat or bay_gio < tat  # khung qua dem, vd 18:00 -> 06:00


def kiem_tra_lich(du_lieu):
    if not isinstance(du_lieu, dict) or du_lieu.get("che_do") not in ("tay", "tu_dong"):
        raise LoiDuLieu("che_do phai la 'tay' hoac 'tu_dong'")
    lich = {"che_do": du_lieu["che_do"]}
    for den in DEN_NODE:
        khung = du_lieu.get(den)
        if not isinstance(khung, dict):
            raise LoiDuLieu(f"thieu gio bat/tat cua {den}")
        for moc in ("bat", "tat"):
            if not isinstance(khung.get(moc), str) or not _GIO.fullmatch(khung[moc]):
                raise LoiDuLieu(f"gio {moc} cua {den} phai dang HH:MM")
        lich[den] = {"bat": khung["bat"], "tat": khung["tat"]}
    return lich


def _so_hoac_none(gia_tri, ten):
    if gia_tri is None or (isinstance(gia_tri, str) and not gia_tri.strip()):
        return None  # o trong = bo dieu kien nay
    try:
        so = float(gia_tri)
    except (TypeError, ValueError):
        raise LoiDuLieu(f"{ten} phai la so") from None
    if not 0 <= so <= 100:
        raise LoiDuLieu(f"{ten} phai trong khoang 0-100")
    return so


def kiem_tra_nguong(du_lieu):
    if not isinstance(du_lieu, dict) or not isinstance(du_lieu.get("den", {}), dict):
        raise LoiDuLieu("sai dinh dang bang nguong")
    den = du_lieu.get("den", {})
    return {
        "nhiet_do": _so_hoac_none(du_lieu.get("nhiet_do"), "nhiet_do"),
        "do_am": _so_hoac_none(du_lieu.get("do_am"), "do_am"),
        "den": {ten: den.get(ten) is True for ten in LED_NGUONG},  # khong tick / thieu = khong chon
    }


def vuot_nguong(nguong, trung_binh):
    for ten in ("nhiet_do", "do_am"):
        muc, do_duoc = nguong[ten], trung_binh.get(ten)
        if muc is not None and isinstance(do_duoc, (int, float)) and do_duoc >= muc:
            return True
    return False


class HeThong:
    def __init__(self, publish, luu_db, bay_gio=lambda: datetime.now(VN)):
        self._publish = publish  # publish(topic, chuoi_json)
        self._luu_db = luu_db  # luu_db(ten_collection, document)
        self._bay_gio = bay_gio
        self._khoa = threading.RLock()
        self._da_gui = None
        self.thu_cong = dict.fromkeys(DAU_RA, 0)
        self.lich = {
            "che_do": "tay",
            "light": {"bat": "18:00", "tat": "06:00"},
            "alarm": {"bat": "22:00", "tat": "05:00"},
            "luc": None,
        }
        self.nguong = {"nhiet_do": None, "do_am": None, "den": dict.fromkeys(LED_NGUONG, False), "luc": None}
        self.slave = {
            ten: {"trung_binh": {}, "trang_thai": {}, "luc_trung_binh": None, "luc_trang_thai": None}
            for ten in ("slave1", "slave2")
        }
        self.dieu_khien = dict.fromkeys(DAU_RA, 0)

    # --- du lieu tu slave -------------------------------------------------
    def nhan_mqtt(self, topic, payload):
        if topic not in TOPIC_NHAN:
            return
        du_lieu = json.loads(payload)
        if not isinstance(du_lieu, dict):
            raise LoiDuLieu("payload phai la JSON object")
        nguon, loai = TOPIC_NHAN[topic]
        luc = self._bay_gio()  # gio master - dong ho Pi nhom 3 bi sai
        with self._khoa:
            self.slave[nguon][loai] = du_lieu
            self.slave[nguon]["luc_" + loai] = luc
        self._luu_db(loai, {**du_lieu, "nguon": nguon, "thoi_gian": luc})
        if topic == SLAVE1_TRUNG_BINH:
            self.tinh_lai()  # nhiet do/do am moi -> xet lai nguong

    # --- tu web -----------------------------------------------------------
    def bam_nut(self, ten, gia_tri):
        if ten not in DAU_RA:
            raise LoiDuLieu(f"khong co thiet bi '{ten}'")
        if gia_tri not in (0, 1):
            raise LoiDuLieu("gia_tri phai la 0 hoac 1")
        with self._khoa:
            self.thu_cong[ten] = int(gia_tri)
        return self.tinh_lai()

    def luu_lich(self, du_lieu):
        moi = kiem_tra_lich(du_lieu)  # sai thi raise truoc khi dung vao cai dat cu
        return self._luu_cai_dat("lich", moi)

    def luu_nguong(self, du_lieu):
        moi = kiem_tra_nguong(du_lieu)
        return self._luu_cai_dat("nguong", moi)

    def _luu_cai_dat(self, loai, moi):
        luc = self._bay_gio()
        moi["luc"] = luc.strftime("%H:%M:%S")
        with self._khoa:
            setattr(self, loai, moi)
        self._luu_db("cai_dat", {"loai": loai, **copy.deepcopy(moi), "thoi_gian": luc})
        self.tinh_lai()
        return copy.deepcopy(moi)

    def nap_cai_dat(self, lich, nguong):
        """Lay lai lan Set cuoi cung (doc tu Database luc khoi dong). Hong thi bo qua."""
        with self._khoa:
            try:
                self.lich = {**kiem_tra_lich(lich), "luc": lich.get("luc")}
            except LoiDuLieu:
                pass
            try:
                self.nguong = {**kiem_tra_nguong(nguong), "luc": nguong.get("luc")}
            except LoiDuLieu:
                pass

    # --- tinh lenh dieu khien ------------------------------------------------
    def tinh_dieu_khien(self):
        with self._khoa:
            ra = dict(self.thu_cong)
            if self.lich["che_do"] == "tu_dong":
                gio = self._bay_gio().strftime("%H:%M")
                for den in DEN_NODE:
                    ra[den] = int(trong_khung(self.lich[den]["bat"], self.lich[den]["tat"], gio))
            if vuot_nguong(self.nguong, self.slave["slave1"]["trung_binh"]):
                for ten, chon in self.nguong["den"].items():
                    if chon:
                        ra[ten] = 1
            return ra

    def tinh_lai(self):
        with self._khoa:
            ra = self.tinh_dieu_khien()
            self.dieu_khien = ra
            chuoi = json.dumps(ra, sort_keys=True)
            if chuoi != self._da_gui:
                self._da_gui = chuoi
                self._publish(DIEU_KHIEN, chuoi)
            return dict(ra)

    def gui_lai(self):
        """Publish lai du khong doi (vd vua ket noi lai broker)."""
        with self._khoa:
            self._da_gui = None
            return self.tinh_lai()

    # --- cho web ------------------------------------------------------------
    def anh_chup(self):
        bay_gio = self._bay_gio()
        with self._khoa:
            ket_qua = {}
            for ten, s in self.slave.items():
                luc_tt = s["luc_trang_thai"]
                ket_qua[ten] = {
                    "trung_binh": dict(s["trung_binh"]),
                    "trang_thai": dict(s["trang_thai"]),
                    "luc_trung_binh": s["luc_trung_binh"].strftime("%H:%M:%S") if s["luc_trung_binh"] else None,
                    "ket_noi": luc_tt is not None and (bay_gio - luc_tt).total_seconds() <= MAT_KET_NOI_GIAY,
                }
            ket_qua.update(
                dieu_khien=dict(self.dieu_khien),
                thu_cong=dict(self.thu_cong),
                lich=copy.deepcopy(self.lich),
                nguong=copy.deepcopy(self.nguong),
                vuot_nguong=vuot_nguong(self.nguong, self.slave["slave1"]["trung_binh"]),
                gio=bay_gio.strftime("%H:%M:%S"),
            )
            return ket_qua
