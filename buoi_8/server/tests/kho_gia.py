"""
Kho du lieu GIA - chi dung trong test, khong bao gio duoc import vao server.

Cai dat cung giao dien KhoDuLieu nhung luu vao mot danh sach trong bo nho,
nho vay bo test chay duoc ma khong can MongoDB Atlas, khong can mang, va
khong lam ban database that.

GIOI HAN CAN BIET: kho nay mo phong lai luat loc/sap xep cua MongoDB bang
Python, no KHONG chung minh duoc cau lenh gui xuong Mongo la dung. Hai thu
bu vao cho do:
  - tests/test_kho_du_lieu.py kiem tra dung_bo_loc() sinh ra dung cau loc
    Mongo (phan dich tham so -> cau truy van, cho de sai nhat).
  - kiem_tra_atlas.py chay that voi Atlas de kiem tra dau noi cuoi cung.
"""

from datetime import datetime, timezone

from bson import ObjectId

from kho_du_lieu import chuan_bi_ban_ghi, doi_sang_ban_ghi
from mo_hinh import BanGhi, DuLieuGui, ThamSoDoc


class KhoBoNho:
    """Kho du lieu trong bo nho, cung giao dien voi KhoMongo."""

    def __init__(self):
        self.tai_lieu: list[dict] = []
        # Cho phep test tu dat thoi diem "bay gio" de kiem tra loc theo
        # khoang thoi gian ma khong phai cho doi that.
        self.thoi_diem_ke_tiep: datetime | None = None

    # -- cung giao dien voi KhoMongo ---------------------------------------
    async def them(self, du_lieu: DuLieuGui) -> BanGhi:
        thoi_diem = self.thoi_diem_ke_tiep or datetime.now(timezone.utc)
        self.thoi_diem_ke_tiep = None
        tai_lieu = chuan_bi_ban_ghi(du_lieu, thoi_diem)
        tai_lieu["_id"] = ObjectId()
        self.tai_lieu.append(tai_lieu)
        return doi_sang_ban_ghi(tai_lieu)

    async def doc(self, tham_so: ThamSoDoc) -> list[BanGhi]:
        khop = [t for t in self.tai_lieu if self._khop(t, tham_so)]
        khop.sort(key=lambda t: t["thoi_gian_gui"], reverse=True)
        return [doi_sang_ban_ghi(t) for t in khop[: tham_so.n]]

    # -- ho tro cho test ---------------------------------------------------
    @staticmethod
    def _khop(tai_lieu: dict, tham_so: ThamSoDoc) -> bool:
        if tham_so.ten_thiet_bi and tai_lieu["ten_thiet_bi"] != tham_so.ten_thiet_bi:
            return False
        moc = tai_lieu["thoi_gian_gui"]
        if tham_so.tu and moc < tham_so.tu.astimezone(timezone.utc):
            return False
        if tham_so.den and moc > tham_so.den.astimezone(timezone.utc):
            return False
        return True

    def dat_thoi_diem(self, thoi_diem: datetime) -> None:
        """Ban ghi TIEP THEO se duoc luu voi moc thoi gian nay."""
        self.thoi_diem_ke_tiep = thoi_diem
