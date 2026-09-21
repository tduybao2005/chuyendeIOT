"""Test ghi NHAT KY CSV.

Ghi lai du lieu DOC VE TU SERVER thanh file .csv, mo duoc bang Excel /
LibreOffice de ve do thi dua vao bao cao.

Ghi cai DOC VE chu khong ghi bien cuc bo: nho vay file csv la bang chung
doc lap rang du lieu da thuc su len toi server va quay ve duoc - trung khop
voi nhung gi nam trong MongoDB Atlas.
"""
import csv
from datetime import datetime

import pytest

from nhat_ky_csv import COT, NhatKyCsv

BAN_GHI = {
    "id": "6620f1a2b3c4d5e6f7890123",
    "ten_thiet_bi": "pi4-tdbao",
    "nhiet_do": 26.0,
    "do_am": 73.0,
    "led1": 1,
    "led2": 0,
    "led3": 0,
    "thoi_gian_gui": "2026-09-21T07:34:03.123000+07:00",
}


def _doc_csv(duong_dan):
    with open(duong_dan, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


# ---------------------------------------------------------------------------
# Dong tieu de
# ---------------------------------------------------------------------------
def test_file_moi_co_dong_tieu_de(tmp_path):
    nhat_ky = NhatKyCsv(tmp_path)
    duong_dan = nhat_ky.ghi(BAN_GHI)
    assert _doc_csv(duong_dan)[0] == COT


def test_chi_ghi_tieu_de_dung_mot_lan(tmp_path):
    """Ghi tieu de lai moi lan thi file day dong rac, Excel doc ra sai het."""
    nhat_ky = NhatKyCsv(tmp_path)
    for _ in range(3):
        duong_dan = nhat_ky.ghi(BAN_GHI)
    dong = _doc_csv(duong_dan)
    assert dong[0] == COT
    assert len(dong) == 4                      # 1 tieu de + 3 ban ghi
    assert all(d[0] != COT[0] for d in dong[1:])


def test_mo_lai_chuong_trinh_khong_ghi_lai_tieu_de(tmp_path):
    """Pi khoi dong lai (systemd dung lai) thi phai GHI TIEP, khong de len.

    Tao mot doi tuong NhatKyCsv hoan toan moi tro toi cung thu muc - dung
    nhu khi tien trinh chet va duoc khoi dong lai.
    """
    NhatKyCsv(tmp_path).ghi(BAN_GHI)
    duong_dan = NhatKyCsv(tmp_path).ghi(BAN_GHI)
    dong = _doc_csv(duong_dan)
    assert len(dong) == 3                      # 1 tieu de + 2 ban ghi
    assert dong.count(COT) == 1


# ---------------------------------------------------------------------------
# Noi dung ban ghi
# ---------------------------------------------------------------------------
def test_ghi_dung_gia_tri_vao_dung_cot(tmp_path):
    duong_dan = NhatKyCsv(tmp_path).ghi(BAN_GHI)
    tieu_de, dong = _doc_csv(duong_dan)
    o = dict(zip(tieu_de, dong))
    assert o["id"] == "6620f1a2b3c4d5e6f7890123"
    assert o["ten_thiet_bi"] == "pi4-tdbao"
    assert o["nhiet_do"] == "26.0"
    assert o["do_am"] == "73.0"
    assert (o["led1"], o["led2"], o["led3"]) == ("1", "0", "0")


def test_thoi_gian_ghi_dang_de_doc_cho_excel(tmp_path):
    """'2026-09-21T07:34:03.123000+07:00' Excel khong hieu la thoi gian.

    Doi thanh '2026-09-21 07:34:03' thi Excel nhan ra ngay va ve do thi
    theo truc thoi gian duoc.
    """
    duong_dan = NhatKyCsv(tmp_path).ghi(BAN_GHI)
    o = dict(zip(*_doc_csv(duong_dan)))
    assert o["thoi_gian_gui"] == "2026-09-21 07:34:03"


def test_server_tra_thieu_truong_thi_de_o_trong_chu_khong_no(tmp_path):
    """Chuong trinh chay lien tuc nhieu gio, khong duoc chet vi mot ban ghi la."""
    duong_dan = NhatKyCsv(tmp_path).ghi({"nhiet_do": 26.0})
    o = dict(zip(*_doc_csv(duong_dan)))
    assert o["nhiet_do"] == "26.0"
    assert o["ten_thiet_bi"] == ""
    assert o["id"] == ""


def test_cot_co_du_thong_tin_de_bai_yeu_cau():
    """De bai: ban ghi phai co ID, thoi gian gui len, ten thiet bi."""
    for bat_buoc in ("id", "thoi_gian_gui", "ten_thiet_bi",
                     "nhiet_do", "do_am", "led1", "led2", "led3"):
        assert bat_buoc in COT


def test_khong_ghi_api_key_vao_file_csv():
    """De bai: khong luu API vao Database - file log cung khong duoc chua."""
    assert not any("api" in c.lower() or "key" in c.lower() for c in COT)


# ---------------------------------------------------------------------------
# Moi ngay mot file
# ---------------------------------------------------------------------------
def test_ten_file_co_ngay_thang(tmp_path):
    duong_dan = NhatKyCsv(tmp_path, dong_ho=lambda: datetime(2026, 9, 21)).ghi(BAN_GHI)
    assert duong_dan.name == "du_lieu_2026-09-21.csv"


def test_sang_ngay_moi_thi_tu_mo_file_moi(tmp_path):
    """Nhip 1 giay = 86400 dong moi ngay. Don het vao mot file thi chay vai
    ngay la file nang hang chuc MB, mo bang Excel rat cham va day the nho.

    Cat theo ngay thi moi file co kich thuoc biet truoc, va van giu duoc
    dong tieu de rieng cho tung file (xoay vong kieu log thuong se cat mat
    tieu de).
    """
    ngay = datetime(2026, 9, 21, 23, 59, 59)
    nhat_ky = NhatKyCsv(tmp_path, dong_ho=lambda: ngay)
    dan_hom_truoc = nhat_ky.ghi(BAN_GHI)

    ngay = datetime(2026, 9, 22, 0, 0, 1)
    dan_hom_sau = nhat_ky.ghi(BAN_GHI)

    assert dan_hom_truoc != dan_hom_sau
    assert _doc_csv(dan_hom_sau)[0] == COT       # file moi co tieu de rieng
    assert len(_doc_csv(dan_hom_sau)) == 2


def test_tu_tao_thu_muc_neu_chua_co(tmp_path):
    thu_muc = tmp_path / "chua" / "ton" / "tai"
    duong_dan = NhatKyCsv(thu_muc).ghi(BAN_GHI)
    assert duong_dan.exists()
