"""
BAO MAT - kiem tra API_KEY.

De bai muc do 3: "co ho tro bao mat dang API_KEY (khong luu API vao
Database)". Cau do co HAI ve, hai ve nam o hai cho:

  - "bao mat dang API_KEY"   -> file nay: khong co khoa dung thi khong vao.
  - "khong luu API vao DB"   -> mo_hinh.py + kho_du_lieu.py: DuLieuGui khong
                                he co truong api_key, nen khong co duong nao
                                de khoa di xuong Database.

Khoa di theo request, KHONG di theo ban ghi. No dung lai o day, khong bao gio
duoc chuyen tiep xuong tang kho du lieu.
"""

import secrets
from typing import Optional

from fastapi import HTTPException, Request, status

TEN_HEADER = "X-API-Key"
TEN_THAM_SO_QUERY = "api_key"


def khoa_hop_le(khoa_nhan_duoc: Optional[str], khoa_that: Optional[str]) -> bool:
    """So sanh khoa client gui len voi khoa that cua server.

    HAI DIEU QUAN TRONG:

    1. FAIL CLOSED. Server chua dat khoa (khoa_that rong/None) thi chan het,
       khong phai cho qua het. Neu lam nguoc lai thi mot lan quen dien
       API_KEY trong .env se bien server thanh cong khai ma khong co dau
       hieu gi bao - dang loi nguy hiem nhat vi no im lang.

    2. DUNG secrets.compare_digest, KHONG dung ==.
       Toan tu == dung ngay khi gap ky tu dau tien khac nhau, nen khoa doan
       dung 5 ky tu dau se mat nhieu thoi gian hon khoa sai ngay ky tu dau.
       Do chenh lech do cho phep do thoi gian phan hoi de mo dan tung ky tu
       (timing attack). compare_digest luon chay het chuoi nen thoi gian nhu
       nhau. Voi bai tap tren LAN thi kho khai thac that, nhung day la cach
       viet dung va khong ton them dong nao.
    """
    if not khoa_that or not khoa_nhan_duoc:
        return False
    return secrets.compare_digest(khoa_nhan_duoc, khoa_that)


def lay_khoa_tu_request(header: Optional[str], query: Optional[str]) -> Optional[str]:
    """Lay khoa tu header truoc, khong co thi lay tu query string.

    VI SAO CHAP NHAN CA QUERY STRING: de bai bat "ho tro ca 2 giao thuc
    POST/GET". Muon bam thu mot API GET tren thanh dia chi trinh duyet thi
    khong co cach nao dat header, nen phai cho phep ?api_key=...

    DANH DOI: query string bi ghi vao lich su trinh duyet va log cua may chu
    trung gian, con header thi khong. Vi vay header duoc uu tien, va chuong
    trinh Pi (raspberry/chuong_trinh_pi.py) luon dung header - query string
    chi de demo bang tay.
    """
    return header or query


async def kiem_tra_api_key(request: Request) -> None:
    """Dependency cua FastAPI - gan vao route nao thi route do duoc bao ve.

    Doc khoa that tu request.app.state chu khong doc tu bien toan cuc: nho
    vay test thay duoc cau hinh khac ma khong phai vá bien toan cuc.

    Tra ve 401 kem header WWW-Authenticate dung chuan HTTP cho truong hop
    thieu/sai khoa.
    """
    khoa_that = getattr(request.app.state, "api_key", None)
    khoa_nhan_duoc = lay_khoa_tu_request(
        request.headers.get(TEN_HEADER),
        request.query_params.get(TEN_THAM_SO_QUERY),
    )
    if khoa_hop_le(khoa_nhan_duoc, khoa_that):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            f"Thieu hoac sai API_KEY. Gui khoa qua header '{TEN_HEADER}' "
            f"hoac tham so '?{TEN_THAM_SO_QUERY}=...'."
        ),
        headers={"WWW-Authenticate": f'ApiKey header="{TEN_HEADER}"'},
    )
