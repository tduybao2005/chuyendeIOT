"""Test tang BAO MAT - API_KEY.

De bai muc do 3: "co ho tro bao mat dang API_KEY (khong luu API vao
Database)". Hai ve, test ca hai:
  - ve BAO MAT: khong co khoa dung thi khong vao duoc  -> file nay
  - ve KHONG LUU: test_kho_du_lieu.py + test_api.py
"""
import pytest

from bao_mat import khoa_hop_le, lay_khoa_tu_request


# ---------------------------------------------------------------------------
# khoa_hop_le - so sanh khoa
# ---------------------------------------------------------------------------
def test_dung_khoa_thi_cho_qua():
    assert khoa_hop_le("bi-mat-123", khoa_that="bi-mat-123") is True


@pytest.mark.parametrize("khoa_sai", [
    "bi-mat-124",       # sai 1 ky tu
    "bi-mat-123 ",      # thua khoang trang
    "BI-MAT-123",       # khac hoa thuong
    "bi-mat",           # la tien to dung cua khoa that
    "",
    None,
])
def test_sai_khoa_thi_chan(khoa_sai):
    assert khoa_hop_le(khoa_sai, khoa_that="bi-mat-123") is False


def test_server_chua_dat_khoa_thi_chan_het():
    """Fail closed: cau hinh thieu API_KEY thi KHONG duoc mo toang cua.

    Neu tra True khi khoa_that rong thi mot lan quen dien API_KEY trong .env
    se bien server thanh cong khai ma khong co dau hieu gi bao.
    """
    assert khoa_hop_le("bat_ky", khoa_that="") is False
    assert khoa_hop_le("", khoa_that="") is False
    assert khoa_hop_le(None, khoa_that=None) is False


# ---------------------------------------------------------------------------
# lay_khoa_tu_request - nhan khoa tu nhieu duong
# ---------------------------------------------------------------------------
def test_uu_tien_header_x_api_key():
    assert lay_khoa_tu_request(header="tu-header", query="tu-query") == "tu-header"


def test_chap_nhan_khoa_qua_query_de_test_bang_trinh_duyet():
    """Trinh duyet khong dat duoc header, nen cho phep ?api_key=... de demo."""
    assert lay_khoa_tu_request(header=None, query="tu-query") == "tu-query"


def test_khong_gui_khoa_nao_thi_tra_ve_none():
    assert lay_khoa_tu_request(header=None, query=None) is None
