"""
Test tang GIAO TIEP cua chuong trinh Pi - phan khong cham mang.

Gom ba viec: loc du lieu cam bien rac, dong goi tin gui len, va dinh dang
ban ghi DOC VE TU SERVER de in ra terminal.

Diem quan trong cua bai nay: terminal phai in du lieu LAY VE TU SERVER, chu
khong phai in lai bien cuc bo vua doc duoc tu cam bien. Vi vay ham dinh dang
nhan vao dung cai dict ma server tra ve - neu server khong tra truong nao
thi o day se lo ra ngay.
"""
import pytest

from giao_tiep import (cam_bien_hop_le, dinh_dang_ban_ghi,
                       dinh_dang_danh_sach, dung_goi_tin)

BAN_GHI_TU_SERVER = {
    "id": "6620f1a2b3c4d5e6f7890123",
    "ten_thiet_bi": "pi4-tdbao",
    "nhiet_do": 28.5,
    "do_am": 70.0,
    "led1": 0,
    "led2": 1,
    "led3": 0,
    "thoi_gian_gui": "2026-09-20T10:00:00+07:00",
}


# ---------------------------------------------------------------------------
# cam_bien_hop_le - loc gia tri rac TRUOC khi gui len
# ---------------------------------------------------------------------------
def test_gia_tri_binh_thuong_thi_hop_le():
    assert cam_bien_hop_le(28.5, 70.0) is True


@pytest.mark.parametrize("nhiet_do,do_am", [
    (None, 70.0),       # DHT doc hut
    (28.5, None),
    (None, None),
    (1.0, 3.0),         # dat sai loai DHT11/DHT22 -> ra so vo nghia
    (-10.0, 70.0),      # ngoai dai
    (80.0, 70.0),
    (28.5, 5.0),
    (28.5, 120.0),
])
def test_gia_tri_rac_bi_loai(nhiet_do, do_am):
    assert cam_bien_hop_le(nhiet_do, do_am) is False


# ---------------------------------------------------------------------------
# dung_goi_tin - dong goi du lieu gui len server
# ---------------------------------------------------------------------------
def test_goi_tin_co_du_5_gia_tri_de_bai_yeu_cau():
    """De bai: nhiet do, do am, va trang thai cua 3 LED."""
    goi_tin = dung_goi_tin("pi4-tdbao", 28.5, 70.0, (0, 1, 0))
    assert goi_tin == {
        "ten_thiet_bi": "pi4-tdbao",
        "nhiet_do": 28.5,
        "do_am": 70.0,
        "led1": 0, "led2": 1, "led3": 0,
    }


def test_goi_tin_khong_chua_api_key():
    """API_KEY di theo header, KHONG di trong than goi tin.

    De bai: 'khong luu API vao Database'. Khoa nam trong than goi tin thi no
    di thang vao cho server ghi ban ghi - chan ngay tu day la chac nhat.
    """
    goi_tin = dung_goi_tin("pi", 25.0, 50.0, (1, 0, 0))
    assert not any("api" in khoa.lower() or "key" in khoa.lower() for khoa in goi_tin)


def test_goi_tin_lam_tron_so_do_ve_mot_chu_so_thap_phan():
    """DHT chi chinh xac toi ~1 C / 1 %, in 28.500000000000004 la vo nghia."""
    goi_tin = dung_goi_tin("pi", 28.456789, 70.123456, (0, 1, 0))
    assert goi_tin["nhiet_do"] == 28.5
    assert goi_tin["do_am"] == 70.1


# ---------------------------------------------------------------------------
# dinh_dang_ban_ghi - in ban ghi DOC VE TU SERVER
# ---------------------------------------------------------------------------
def test_in_du_thong_tin_de_bai_yeu_cau():
    """Phai thay duoc ID, thoi gian gui, ten thiet bi, va 5 gia tri do."""
    dong = dinh_dang_ban_ghi(BAN_GHI_TU_SERVER)
    assert "6620f1a2b3c4d5e6f7890123" in dong
    assert "pi4-tdbao" in dong
    assert "28.5" in dong
    assert "70" in dong
    assert "10:00:00" in dong


def test_in_trang_thai_3_led():
    dong = dinh_dang_ban_ghi(BAN_GHI_TU_SERVER)
    assert "010" in dong.replace(" ", "")


def test_khong_no_khi_server_tra_thieu_truong():
    """Server phien ban cu / loi mang cat ngan thi van phai in duoc gi do.

    Chuong trinh Pi chay lien tuc nhieu gio; nem KeyError giua chung thi
    tien trinh chet han, mat het du lieu tu do tro di. In '?' roi chay tiep
    thi chi hong mot dong log.
    """
    dong = dinh_dang_ban_ghi({"nhiet_do": 28.5})
    assert "28.5" in dong
    assert "?" in dong


def test_in_thoi_gian_de_doc_chu_khong_phai_chuoi_iso_tho():
    """'2026-09-20T10:00:00+07:00' doc kho, doi thanh '2026-09-20 10:00:00'."""
    dong = dinh_dang_ban_ghi(BAN_GHI_TU_SERVER)
    assert "2026-09-20 10:00:00" in dong
    assert "T10:00" not in dong


# ---------------------------------------------------------------------------
# dinh_dang_danh_sach - in N ban ghi doc ve
# ---------------------------------------------------------------------------
def test_in_moi_ban_ghi_mot_dong():
    dong = dinh_dang_danh_sach([BAN_GHI_TU_SERVER, BAN_GHI_TU_SERVER])
    assert dong.count("6620f1a2b3c4d5e6f7890123") == 2


def test_in_danh_sach_rong_van_co_thong_bao():
    ket_qua = dinh_dang_danh_sach([])
    assert ket_qua.strip() != ""


# ---------------------------------------------------------------------------
# kiem_tra_phan_hoi - phan loai loi tu server
#
# Phan biet hai loai loi hoan toan khac nhau:
#   - LoiCauHinh : sai API_KEY. Thu lai 100 lan cung van sai -> bao NGAY.
#   - LoiTamThoi : mang chap chon, server dang khoi dong lai -> thu lai.
# Gop chung mot loai thi sai khoa cung phai cho het 15 lan thu (75 giay) moi
# biet, ma ly do that thi da ro ngay tu lan dau.
# ---------------------------------------------------------------------------
class _PhanHoiGia:
    """Ban gia cua doi tuong Response cua requests - du cho ham can dung."""

    def __init__(self, status_code, du_lieu=None, text=""):
        self.status_code = status_code
        self._du_lieu = du_lieu
        self.text = text

    def json(self):
        if self._du_lieu is None:
            raise ValueError("khong phai json")
        return self._du_lieu


def test_phan_hoi_thanh_cong_thi_tra_ve_than():
    from giao_tiep import kiem_tra_phan_hoi
    phan_hoi = _PhanHoiGia(200, {"thanh_cong": True, "ban_ghi": {"id": "abc"}})
    assert kiem_tra_phan_hoi(phan_hoi) == {"thanh_cong": True, "ban_ghi": {"id": "abc"}}


@pytest.mark.parametrize("ma", [401, 403])
def test_sai_api_key_la_loi_cau_hinh_khong_thu_lai(ma):
    from giao_tiep import LoiCauHinh, kiem_tra_phan_hoi
    with pytest.raises(LoiCauHinh):
        kiem_tra_phan_hoi(_PhanHoiGia(ma, {"detail": "Thieu hoac sai API_KEY."}))


@pytest.mark.parametrize("ma", [500, 502, 503, 504])
def test_server_loi_la_loi_tam_thoi_nen_thu_lai(ma):
    from giao_tiep import LoiTamThoi, kiem_tra_phan_hoi
    with pytest.raises(LoiTamThoi):
        kiem_tra_phan_hoi(_PhanHoiGia(ma, {"detail": "server dang khoi dong"}))


def test_du_lieu_sai_422_la_loi_cau_hinh():
    """422 nghia la chuong trinh gui sai dinh dang - thu lai cung the."""
    from giao_tiep import LoiCauHinh, kiem_tra_phan_hoi
    with pytest.raises(LoiCauHinh):
        kiem_tra_phan_hoi(_PhanHoiGia(422, {"detail": [{"msg": "sai"}]}))


def test_thong_bao_loi_keo_ra_ly_do_server_giai_thich():
    """'HTTP 401' khong noi len gi; server da giai thich san trong 'detail'."""
    from giao_tiep import LoiCauHinh, kiem_tra_phan_hoi
    with pytest.raises(LoiCauHinh, match="Thieu hoac sai API_KEY"):
        kiem_tra_phan_hoi(_PhanHoiGia(401, {"detail": "Thieu hoac sai API_KEY."}))


def test_phan_hoi_loi_khong_phai_json_van_bao_duoc():
    """Nginx / proxy chen giua co the tra ve HTML thay vi json."""
    from giao_tiep import LoiTamThoi, kiem_tra_phan_hoi
    with pytest.raises(LoiTamThoi, match="502"):
        kiem_tra_phan_hoi(_PhanHoiGia(502, du_lieu=None, text="<html>Bad Gateway</html>"))


# ---------------------------------------------------------------------------
# tao_phien - phien HTTP chiu duoc ket noi keep-alive bi rot
#
# LOI THAT DA GAP (2026-09-21, chay tren pi4-tdbao):
#   Nhip gui cua Pi la 5 giay, ma timeout_keep_alive mac dinh cua uvicorn
#   CUNG la 5 giay. Giua hai chu ky, ket noi nam khong dung 5 giay - server
#   dong no dung luc requests.Session dinh dung lai -> server dong ma khong
#   tra loi gi -> RemoteDisconnected.
#
#   Do duoc tu Pi qua WiFi: nhip 1s -> 0/12 loi, nhip 5s -> 5/12 loi.
#
# Sua o HAI tang:
#   - Goc re: server dat timeout_keep_alive dai hon han moi nhip client
#     (chay_server.py).
#   - Phong tuyen 2: phien cua client tu mo ket noi moi va thu lai - dung
#     duoc voi bat ky server nao, ke ca server nguoi khac dung.
# ---------------------------------------------------------------------------
import json as _json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _MayChuRotKetNoiLanDau(BaseHTTPRequestHandler):
    """Dong phang ket noi o request dau, tra loi binh thuong tu request sau.

    Mo phong dung hanh vi cua uvicorn khi ket noi keep-alive qua han: dong
    ma KHONG tra ve byte nao.
    """

    so_lan = 0

    def do_GET(self):
        type(self).so_lan += 1
        if type(self).so_lan == 1:
            self.close_connection = True
            return
        than = _json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(than)))
        self.end_headers()
        self.wfile.write(than)

    def log_message(self, *_):
        pass        # khong in log ra man hinh test


def _may_chu_thu():
    may = HTTPServer(("127.0.0.1", 0), _MayChuRotKetNoiLanDau)
    threading.Thread(target=may.serve_forever, daemon=True).start()
    return may


def test_phien_tu_thu_lai_khi_ket_noi_keep_alive_bi_rot():
    from giao_tiep import tao_phien
    _MayChuRotKetNoiLanDau.so_lan = 0
    may = _may_chu_thu()
    try:
        phien = tao_phien("khoa-test-du-dai-32-ky-tu-abcdef")
        phan_hoi = phien.get(f"http://127.0.0.1:{may.server_port}/", timeout=3)
        assert phan_hoi.status_code == 200
        assert _MayChuRotKetNoiLanDau.so_lan == 2   # lan 1 rot, lan 2 thanh cong
    finally:
        may.shutdown()
        may.server_close()


def test_phien_thuong_KHONG_chiu_duoc_loi_nay():
    """Chung minh bo khung test tren that su tai hien duoc loi.

    Neu test nay cung pass thi test o tren khong chung minh duoc gi - no se
    pass ca khi tao_phien() quen cau hinh thu lai.
    """
    import requests
    _MayChuRotKetNoiLanDau.so_lan = 0
    may = _may_chu_thu()
    try:
        with requests.Session() as phien:
            with pytest.raises(requests.RequestException):
                phien.get(f"http://127.0.0.1:{may.server_port}/", timeout=3)
    finally:
        may.shutdown()
        may.server_close()


def test_phien_gan_san_api_key_vao_header():
    from giao_tiep import tao_phien
    assert tao_phien("khoa-bi-mat").headers["X-API-Key"] == "khoa-bi-mat"


def test_phien_KHONG_tu_thu_lai_POST():
    """POST khong duoc tu thu lai - se tao ban ghi TRUNG trong Database.

    Ket noi rot truoc khi server doc request thi thu lai an toan, nhung rot
    SAU khi server da ghi xong ban ghi thi thu lai se ghi them mot ban nua.
    urllib3 khong phan biet duoc hai truong hop do, nen chi thu lai cac
    phuong thuc doc (GET/HEAD/...). POST hong thi bo qua chu ky, chu ky sau
    gui lai - mat mot mau do con hon co hai ban ghi ma.
    """
    from giao_tiep import tao_phien
    bo_thu_lai = tao_phien("khoa").get_adapter("http://x/").max_retries
    assert "GET" in bo_thu_lai.allowed_methods
    assert "POST" not in bo_thu_lai.allowed_methods
