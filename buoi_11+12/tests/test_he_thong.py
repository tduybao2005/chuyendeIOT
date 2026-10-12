import json
from datetime import datetime

import pytest

from he_thong import (
    DIEU_KHIEN,
    SLAVE1_TRANG_THAI,
    SLAVE1_TRUNG_BINH,
    SLAVE2_TRANG_THAI,
    VN,
    HeThong,
    LoiDuLieu,
    trong_khung,
)


class Gia:
    """Gia lap MQTT publish + Database + dong ho cho HeThong."""

    def __init__(self):
        self.da_publish = []
        self.db = []
        self.dat_gio("12:00")

    def dat_gio(self, gio, giay=0):
        h, m = map(int, gio.split(":"))
        self.luc = datetime(2026, 10, 12, h, m, giay, tzinfo=VN)

    def publish(self, topic, chuoi):
        self.da_publish.append((topic, json.loads(chuoi)))

    def luu_db(self, bang, ban_ghi):
        self.db.append((bang, ban_ghi))


@pytest.fixture
def gia():
    return Gia()


@pytest.fixture
def ht(gia):
    return HeThong(publish=gia.publish, luu_db=gia.luu_db, bay_gio=lambda: gia.luc)


def dk_cuoi(gia):
    return [noi_dung for topic, noi_dung in gia.da_publish if topic == DIEU_KHIEN][-1]


LICH = {"che_do": "tu_dong", "light": {"bat": "18:00", "tat": "06:00"}, "alarm": {"bat": "22:00", "tat": "05:00"}}
NGUONG = {"nhiet_do": "30", "do_am": "80", "den": {"led1": True, "led2": False, "led3": True}}


def nhan_tb(ht, nhiet_do, do_am):
    goi = {"nhiet_do": nhiet_do, "do_am": do_am, "bien_tro": 1.2, "khoang_cach": 50, "so_mau": 20}
    ht.nhan_mqtt(SLAVE1_TRUNG_BINH, json.dumps(goi).encode())


# --- lich ---------------------------------------------------------------
def test_trong_khung():
    assert trong_khung("18:00", "06:00", "23:00")
    assert trong_khung("18:00", "06:00", "05:59")
    assert not trong_khung("18:00", "06:00", "12:00")
    assert trong_khung("08:00", "17:00", "08:00")
    assert not trong_khung("08:00", "17:00", "17:00")


def test_lich_tu_dong_theo_gio(ht, gia):
    ht.luu_lich(LICH)
    gia.dat_gio("19:00")
    assert (ht.tinh_lai()["light"], ht.tinh_lai()["alarm"]) == (1, 0)
    gia.dat_gio("23:00")
    assert (ht.tinh_lai()["light"], ht.tinh_lai()["alarm"]) == (1, 1)
    gia.dat_gio("12:00")
    assert (ht.tinh_lai()["light"], ht.tinh_lai()["alarm"]) == (0, 0)


def test_luu_lich_lan_hai_ghi_de_lan_mot(ht, gia):
    ht.luu_lich(LICH)
    assert ht.tinh_lai()["light"] == 0
    ht.luu_lich({**LICH, "light": {"bat": "11:00", "tat": "13:00"}})
    assert ht.tinh_lai()["light"] == 1
    ht.luu_lich({**LICH, "light": {"bat": "14:00", "tat": "15:00"}})
    assert ht.tinh_lai()["light"] == 0
    assert ht.anh_chup()["lich"]["light"] == {"bat": "14:00", "tat": "15:00"}


def test_luu_lich_cung_gia_tri_van_cap_nhat_luc(ht, gia):
    a = ht.luu_lich(LICH)["luc"]
    gia.dat_gio("12:00", 5)
    b = ht.luu_lich(LICH)["luc"]
    assert (a, b) == ("12:00:00", "12:00:05")
    assert len([1 for bang, _ in gia.db if bang == "cai_dat"]) == 2


def test_chuyen_tu_dong_ve_thu_cong(ht, gia):
    ht.luu_lich(LICH)
    gia.dat_gio("19:00")
    assert ht.tinh_lai()["light"] == 1
    ht.luu_lich({**LICH, "che_do": "tay"})
    assert dk_cuoi(gia)["light"] == 0
    ht.bam_nut("light", 1)
    assert dk_cuoi(gia)["light"] == 1


def test_bam_nut_light_khi_tu_dong_khong_tac_dung(ht, gia):
    ht.luu_lich(LICH)
    ht.bam_nut("light", 1)
    assert dk_cuoi(gia)["light"] == 0


def test_lich_sai_bi_tu_choi_giu_nguyen_cu(ht):
    ht.luu_lich(LICH)
    for sai in (
        {**LICH, "che_do": "abc"},
        {**LICH, "light": {"bat": "", "tat": "06:00"}},
        {**LICH, "alarm": {"bat": "25:00", "tat": "05:00"}},
        {"che_do": "tu_dong"},
        None,
    ):
        with pytest.raises(LoiDuLieu):
            ht.luu_lich(sai)
    lich = ht.anh_chup()["lich"]
    assert lich["che_do"] == "tu_dong" and lich["light"]["bat"] == "18:00"


# --- nut bam ------------------------------------------------------------
def test_bam_nut_publish_dieu_khien(ht, gia):
    ht.bam_nut("led1", 1)
    assert dk_cuoi(gia)["led1"] == 1
    ht.bam_nut("led1", 0)
    assert dk_cuoi(gia)["led1"] == 0


def test_bam_nut_sai_bi_tu_choi(ht):
    with pytest.raises(LoiDuLieu):
        ht.bam_nut("den_la", 1)
    with pytest.raises(LoiDuLieu):
        ht.bam_nut("led1", 5)
    with pytest.raises(LoiDuLieu):
        ht.bam_nut(None, None)


def test_khong_publish_lai_khi_khong_doi(ht, gia):
    ht.bam_nut("relay", 1)
    n = len(gia.da_publish)
    ht.tinh_lai()
    ht.tinh_lai()
    assert len(gia.da_publish) == n


def test_gui_lai_publish_du_khong_doi(ht, gia):
    ht.tinh_lai()
    n = len(gia.da_publish)
    ht.gui_lai()
    assert len(gia.da_publish) == n + 1


# --- nguong -------------------------------------------------------------
def test_nguong_vuot_nhiet_do_bat_den_da_chon(ht, gia):
    ht.luu_nguong(NGUONG)
    nhan_tb(ht, 31, 50)
    d = dk_cuoi(gia)
    assert (d["led1"], d["led2"], d["led3"]) == (1, 0, 1)


def test_nguong_vuot_do_am_cung_bat(ht, gia):
    ht.luu_nguong(NGUONG)
    nhan_tb(ht, 25, 85)
    d = dk_cuoi(gia)
    assert (d["led1"], d["led2"], d["led3"]) == (1, 0, 1)


def test_nguong_khong_vuot_thi_theo_nut(ht, gia):
    ht.bam_nut("led2", 1)
    ht.luu_nguong(NGUONG)
    nhan_tb(ht, 25, 50)
    d = dk_cuoi(gia)
    assert (d["led1"], d["led2"], d["led3"]) == (0, 1, 0)


def test_het_vuot_nguong_thi_tat_lai(ht, gia):
    ht.luu_nguong(NGUONG)
    nhan_tb(ht, 31, 50)
    assert dk_cuoi(gia)["led1"] == 1
    nhan_tb(ht, 25, 50)
    assert dk_cuoi(gia)["led1"] == 0


def test_luu_nguong_bo_chon_het_thi_khong_con_bat(ht, gia):
    ht.luu_nguong(NGUONG)
    nhan_tb(ht, 31, 50)
    assert dk_cuoi(gia)["led1"] == 1
    ht.luu_nguong({"nhiet_do": "30", "do_am": "80", "den": {"led1": False, "led2": False, "led3": False}})
    d = dk_cuoi(gia)
    assert (d["led1"], d["led3"]) == (0, 0)


def test_luu_nguong_thieu_khoa_den_tinh_la_khong_chon(ht):
    ht.luu_nguong(NGUONG)
    n = ht.luu_nguong({"nhiet_do": "30", "do_am": "", "den": {"led2": True}})
    assert n["den"] == {"led1": False, "led2": True, "led3": False}
    assert n["do_am"] is None and n["nhiet_do"] == 30.0


def test_nguong_o_trong_thi_bo_qua_dieu_kien(ht, gia):
    ht.luu_nguong({"nhiet_do": "", "do_am": "", "den": {"led1": True}})
    nhan_tb(ht, 99, 99)
    assert dk_cuoi(gia)["led1"] == 0


def test_nguong_sai_bi_tu_choi(ht):
    ht.luu_nguong(NGUONG)
    for sai in ({"nhiet_do": "abc", "den": {}}, {"nhiet_do": "500", "den": {}}, {"den": [1]}, None):
        with pytest.raises(LoiDuLieu):
            ht.luu_nguong(sai)
    assert ht.anh_chup()["nguong"]["nhiet_do"] == 30.0


def test_trung_binh_co_none_khong_loi(ht, gia):
    ht.luu_nguong(NGUONG)
    nhan_tb(ht, None, None)
    assert dk_cuoi(gia)["led1"] == 0


# --- nhan du lieu tu slave ----------------------------------------------
def test_nhan_trang_thai_luu_db_kem_thoi_gian_master(ht, gia):
    goi = {"led3": 1, "buzzer": 0, "relay": 1, "light": 0, "alarm": None, "lora_ok": False}
    ht.nhan_mqtt(SLAVE2_TRANG_THAI, json.dumps(goi).encode())
    bang, ban_ghi = gia.db[-1]
    assert bang == "trang_thai" and ban_ghi["nguon"] == "slave2"
    assert ban_ghi["led3"] == 1 and ban_ghi["thoi_gian"] == gia.luc
    chup = ht.anh_chup()
    assert chup["slave2"]["trang_thai"]["relay"] == 1
    json.dumps(chup)  # web nhan duoc: khong con datetime trong anh chup


def test_moi_goi_trang_thai_la_1_ban_ghi(ht, gia):
    for _ in range(3):
        ht.nhan_mqtt(SLAVE1_TRANG_THAI, b'{"led1": 1, "led2": 0}')
    assert [bang for bang, _ in gia.db] == ["trang_thai"] * 3


def test_trung_binh_luu_db(ht, gia):
    nhan_tb(ht, 28.5, 60)
    bang, ban_ghi = gia.db[-1]
    assert bang == "trung_binh" and ban_ghi["nguon"] == "slave1" and ban_ghi["nhiet_do"] == 28.5
    assert ht.anh_chup()["slave1"]["luc_trung_binh"] == "12:00:00"


def test_payload_hong_bi_tu_choi(ht, gia):
    with pytest.raises(ValueError):
        ht.nhan_mqtt(SLAVE1_TRANG_THAI, b"khong phai json")
    with pytest.raises(LoiDuLieu):
        ht.nhan_mqtt(SLAVE1_TRANG_THAI, b"[1, 2]")
    assert gia.db == []


def test_topic_la_bi_bo_qua(ht, gia):
    ht.nhan_mqtt("khac/topic", b"{}")
    assert gia.db == []


def test_mat_ket_noi_sau_5_giay(ht, gia):
    ht.nhan_mqtt(SLAVE1_TRANG_THAI, b'{"led1": 1, "led2": 0}')
    assert ht.anh_chup()["slave1"]["ket_noi"] is True
    gia.dat_gio("12:00", 6)
    assert ht.anh_chup()["slave1"]["ket_noi"] is False
    assert ht.anh_chup()["slave2"]["ket_noi"] is False


# --- nap cai dat tu Database khi khoi dong ------------------------------
def test_nap_cai_dat_tu_db(ht):
    ht.nap_cai_dat(
        {"_id": "x", "loai": "lich", **LICH, "luc": "10:00:00"},
        {"_id": "y", "loai": "nguong", "nhiet_do": 30.0, "do_am": None,
         "den": {"led1": True, "led2": False, "led3": False}, "luc": "10:00:01"},
    )
    chup = ht.anh_chup()
    assert chup["lich"]["che_do"] == "tu_dong" and chup["lich"]["luc"] == "10:00:00"
    assert chup["nguong"]["nhiet_do"] == 30.0 and chup["nguong"]["den"]["led1"] is True


def test_nap_cai_dat_hong_thi_giu_mac_dinh(ht):
    ht.nap_cai_dat({"che_do": "???"}, None)
    chup = ht.anh_chup()
    assert chup["lich"]["che_do"] == "tay" and chup["nguong"]["nhiet_do"] is None
