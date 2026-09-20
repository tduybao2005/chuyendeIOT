"""Test tang MO HINH: validate du lieu truoc khi cho vao Database.

Muc tieu cua tang nay: khong mot ban ghi rac nao lot xuong MongoDB. Cam bien
DHT doc hut hay ai do goi API bang tay sai don vi deu phai bi chan tai day,
chu khong phai phat hien sau khi da luu.
"""
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from mo_hinh import MUI_GIO_VN, DuLieuGui, ThamSoDoc


# ---------------------------------------------------------------------------
# DuLieuGui - du lieu Pi gui len
# ---------------------------------------------------------------------------
def test_nhan_du_lieu_hop_le():
    du_lieu = DuLieuGui(
        ten_thiet_bi="pi4-tdbao", nhiet_do=28.5, do_am=70.0,
        led1=0, led2=1, led3=0,
    )
    assert du_lieu.ten_thiet_bi == "pi4-tdbao"
    assert du_lieu.nhiet_do == 28.5
    assert (du_lieu.led1, du_lieu.led2, du_lieu.led3) == (0, 1, 0)


@pytest.mark.parametrize("dau_vao,mong_doi", [
    ("1", 1), ("0", 0),
    ("true", 1), ("false", 0),
    ("on", 1), ("off", 0),
    (True, 1), (False, 0),
    (1, 1), (0, 0),
])
def test_trang_thai_led_nhan_nhieu_kieu_viet(dau_vao, mong_doi):
    """form-urlencoded chi gui duoc CHUOI, json gui duoc bool/int.

    Ca hai duong deu phai ra cung mot gia tri 0/1 luu xuong Database.
    """
    du_lieu = DuLieuGui(
        ten_thiet_bi="pi", nhiet_do=25, do_am=50,
        led1=dau_vao, led2=0, led3=0,
    )
    assert du_lieu.led1 == mong_doi


@pytest.mark.parametrize("gia_tri_xau", ["2", 2, -1, "bat_den", ""])
def test_tu_choi_trang_thai_led_khong_phai_0_hoac_1(gia_tri_xau):
    with pytest.raises(ValidationError):
        DuLieuGui(ten_thiet_bi="pi", nhiet_do=25, do_am=50,
                  led1=gia_tri_xau, led2=0, led3=0)


@pytest.mark.parametrize("nhiet_do_xau", [-50, 200])
def test_tu_choi_nhiet_do_ngoai_dai_cam_bien(nhiet_do_xau):
    with pytest.raises(ValidationError):
        DuLieuGui(ten_thiet_bi="pi", nhiet_do=nhiet_do_xau, do_am=50,
                  led1=0, led2=0, led3=0)


@pytest.mark.parametrize("do_am_xau", [-1, 101])
def test_tu_choi_do_am_ngoai_khoang_0_100(do_am_xau):
    with pytest.raises(ValidationError):
        DuLieuGui(ten_thiet_bi="pi", nhiet_do=25, do_am=do_am_xau,
                  led1=0, led2=0, led3=0)


def test_tu_choi_ten_thiet_bi_rong():
    with pytest.raises(ValidationError):
        DuLieuGui(ten_thiet_bi="   ", nhiet_do=25, do_am=50,
                  led1=0, led2=0, led3=0)


def test_ten_thiet_bi_duoc_cat_khoang_trang_thua():
    du_lieu = DuLieuGui(ten_thiet_bi="  pi4-tdbao  ", nhiet_do=25, do_am=50,
                        led1=0, led2=0, led3=0)
    assert du_lieu.ten_thiet_bi == "pi4-tdbao"


def test_khong_co_truong_api_key_trong_mo_hinh():
    """De bai: KHONG duoc luu API_KEY vao Database.

    Chan ngay tu mo hinh: neu client co gui kem api_key trong body thi truong
    do khong ton tai trong DuLieuGui nen khong the di tiep xuong Database.
    """
    assert "api_key" not in DuLieuGui.model_fields
    du_lieu = DuLieuGui.model_validate({
        "ten_thiet_bi": "pi", "nhiet_do": 25, "do_am": 50,
        "led1": 0, "led2": 0, "led3": 0, "api_key": "bi-mat",
    })
    assert not hasattr(du_lieu, "api_key")
    assert "api_key" not in du_lieu.model_dump()


# ---------------------------------------------------------------------------
# ThamSoDoc - tham so cua API doc
# ---------------------------------------------------------------------------
def test_mac_dinh_doc_10_ban_ghi_gan_nhat():
    tham_so = ThamSoDoc()
    assert tham_so.n == 10
    assert tham_so.tu is None and tham_so.den is None


@pytest.mark.parametrize("n_xau", [0, -5, 10_000])
def test_tu_choi_so_ban_ghi_vo_ly(n_xau):
    with pytest.raises(ValidationError):
        ThamSoDoc(n=n_xau)


def test_thoi_gian_khong_ghi_mui_gio_duoc_hieu_la_gio_viet_nam():
    """Nguoi cham bai go gio theo dong ho VN, khong ai go kem '+07:00'.

    Server luu UTC nhung phai hieu dung y nguoi go, neu khong thi truy van
    lech 7 tieng va tra ve rong - loi rat kho nhan ra.
    """
    tham_so = ThamSoDoc(tu="2026-09-20T10:00:00")
    assert tham_so.tu.utcoffset() == timedelta(hours=7)
    assert tham_so.tu == datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)


def test_thoi_gian_co_ghi_mui_gio_duoc_giu_nguyen():
    tham_so = ThamSoDoc(tu="2026-09-20T10:00:00+00:00")
    assert tham_so.tu == datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)


def test_tu_choi_khoang_thoi_gian_nguoc():
    with pytest.raises(ValidationError):
        ThamSoDoc(tu="2026-09-20T11:00:00", den="2026-09-20T10:00:00")


def test_mui_gio_vn_la_cong_7():
    assert datetime(2026, 9, 20, tzinfo=MUI_GIO_VN).utcoffset() == timedelta(hours=7)
