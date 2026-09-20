"""
TANG KHO DU LIEU - cho duy nhat trong chuong trinh biet MongoDB ton tai.

Cac route trong main.py chi goi hai ham `them()` va `doc()` qua giao dien
KhoDuLieu, khong route nao tu viet cau lenh Mongo. Nho vay:

  - Doi cach luu tru (Atlas -> Mongo chay may, hay sau nay doi han sang
    PostgreSQL) chi sua mot file nay, khong dong den route nao.
  - Test chay offline duoc: tests/kho_gia.py cai dat cung giao dien do bang
    mot danh sach trong bo nho, khong can mang, khong can Atlas.

Ba ham THUAN LOGIC (dung_bo_loc / chuan_bi_ban_ghi / doi_sang_ban_ghi) tach
rieng khoi lop KhoMongo de test duoc ma khong can ket noi that - chung chua
toan bo phan de sai: mui gio va hinh dang cau truy van.
"""

from datetime import datetime, timezone
from typing import Any, Optional, Protocol

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from mo_hinh import BanGhi, DuLieuGui, ThamSoDoc

# Ten index sap xep theo thiet bi + thoi gian giam dan.
#
# VI SAO CAN INDEX NAY: moi truy van cua de bai deu la "N ban ghi GAN NHAT"
# (sort thoi_gian_gui giam dan), co the kem loc theo thiet bi. Khong co index
# thi MongoDB phai doc va sap xep TOAN BO collection moi lan - voi goi free M0
# cua Atlas (512 MB, RAM rat han che) thi chi vai chuc nghin ban ghi la truy
# van bat dau cham thay ro, va Atlas bao loi neu bo sap xep vuot 32 MB RAM.
TEN_INDEX = "thiet_bi_va_thoi_gian"


# =========================================================================
# 1. BA HAM THUAN LOGIC - khong cham mang, test duoc offline
# =========================================================================
def dung_bo_loc(tham_so: ThamSoDoc) -> dict[str, Any]:
    """Dich tham so nguoi dung thanh cau loc cua MongoDB.

    Chi dua vao bo loc nhung dieu kien nguoi dung THUC SU gui len: bo loc
    rong nghia la "lay tat ca". Dat san {"$gte": None} se khong loc dung.

    Moc thoi gian luon doi ve UTC vi Database luu UTC. Quen buoc nay thi cau
    loc lech dung 7 tieng, truy van tra ve rong ma khong bao loi gi - loi im
    lang, rat kho tim.
    """
    bo_loc: dict[str, Any] = {}

    if tham_so.ten_thiet_bi:
        bo_loc["ten_thiet_bi"] = tham_so.ten_thiet_bi

    khoang_thoi_gian: dict[str, datetime] = {}
    if tham_so.tu:
        khoang_thoi_gian["$gte"] = tham_so.tu.astimezone(timezone.utc)
    if tham_so.den:
        khoang_thoi_gian["$lte"] = tham_so.den.astimezone(timezone.utc)
    if khoang_thoi_gian:
        bo_loc["thoi_gian_gui"] = khoang_thoi_gian

    return bo_loc


def chuan_bi_ban_ghi(du_lieu: DuLieuGui, thoi_diem: datetime) -> dict[str, Any]:
    """Tu du lieu client thanh tai lieu san sang luu xuong MongoDB.

    THOI GIAN DO SERVER GAN, KHONG LAY CUA CLIENT: Raspberry Pi khong co pin
    RTC, moi lan mat dien bat len neu chua kip dong bo NTP thi dong ho bao
    nam 1970. Lay gio cua Pi thi thu tu ban ghi loan va do thi vo nghia.

    model_dump() chi tra ve dung cac truong khai bao trong DuLieuGui, ma
    DuLieuGui khong he co truong api_key - nen theo thiet ke thi API_KEY
    KHONG CO DUONG NAO xuong duoc Database (yeu cau cua de bai).
    """
    tai_lieu = du_lieu.model_dump()
    tai_lieu["thoi_gian_gui"] = thoi_diem.astimezone(timezone.utc)
    return tai_lieu


def doi_sang_ban_ghi(tai_lieu: dict[str, Any]) -> BanGhi:
    """Tu tai lieu MongoDB thanh ban ghi tra ve client.

    Doi _id (kieu ObjectId) thanh chuoi vi ObjectId khong serialize thang ra
    JSON duoc. Day chinh la truong "ID" ma de bai yeu cau moi ban ghi phai co
    - dung _id san cua MongoDB thay vi tu sinh them mot ID nua, vua khong
    trung nhau vua khong phai quan ly bo dem.
    """
    return BanGhi(
        id=str(tai_lieu["_id"]),
        ten_thiet_bi=tai_lieu["ten_thiet_bi"],
        nhiet_do=tai_lieu["nhiet_do"],
        do_am=tai_lieu["do_am"],
        led1=tai_lieu["led1"],
        led2=tai_lieu["led2"],
        led3=tai_lieu["led3"],
        thoi_gian_gui=tai_lieu["thoi_gian_gui"],
    )


# =========================================================================
# 2. GIAO DIEN CHUNG - route chi biet den chung nay
# =========================================================================
class KhoDuLieu(Protocol):
    """Hop dong giua route va noi luu tru.

    Chi hai viec. Route khong duoc biet gi hon the: khong biet MongoDB, khong
    biet ten collection, khong biet cau lenh sort. Nho vay tests/kho_gia.py
    thay the duoc bang mot danh sach trong bo nho.
    """

    async def them(self, du_lieu: DuLieuGui) -> BanGhi:
        """Luu mot ban ghi, tra ve ban ghi da luu (kem ID va thoi gian)."""
        ...

    async def doc(self, tham_so: ThamSoDoc) -> list[BanGhi]:
        """Lay tham_so.n ban ghi GAN NHAT khop bo loc, moi nhat dung truoc."""
        ...


# =========================================================================
# 3. CAI DAT THAT - MongoDB Atlas
# =========================================================================
class KhoMongo:
    """Cai dat KhoDuLieu tren MongoDB (Atlas hoac Mongo chay may)."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self._collection = collection

    async def tao_index(self) -> None:
        """Tao index phuc vu truy van 'N ban ghi gan nhat'.

        Goi moi lan khoi dong server. MongoDB coi create_index la thao tac
        'tao neu chua co' nen goi lai nhieu lan khong ton them gi.
        """
        await self._collection.create_index(
            [("ten_thiet_bi", 1), ("thoi_gian_gui", -1)],
            name=TEN_INDEX,
        )

    async def them(self, du_lieu: DuLieuGui) -> BanGhi:
        tai_lieu = chuan_bi_ban_ghi(du_lieu, datetime.now(timezone.utc))
        ket_qua = await self._collection.insert_one(tai_lieu)
        # insert_one() gan _id nguoc vao chinh dict `tai_lieu`, nhung lay tu
        # ket_qua.inserted_id thi ro rang hon va khong phu thuoc hanh vi do.
        tai_lieu["_id"] = ket_qua.inserted_id
        return doi_sang_ban_ghi(tai_lieu)

    async def doc(self, tham_so: ThamSoDoc) -> list[BanGhi]:
        con_tro = (
            self._collection
            .find(dung_bo_loc(tham_so))
            .sort("thoi_gian_gui", -1)   # moi nhat truoc
            .limit(tham_so.n)
        )
        return [doi_sang_ban_ghi(tai_lieu) async for tai_lieu in con_tro]


def mo_ket_noi(uri: str, ten_database: str, ten_collection: str):
    """Mo ket noi toi MongoDB, tra ve (client, KhoMongo).

    Tra ve ca client de main.py con dong lai luc tat server. Khong dong thi
    tien trinh co the treo khong thoat han khi nhan Ctrl+C.

    tz_aware=True: bat buoc. Mac dinh motor tra datetime KHONG co tzinfo, luc
    do so sanh voi datetime co tzinfo se nem TypeError, va astimezone() se
    hieu nham la gio may chu -> lech 7 tieng.
    """
    client = AsyncIOMotorClient(uri, tz_aware=True, tzinfo=timezone.utc)
    collection = client[ten_database][ten_collection]
    return client, KhoMongo(collection)
