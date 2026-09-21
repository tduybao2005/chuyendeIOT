"""Test LOGIC LED - den sang duoi.

Yeu cau: 3 LED sang DUOI, moi 1 giay chuyen sang den ke tiep, luon chi mot
den sang. Trang thai 3 den do duoc day len server, va terminal in lai gia
tri DOC VE TU SERVER chu khong in bien cuc bo.

Phan nay thuan tinh toan nen test duoc tren may tinh, khong can Pi va khong
can cam den that. Phan cham vao chan GPIO thi phai kiem tra thuc te tren
phan cung.
"""
import pytest

from logic_led import SO_DEN, den_dang_sang, mo_ta_den


# ---------------------------------------------------------------------------
# den_dang_sang - tu so buoc ra trang thai 3 den
#
# Quy uoc thu tu tra ve: (led1_do, led2_vang, led3_xanh)
#   led1 = LED do   cong D16
#   led2 = LED vang cong D22
#   led3 = LED xanh cong D24
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("buoc,mong_doi", [
    (0, (1, 0, 0)),     # do
    (1, (0, 1, 0)),     # vang
    (2, (0, 0, 1)),     # xanh
])
def test_ba_buoc_dau_sang_lan_luot_do_vang_xanh(buoc, mong_doi):
    assert den_dang_sang(buoc) == mong_doi


@pytest.mark.parametrize("buoc,mong_doi", [
    (3, (1, 0, 0)),     # quay ve den do
    (4, (0, 1, 0)),
    (5, (0, 0, 1)),
    (99, (1, 0, 0)),    # 99 = 33 vong tron chan
])
def test_het_ba_den_thi_quay_lai_tu_dau(buoc, mong_doi):
    """Duoi la vong tron: het den cuoi phai quay ve den dau, khong dung lai."""
    assert den_dang_sang(buoc) == mong_doi


@pytest.mark.parametrize("buoc", range(12))
def test_luon_luon_chi_co_dung_mot_den_sang(buoc):
    """Sang duoi nghia la mot diem sang chay doc day den.

    Neu co luc hai den cung sang (hoac khong den nao sang) thi khong con la
    duoi nua - nhin vao khong biet diem sang dang o dau.
    """
    assert sum(den_dang_sang(buoc)) == 1


def test_mot_vong_day_du_di_qua_ca_ba_den_dung_mot_lan():
    trang_thai = [den_dang_sang(b) for b in range(SO_DEN)]
    assert sorted(trang_thai) == [(0, 0, 1), (0, 1, 0), (1, 0, 0)]


def test_hai_buoc_lien_tiep_khong_bao_gio_giong_nhau():
    """Hai buoc giong nhau thi den dung yen mot nhip - duoi bi khuc khuu."""
    for buoc in range(12):
        assert den_dang_sang(buoc) != den_dang_sang(buoc + 1)


def test_co_dung_ba_den():
    assert SO_DEN == 3


# ---------------------------------------------------------------------------
# mo_ta_den - chu in kem ra terminal cho de doc
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("trang_thai,tu_khoa", [
    ((1, 0, 0), "DO"),
    ((0, 1, 0), "VANG"),
    ((0, 0, 1), "XANH"),
])
def test_mo_ta_den_dang_sang_bang_chu(trang_thai, tu_khoa):
    assert mo_ta_den(trang_thai) == tu_khoa


def test_mo_ta_khi_khong_den_nao_sang():
    """Server tra ve 000 (vi du ban ghi cu luc chua chay duoi) van in duoc."""
    assert mo_ta_den((0, 0, 0)) == "TAT"


def test_mo_ta_khi_nhieu_den_cung_sang():
    """Khong xay ra trong chuong trinh nay, nhung ham khong duoc no.

    mo_ta_den() con duoc dung de in ban ghi DOC VE TU SERVER, ma du lieu do
    co the do chuong trinh khac gui len voi to hop bat ky.
    """
    assert mo_ta_den((1, 1, 0)) == "DO+VANG"
    assert mo_ta_den((1, 1, 1)) == "DO+VANG+XANH"
