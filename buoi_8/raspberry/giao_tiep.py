"""
GIAO TIEP - dong goi du lieu gui len va dinh dang du lieu doc ve.

Cung nhu logic_led.py, file nay KHONG cham GPIO, KHONG cham mang, nen test
duoc tren may tinh khong can Pi.

=========================================================================
DIEM QUAN TRONG CUA BAI: TERMINAL IN DU LIEU DOC VE TU SERVER
=========================================================================
Chuong trinh Pi doc cam bien roi bat den, nhung KHONG in thang bien cuc bo
vua doc duoc ra terminal. No gui len server, roi GOI API DOC de lay du lieu
tu server ve, va in cai lay ve do.

Lam vong nhu vay la co chu dich: no chung minh ca duong di ve deu song -
Pi -> HTTP -> FastAPI -> MongoDB Atlas -> FastAPI -> HTTP -> Pi. In bien
cuc bo thi man hinh van dep y het ke ca khi Atlas dang chet, khong chung
minh duoc gi ca.

Vi vay dinh_dang_ban_ghi() nhan vao dung cai dict server tra ve, va no phai
chiu duoc truong hop server tra thieu truong (in '?') thay vi nem KeyError
lam chet han tien trinh dang chay nhieu gio.
"""

from typing import Any, Optional, Sequence

# Dai gia tri hop le cua cam bien - loai gia tri rac TRUOC khi gui len.
#
# Co y lap lai gia tri nay o ca hai phia (server co DAI_NHIET_DO/DAI_DO_AM
# trong mo_hinh.py) chu khong chia se mot file chung: hai chuong trinh chay
# tren HAI MAY khac nhau, khong co thu muc chung. Pi loc som de khoi ton mot
# luot goi mang cho du lieu chac chan bi tu choi; server van tu loc lai vi
# no khong duoc tin client.
#
# Dai o day HEP HON ben server, va do la co y: ben server phai chap nhan moi
# thiet bi hop ly (ke ca dat ngoai troi), con Pi nay dat trong phong hoc nen
# siet chat hon de bat duoc gia tri vo ly som.
DAI_NHIET_DO = (0.0, 60.0)    # do C
DAI_DO_AM = (10.0, 100.0)     # %


def cam_bien_hop_le(nhiet_do: Optional[float], do_am: Optional[float]) -> bool:
    """Gia tri doc duoc co dang tin khong.

    Loai ba hai kieu rac hay gap nhat:

    1. None - thu vien seeed_dht tra None khi khong bat tay duoc voi cam bien
       (day tuot, nhieu). Chuyen thuong ngay, khong phai su co.

    2. So vo nghia do dat SAI LOAI DHT. Da gap that o buoi 6: cam DHT22 ma
       khai bao DHT11 thi doc ra 1 C va 3 % - khong bao loi gi ca, cam bien
       van "doc duoc", chi la so sai hoan toan. Dai gia tri chan duoc ngay.
    """
    if nhiet_do is None or do_am is None:
        return False
    if not DAI_NHIET_DO[0] <= nhiet_do <= DAI_NHIET_DO[1]:
        return False
    if not DAI_DO_AM[0] <= do_am <= DAI_DO_AM[1]:
        return False
    return True


def dung_goi_tin(ten_thiet_bi: str, nhiet_do: float, do_am: float,
                 led: Sequence[int]) -> dict[str, Any]:
    """Dong goi 5 gia tri de bai yeu cau thanh than request gui len server.

    KHONG co api_key o day: khoa di theo header 'X-API-Key'. De khoa trong
    than goi tin thi no di thang vao cho server ghi ban ghi, di nguoc yeu
    cau "khong luu API vao Database" - chan tu day la chac nhat.

    KHONG co thoi gian: server tu gan. Pi khong co pin RTC, mat dien bat len
    ma chua kip dong bo NTP thi dong ho bao nam 1970.

    Lam tron 1 chu so thap phan: DHT chi chinh xac toi khoang 1 C / 1 %, in
    ra 28.500000000000004 (sai so dau phay dong) vua vo nghia vua kho doc.
    """
    return {
        "ten_thiet_bi": ten_thiet_bi,
        "nhiet_do": round(float(nhiet_do), 1),
        "do_am": round(float(do_am), 1),
        "led1": int(led[0]),
        "led2": int(led[1]),
        "led3": int(led[2]),
    }


def _lay(ban_ghi: dict[str, Any], khoa: str) -> str:
    """Lay mot truong, thieu thi tra '?' chu khong nem loi.

    Chuong trinh chay lien tuc nhieu gio; nem KeyError giua chung thi tien
    trinh chet han va mat het du lieu tu do tro di. In '?' thi chi hong mot
    dong tren man hinh, van thay duoc ngay la co gi do khong on.
    """
    gia_tri = ban_ghi.get(khoa)
    return "?" if gia_tri is None else str(gia_tri)


def _gio_de_doc(chuoi_thoi_gian: Optional[str]) -> str:
    """'2026-09-20T10:00:00+07:00' -> '2026-09-20 10:00:00'.

    Bo chu 'T' va phan mui gio cho de doc tren terminal. Khong dung
    datetime.fromisoformat roi format lai vi chi can cat chuoi - it viec hon
    va khong the sai mui gio (server da tra ve gio VN san).
    """
    if not chuoi_thoi_gian:
        return "?"
    chuoi = str(chuoi_thoi_gian).replace("T", " ")
    for dau in ("+", "Z"):
        vi_tri = chuoi.rfind(dau)
        if vi_tri > 10:          # > 10 de khong cat nham dau '-' cua ngay
            chuoi = chuoi[:vi_tri]
    return chuoi.split(".")[0].strip()   # bo phan mili giay neu co


def dinh_dang_ban_ghi(ban_ghi: dict[str, Any]) -> str:
    """Mot ban ghi doc ve tu server -> mot dong tren terminal."""
    led = "".join(_lay(ban_ghi, f"led{so}") for so in (1, 2, 3))
    return (
        f"[{_gio_de_doc(ban_ghi.get('thoi_gian_gui'))}] "
        f"{_lay(ban_ghi, 'ten_thiet_bi'):<12} "
        f"nhiet do {_lay(ban_ghi, 'nhiet_do'):>5} C | "
        f"do am {_lay(ban_ghi, 'do_am'):>5} % | "
        f"LED(do,vang,xanh) {led} | "
        f"ID {_lay(ban_ghi, 'id')}"
    )


def dinh_dang_danh_sach(danh_sach: Sequence[dict[str, Any]]) -> str:
    """Nhieu ban ghi doc ve -> nhieu dong, moi ban ghi mot dong."""
    if not danh_sach:
        return "    (server chua co ban ghi nao)"
    return "\n".join(f"    {dinh_dang_ban_ghi(b)}" for b in danh_sach)


# =========================================================================
# PHAN LOAI LOI TU SERVER
#
# HAI LOAI LOI NAY DOI XU HOAN TOAN KHAC NHAU - gop chung mot loai la sai:
#
#   LoiCauHinh (401/403/422): sai API_KEY, hoac chuong trinh gui sai dinh
#       dang. Thu lai 100 lan cung van sai y nhu vay. Phai bao NGAY roi dung
#       han. Neu coi day la loi mang thi nguoi dung phai ngoi cho het 15 lan
#       thu (75 giay) moi biet, trong khi ly do that da ro tu lan dau.
#
#   LoiTamThoi (5xx, mat mang, timeout): server dang khoi dong lai, Wi-Fi
#       chop chop. Nhung thu nay tu het - phai THU LAI, khong duoc dung han.
#       Coi day la loi cau hinh thi Pi tat han chi vi mang chop mot cai.
# =========================================================================
class LoiCauHinh(Exception):
    """Sai cau hinh - thu lai vo ich, phai sua roi chay lai."""


class LoiTamThoi(Exception):
    """Su co nhat thoi - thu lai o chu ky sau."""


def _ly_do_tu_server(phan_hoi) -> str:
    """Keo loi giai thich cua server ra.

    requests.raise_for_status() chi in "401 Client Error" - nhin vao khong
    biet phai sua gi. Server da giai thich san trong truong 'detail' (vi du
    "Thieu hoac sai API_KEY"), keo ra day thi doc mot dong la biet.
    """
    try:
        than = phan_hoi.json()
    except Exception:
        return (phan_hoi.text or "")[:300]
    if isinstance(than, dict) and "detail" in than:
        return str(than["detail"])[:300]
    return str(than)[:300]


def kiem_tra_phan_hoi(phan_hoi):
    """Kiem tra phan hoi HTTP, tra ve than json neu thanh cong.

    Loi thi nem LoiCauHinh hoac LoiTamThoi tuy theo ma trang thai - xem
    giai thich su khac biet o tren.
    """
    ma = phan_hoi.status_code
    if ma < 400:
        return phan_hoi.json()

    thong_bao = f"HTTP {ma}: {_ly_do_tu_server(phan_hoi)}"
    # 4xx = loi cua BEN GOI (khoa sai, du lieu sai) -> sua roi chay lai.
    # 5xx = loi cua BEN SERVER -> khong phai loi cua ta, cho roi thu lai.
    #
    # Rieng 408 (Request Timeout) va 429 (Too Many Requests) tuy la 4xx
    # nhung tu het theo thoi gian, nen xep vao loai thu lai.
    if 400 <= ma < 500 and ma not in (408, 429):
        raise LoiCauHinh(thong_bao)
    raise LoiTamThoi(thong_bao)
