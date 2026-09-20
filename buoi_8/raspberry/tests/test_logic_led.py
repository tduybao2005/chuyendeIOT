"""Test LOGIC LED - phan thuan tinh toan cua chuong trinh Pi.

Phan nay tach rieng khoi GPIO de test duoc tren may tinh, khong can Pi va
khong can cam den that. Rieng phan cham vao chan GPIO va doc cam bien DHT
thi khong test tu dong duoc - phai chay thuc te tren Pi.
"""
import pytest

from logic_led import (NGUONG_AM, NGUONG_NONG, mo_ta_muc_nhiet,
                       quyet_dinh_led)


# ---------------------------------------------------------------------------
# quyet_dinh_led - tu nhiet do ra trang thai 3 LED
#
# Quy uoc thu tu tra ve: (led1_do, led2_vang, led3_xanh)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nhiet_do", [15.0, 25.0, 27.9])
def test_troi_mat_thi_sang_led_xanh(nhiet_do):
    assert quyet_dinh_led(nhiet_do) == (0, 0, 1)


@pytest.mark.parametrize("nhiet_do", [28.0, 30.0, 31.9])
def test_troi_am_thi_sang_led_vang(nhiet_do):
    assert quyet_dinh_led(nhiet_do) == (0, 1, 0)


@pytest.mark.parametrize("nhiet_do", [32.0, 35.0, 50.0])
def test_troi_nong_thi_sang_led_do(nhiet_do):
    assert quyet_dinh_led(nhiet_do) == (1, 0, 0)


@pytest.mark.parametrize("nhiet_do", [10.0, 28.0, 32.0, 45.0])
def test_luon_luon_chi_co_dung_mot_led_sang(nhiet_do):
    """Nhin vao bang den la doc duoc ngay muc nhiet, khong phai giai ma."""
    assert sum(quyet_dinh_led(nhiet_do)) == 1


def test_ranh_gioi_nguong_thuoc_ve_muc_cao_hon():
    """Dung dung nguong thi tinh la da len muc tren - khong de ho khoang nao.

    Neu dinh nghia mo ho o diem ranh gioi thi co gia tri nhiet do khong LED
    nao sang, va loi do chi lo ra dung luc nhiet do roi vao so do.
    """
    assert quyet_dinh_led(NGUONG_AM) == (0, 1, 0)
    assert quyet_dinh_led(NGUONG_NONG) == (1, 0, 0)
    assert quyet_dinh_led(NGUONG_AM - 0.1) == (0, 0, 1)
    assert quyet_dinh_led(NGUONG_NONG - 0.1) == (0, 1, 0)


def test_hai_nguong_theo_dung_thu_tu():
    assert NGUONG_AM < NGUONG_NONG


# ---------------------------------------------------------------------------
# mo_ta_muc_nhiet - chu in kem ra terminal
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nhiet_do,tu_khoa", [
    (20.0, "MAT"), (30.0, "AM"), (40.0, "NONG"),
])
def test_mo_ta_muc_nhiet_bang_chu(nhiet_do, tu_khoa):
    assert tu_khoa in mo_ta_muc_nhiet(nhiet_do).upper()
