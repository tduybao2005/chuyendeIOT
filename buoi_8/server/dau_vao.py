"""
DOC THAN REQUEST - nhan ca json LAN form-urlencoded tren CUNG MOT route.

De bai muc do 3: "Du lieu co the theo dinh dang json hoac form-urlencoded".

FastAPI khong lam san viec nay. Cach thong thuong la khai bao tham so kieu
Pydantic (chi nhan json) HOAC kieu Form(...) (chi nhan form) - khong co cach
nao khai bao "nhan ca hai" tren cung mot route. Neu lam hai route rieng thi
lai vo yeu cau "MOT API nhan ca hai dinh dang", va tach ra hai duong code se
lech nhau luc sua.

Nen o day doc than request o dang tho roi tu chon cach phan tich theo
Content-Type. Ca hai dinh dang deu quy ve mot dict, sau do CUNG MOT mo hinh
Pydantic validate - mot duong code duy nhat, khong the lech nhau.
"""

import json
from typing import Any

from fastapi import HTTPException, Request
from pydantic import BaseModel, ValidationError

# Ma loi "du lieu gui len khong hop le".
#
# Viet thang so 422 chu khong dung hang so cua Starlette: ten hang so vua bi
# doi (HTTP_422_UNPROCESSABLE_ENTITY -> HTTP_422_UNPROCESSABLE_CONTENT) nen
# dung ten nao cung se bao deprecation warning tren mot trong hai phien ban.
# Con con so 422 thi nam trong chuan HTTP, khong bao gio doi.
MA_DU_LIEU_SAI = 422

KIEU_JSON = "application/json"
KIEU_FORM = "application/x-www-form-urlencoded"
KIEU_MULTIPART = "multipart/form-data"


async def doc_than_request(request: Request) -> dict[str, Any]:
    """Doc than request thanh dict, tu nhan biet json hay form-urlencoded.

    Than RONG tra ve {} chu khong bao loi: API doc du lieu co tat ca tham so
    deu tuy chon, nen `curl -X POST .../doc` tay khong la cach goi hop le va
    phai chay duoc.

    Khong co Content-Type thi doan: thu json truoc, hong thi thu form. Mot so
    client (curl -d khong kem -H) khong gui Content-Type dung.
    """
    kieu = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    than = await request.body()

    if not than:
        return {}

    if kieu == KIEU_JSON:
        return _phan_tich_json(than)

    if kieu in (KIEU_FORM, KIEU_MULTIPART):
        return dict(await request.form())

    # Khong ro Content-Type: thu json, that bai thi quay ve form.
    try:
        return _phan_tich_json(than)
    except HTTPException:
        return dict(await request.form())


def _phan_tich_json(than: bytes) -> dict[str, Any]:
    try:
        du_lieu = json.loads(than)
    except (json.JSONDecodeError, UnicodeDecodeError) as loi:
        raise HTTPException(
            status_code=MA_DU_LIEU_SAI,
            detail=f"Than request khong phai JSON hop le: {loi}",
        ) from loi

    if not isinstance(du_lieu, dict):
        raise HTTPException(
            status_code=MA_DU_LIEU_SAI,
            detail="Than request phai la mot doi tuong JSON, vi du "
                   '{"ten_thiet_bi": "pi4-tdbao", "nhiet_do": 28.5, ...}',
        )
    return du_lieu


def validate_hoac_422(mo_hinh: type[BaseModel], du_lieu: dict[str, Any]) -> BaseModel:
    """Validate bang mo hinh Pydantic, loi thi tra ve 422 kem chi tiet.

    Phai bat tay vi day la du lieu doc thu cong tu than request - FastAPI
    khong biet den no nen khong tu sinh loi 422 giup nhu voi tham so khai
    bao san. Giu nguyen dinh dang loi cua Pydantic (errors()) de thong bao
    giong het cac route khac, khong lech mot kieu rieng.
    """
    try:
        return mo_hinh.model_validate(du_lieu)
    except ValidationError as loi:
        raise HTTPException(
            status_code=MA_DU_LIEU_SAI,
            detail=json.loads(loi.json()),
        ) from loi
