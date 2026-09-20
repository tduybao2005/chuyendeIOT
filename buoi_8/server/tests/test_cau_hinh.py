"""Test tang CAU HINH - doc tu bien moi truong / file .env."""
import pytest

from cau_hinh import CauHinh


def _bien_moi_truong_toi_thieu(**ghi_de):
    gia_tri = {
        "MONGODB_URI": "mongodb+srv://u:p@cluster.mongodb.net/",
        "API_KEY": "khoa-test-du-dai-32-ky-tu-abcdef",
    }
    gia_tri.update(ghi_de)
    return gia_tri


def test_doc_duoc_uri_va_khoa_tu_bien_moi_truong(monkeypatch):
    for ten, gia_tri in _bien_moi_truong_toi_thieu().items():
        monkeypatch.setenv(ten, gia_tri)
    cau_hinh = CauHinh()
    assert cau_hinh.mongodb_uri.startswith("mongodb+srv://")
    assert cau_hinh.api_key == "khoa-test-du-dai-32-ky-tu-abcdef"


def test_co_ten_database_va_collection_mac_dinh(monkeypatch):
    """De nguoi moi chay duoc ngay, chi bat buoc dien URI va API_KEY."""
    for ten, gia_tri in _bien_moi_truong_toi_thieu().items():
        monkeypatch.setenv(ten, gia_tri)
    cau_hinh = CauHinh()
    assert cau_hinh.mongodb_db
    assert cau_hinh.mongodb_collection


def test_doi_duoc_ten_database(monkeypatch):
    for ten, gia_tri in _bien_moi_truong_toi_thieu(MONGODB_DB="db_khac").items():
        monkeypatch.setenv(ten, gia_tri)
    assert CauHinh().mongodb_db == "db_khac"


@pytest.mark.parametrize("thieu", ["MONGODB_URI", "API_KEY"])
def test_thieu_cau_hinh_bat_buoc_thi_bao_loi_ngay_luc_khoi_dong(monkeypatch, thieu):
    """Bao loi luc KHOI DONG, khong phai luc co request dau tien.

    Thieu ma van khoi dong duoc thi server trong nhu dang chay binh thuong,
    den luc demo truoc lop moi loi - luc do khong con thoi gian sua.
    """
    for ten, gia_tri in _bien_moi_truong_toi_thieu().items():
        if ten != thieu:
            monkeypatch.setenv(ten, gia_tri)
    monkeypatch.delenv(thieu, raising=False)
    with pytest.raises(Exception):
        CauHinh()


def test_tu_choi_api_key_qua_ngan(monkeypatch):
    """Khoa 'abc' thi do bang tay vai giay la ra - khong con la bao mat."""
    for ten, gia_tri in _bien_moi_truong_toi_thieu(API_KEY="abc").items():
        monkeypatch.setenv(ten, gia_tri)
    with pytest.raises(Exception):
        CauHinh()
