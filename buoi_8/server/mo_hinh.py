"""
MO HINH DU LIEU - cua ngo duy nhat de du lieu di vao Database.

Moi ban ghi muon xuong MongoDB deu phai qua DuLieuGui, moi truy van deu phai
qua ThamSoDoc. Validate tap trung o day thay vi rai rac trong tung route:
them mot route moi cung tu dong duoc bao ve, khong phai nho chep lai luat.

BA VIEC TANG NAY LAM, VA VI SAO PHAI LAM

1. Chan du lieu rac truoc khi luu.
   Cam bien DHT doc hut la chuyen thuong ngay (buoi 6 da phai dat DAI_NHIET_DO
   /DAI_DO_AM vi ly do nay). Neu de gia tri rac xuong Database thi do thi va
   trung binh sai vinh vien - xoa tay tung ban ghi trong Atlas rat cuc.

2. Quy mot gia tri LED ve dung 0/1.
   De bai cho gui "json hoac form-urlencoded". form-urlencoded CHI truyen
   duoc CHUOI: checkbox HTML gui "on", curl -d thuong gui "1"/"true", con
   json gui duoc bool that. Neu khong quy chuan thi cung mot cai den se nam
   trong Database duoi 4 hinh dang khac nhau ("on", "true", true, 1) va moi
   truy van loc theo trang thai LED deu sai.

3. Hieu dung mui gio.
   Database luu UTC (chuan, khong phu thuoc may chu dat o dau), nhung nguoi
   go tham so truy van doc dong ho VN. Xem giai thich o MUI_GIO_VN.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

from pydantic import BaseModel, BeforeValidator, Field, field_validator, model_validator

# =========================================================================
# MUI GIO
#
# Database luu UTC. Nhung khi nguoi cham bai go:
#     /api/v1/du-lieu?tu=2026-09-20T10:00:00
# ho dang nghi den 10 GIO SANG THEO DONG HO VIET NAM, khong ai go kem
# "+07:00". Neu server hieu chuoi do la UTC thi no di tim du lieu luc 17h VN
# -> tra ve rong, va loi nay cuc kho nhan ra vi khong he bao loi gi ca, chi
# la "sao khong co du lieu".
#
# Vi vay: thoi gian KHONG ghi mui gio duoc hieu la gio VN (+07:00); thoi gian
# CO ghi mui gio thi ton trong dung cai nguoi dung viet.
# =========================================================================
MUI_GIO_VN = timezone(timedelta(hours=7), "ICT")

# Dai gia tri hop le - lay theo thong so datasheet cua DHT11/DHT22 noi rong
# mot chut, du de chan gia tri rac ma khong loai nham so do that.
DAI_NHIET_DO = (-40.0, 125.0)   # do C
DAI_DO_AM = (0.0, 100.0)        # %

# So ban ghi toi da mot lan doc. Chan de mot request lo tay (?n=1000000)
# khong keo ca collection ve lam nghen server va het quota Atlas.
SO_BAN_GHI_TOI_DA = 1000

_CHUOI_BAT = {"1", "true", "on", "yes", "bat"}
_CHUOI_TAT = {"0", "false", "off", "no", "tat"}


def _ve_0_hoac_1(gia_tri: Any) -> Any:
    """Quy moi cach viet trang thai LED ve dung so nguyen 0 hoac 1.

    Kiem tra bool TRUOC int vi trong Python `True` cung la `int` (isinstance(
    True, int) == True). Dao thu tu thi nhanh int se nuot mat bool - khong sai
    ket qua o day, nhung la cai bay kinh dien nen viet ro thu tu.

    Gia tri khong hieu duoc thi tra nguyen si cho pydantic bao loi, de thong
    bao loi cua pydantic chi dung ten truong (led1/led2/led3) cho nguoi goi.
    """
    if isinstance(gia_tri, bool):
        return int(gia_tri)
    if isinstance(gia_tri, (int, float)) and gia_tri in (0, 1):
        return int(gia_tri)
    if isinstance(gia_tri, str):
        chuoi = gia_tri.strip().lower()
        if chuoi in _CHUOI_BAT:
            return 1
        if chuoi in _CHUOI_TAT:
            return 0
    return gia_tri


# Kieu dung chung cho ca 3 LED: nhan nhieu cach viet o dau vao, luon ra 0/1.
TrangThaiLed = Annotated[
    int,
    BeforeValidator(_ve_0_hoac_1),
    Field(ge=0, le=1, description="0 = tat, 1 = bat"),
]


def gan_mui_gio_vn_neu_thieu(thoi_diem: Optional[datetime]) -> Optional[datetime]:
    """Thoi gian khong ghi mui gio -> hieu la gio VN. Xem MUI_GIO_VN."""
    if thoi_diem is None:
        return None
    if thoi_diem.tzinfo is None:
        return thoi_diem.replace(tzinfo=MUI_GIO_VN)
    return thoi_diem


class DuLieuGui(BaseModel):
    """Mot lan Pi gui du lieu len - phan do CLIENT quyet dinh.

    CO Y KHONG CO TRUONG api_key VA KHONG CO thoi_gian_gui:

    - api_key: de bai ghi ro "khong luu API vao Database". Chan bang mo hinh
      la chac chan nhat - du client co nhet api_key vao body thi pydantic
      cung bo qua (extra='ignore' mac dinh), no khong the di tiep xuong
      Database duoc nua. Chan bang cach "nho xoa trong route" thi chi can
      them mot route la quen.

    - thoi_gian_gui: do SERVER gan (xem kho_du_lieu.py). Dong ho Raspberry Pi
      khong co pin RTC, moi lan mat dien khoi dong lai neu chua kip dong bo
      NTP thi no bao nam 1970. Tin gio cua Pi thi ca do thi vo nghia.
    """

    ten_thiet_bi: str = Field(
        min_length=1, max_length=64,
        description="Ten thiet bi gui len, vi du 'pi4-tdbao'",
    )
    nhiet_do: float = Field(
        ge=DAI_NHIET_DO[0], le=DAI_NHIET_DO[1], description="do C",
    )
    do_am: float = Field(
        ge=DAI_DO_AM[0], le=DAI_DO_AM[1], description="%",
    )
    led1: TrangThaiLed
    led2: TrangThaiLed
    led3: TrangThaiLed

    @field_validator("ten_thiet_bi")
    @classmethod
    def _cat_khoang_trang(cls, ten: str) -> str:
        """Cat khoang trang hai dau roi moi kiem tra rong.

        Khong cat thi "pi4-tdbao" va "pi4-tdbao " thanh hai thiet bi khac nhau
        trong Database, loc theo ten se thieu ban ghi.
        """
        ten = ten.strip()
        if not ten:
            raise ValueError("ten_thiet_bi khong duoc rong")
        return ten


class ThamSoDoc(BaseModel):
    """Tham so cua API doc - dung chung cho ca duong GET lan duong POST.

    De bai muc do 3: "Co the chon doc N du lieu gan nhat, truy xuat du lieu
    trong mot khoang thoi gian tuy chon."
    """

    n: int = Field(
        default=10, ge=1, le=SO_BAN_GHI_TOI_DA,
        description="So ban ghi gan nhat can lay",
    )
    tu: Optional[datetime] = Field(
        default=None, description="Moc dau khoang thoi gian (>= tu)",
    )
    den: Optional[datetime] = Field(
        default=None, description="Moc cuoi khoang thoi gian (<= den)",
    )
    ten_thiet_bi: Optional[str] = Field(
        default=None, description="Chi lay du lieu cua mot thiet bi",
    )

    @field_validator("tu", "den")
    @classmethod
    def _hieu_theo_gio_vn(cls, thoi_diem: Optional[datetime]) -> Optional[datetime]:
        return gan_mui_gio_vn_neu_thieu(thoi_diem)

    @field_validator("ten_thiet_bi")
    @classmethod
    def _cat_khoang_trang(cls, ten: Optional[str]) -> Optional[str]:
        if ten is None:
            return None
        ten = ten.strip()
        return ten or None

    @model_validator(mode="after")
    def _khoang_thoi_gian_phai_thuan(self) -> "ThamSoDoc":
        """Bao loi ngay khi tu > den.

        Khong chan thi MongoDB tra ve rong mot cach hop le, nguoi dung tuong
        la "khong co du lieu" va di kiem tra nham phia cam bien.
        """
        if self.tu and self.den and self.tu > self.den:
            raise ValueError("'tu' phai truoc 'den'")
        return self


class BanGhi(BaseModel):
    """Mot ban ghi doc tu Database tra ve cho client.

    Du 4 thong tin de bai bat buoc: ID, thoi gian gui len, ten thiet bi, va
    cac gia tri do duoc. Khong co api_key - no chua bao gio duoc luu.
    """

    id: str = Field(description="ID ban ghi (_id cua MongoDB, dang chuoi)")
    ten_thiet_bi: str
    nhiet_do: float
    do_am: float
    led1: int
    led2: int
    led3: int
    thoi_gian_gui: datetime = Field(description="Thoi diem server nhan, tra ve gio VN")

    @field_validator("thoi_gian_gui")
    @classmethod
    def _tra_ve_gio_vn(cls, thoi_diem: datetime) -> datetime:
        """Database luu UTC, nhung tra ra ngoai theo gio VN.

        MongoDB tra datetime KHONG co tzinfo (BSON khong luu mui gio, moi thu
        ngam dinh la UTC) nen phai dan nhan UTC vao truoc, roi moi doi sang
        +07:00. Thieu buoc dan nhan thi astimezone() se hieu nham la gio may
        chu va lech 7 tieng.
        """
        if thoi_diem.tzinfo is None:
            thoi_diem = thoi_diem.replace(tzinfo=timezone.utc)
        return thoi_diem.astimezone(MUI_GIO_VN)


class KetQuaGui(BaseModel):
    """Tra loi cho API gui du lieu."""

    thanh_cong: bool = True
    ban_ghi: BanGhi


class KetQuaDoc(BaseModel):
    """Tra loi cho API doc du lieu."""

    thanh_cong: bool = True
    so_luong: int
    ban_ghi: list[BanGhi]
