"""Test phan THUAN LOGIC cua tang kho du lieu.

Ba ham duoi day quyet dinh du lieu nam the nao trong MongoDB va cau truy van
gui xuong MongoDB ra sao. Chung khong can ket noi mang nen test duoc offline;
phan thuc su noi chuyen voi Atlas thi kiem tra bang kiem_tra_atlas.py.
"""
from datetime import datetime, timezone

from bson import ObjectId

from kho_du_lieu import chuan_bi_ban_ghi, doi_sang_ban_ghi, dung_bo_loc
from mo_hinh import MUI_GIO_VN, BanGhi, DuLieuGui, ThamSoDoc


# ---------------------------------------------------------------------------
# dung_bo_loc - dich ThamSoDoc thanh cau loc cua MongoDB
# ---------------------------------------------------------------------------
def test_khong_co_dieu_kien_thi_bo_loc_rong():
    assert dung_bo_loc(ThamSoDoc()) == {}


def test_loc_theo_ten_thiet_bi():
    assert dung_bo_loc(ThamSoDoc(ten_thiet_bi="pi4-tdbao")) == {
        "ten_thiet_bi": "pi4-tdbao"
    }


def test_loc_tu_mot_moc_thoi_gian():
    bo_loc = dung_bo_loc(ThamSoDoc(tu="2026-09-20T10:00:00"))
    assert bo_loc == {
        "thoi_gian_gui": {"$gte": datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)}
    }


def test_loc_trong_mot_khoang_thoi_gian():
    bo_loc = dung_bo_loc(ThamSoDoc(tu="2026-09-20T10:00:00",
                                   den="2026-09-20T11:30:00"))
    assert bo_loc == {
        "thoi_gian_gui": {
            "$gte": datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc),
            "$lte": datetime(2026, 9, 20, 4, 30, tzinfo=timezone.utc),
        }
    }


def test_loc_ghep_ca_thiet_bi_lan_thoi_gian():
    bo_loc = dung_bo_loc(ThamSoDoc(ten_thiet_bi="pi", den="2026-09-20T11:00:00"))
    assert set(bo_loc) == {"ten_thiet_bi", "thoi_gian_gui"}


def test_moc_thoi_gian_luon_duoc_doi_sang_utc():
    """Database luu UTC nen cau loc cung phai la UTC, khong the gui gio VN.

    Neu quen doi thi so sanh lech dung 7 tieng va truy van tra ve rong.
    """
    moc = dung_bo_loc(ThamSoDoc(tu="2026-09-20T10:00:00"))["thoi_gian_gui"]["$gte"]
    assert moc.tzinfo is not None
    assert moc.utcoffset().total_seconds() == 0


# ---------------------------------------------------------------------------
# chuan_bi_ban_ghi - tu du lieu client thanh tai lieu luu xuong MongoDB
# ---------------------------------------------------------------------------
def _du_lieu_mau(**ghi_de):
    tham_so = dict(ten_thiet_bi="pi4-tdbao", nhiet_do=28.5, do_am=70.0,
                   led1=0, led2=1, led3=0)
    tham_so.update(ghi_de)
    return DuLieuGui(**tham_so)


def test_ban_ghi_co_du_thong_tin_de_bai_yeu_cau():
    """De bai: phai co ID, thoi gian gui len, ten thiet bi."""
    luc = datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)
    tai_lieu = chuan_bi_ban_ghi(_du_lieu_mau(), luc)

    assert tai_lieu["ten_thiet_bi"] == "pi4-tdbao"
    assert tai_lieu["thoi_gian_gui"] == luc
    assert tai_lieu["nhiet_do"] == 28.5
    assert tai_lieu["do_am"] == 70.0
    assert (tai_lieu["led1"], tai_lieu["led2"], tai_lieu["led3"]) == (0, 1, 0)


def test_khong_bao_gio_luu_api_key_xuong_database():
    """De bai muc do 3: 'khong luu API vao Database'."""
    tai_lieu = chuan_bi_ban_ghi(_du_lieu_mau(), datetime.now(timezone.utc))
    assert not any("api" in khoa.lower() for khoa in tai_lieu)
    assert not any("key" in khoa.lower() for khoa in tai_lieu)


def test_thoi_gian_luu_xuong_luon_la_utc():
    gio_vn = datetime(2026, 9, 20, 10, 0, tzinfo=MUI_GIO_VN)
    tai_lieu = chuan_bi_ban_ghi(_du_lieu_mau(), gio_vn)
    assert tai_lieu["thoi_gian_gui"].utcoffset().total_seconds() == 0
    assert tai_lieu["thoi_gian_gui"] == datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# doi_sang_ban_ghi - tu tai lieu MongoDB thanh ban ghi tra ve client
# ---------------------------------------------------------------------------
def test_id_cua_mongodb_duoc_doi_thanh_chuoi():
    """_id cua MongoDB la ObjectId, khong serialize thang ra JSON duoc."""
    ma = ObjectId()
    ban_ghi = doi_sang_ban_ghi({
        "_id": ma, "ten_thiet_bi": "pi", "nhiet_do": 25.0, "do_am": 50.0,
        "led1": 1, "led2": 0, "led3": 0,
        "thoi_gian_gui": datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc),
    })
    assert isinstance(ban_ghi, BanGhi)
    assert ban_ghi.id == str(ma)
    assert "_id" not in ban_ghi.model_dump()


def test_thoi_gian_tra_ve_theo_gio_viet_nam():
    """MongoDB tra datetime KHONG co tzinfo (BSON ngam dinh UTC).

    Phai dan nhan UTC roi doi sang +07:00, neu khong nguoi doc terminal se
    thay gio lech 7 tieng so voi dong ho tren tuong.
    """
    ban_ghi = doi_sang_ban_ghi({
        "_id": ObjectId(), "ten_thiet_bi": "pi", "nhiet_do": 25.0, "do_am": 50.0,
        "led1": 0, "led2": 0, "led3": 0,
        "thoi_gian_gui": datetime(2026, 9, 20, 3, 0),   # khong tzinfo, la UTC
    })
    assert ban_ghi.thoi_gian_gui.hour == 10
    assert ban_ghi.thoi_gian_gui.utcoffset().total_seconds() == 7 * 3600
