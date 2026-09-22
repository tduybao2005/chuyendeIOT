"""
Buoi 8 - Bai tap muc do 3 (10 diem): HTTP Server co Database.

De bai:
    - API de gui du lieu nhiet do, do am, gia tri trang thai cua 3 LED len
      Server. Du lieu co the theo dinh dang json hoac form-urlencoded.
    - API doc du lieu nhiet do, do am, gia tri trang thai cua 3 LED tu
      Server. Co the chon doc N du lieu gan nhat, truy xuat du lieu trong
      mot khoang thoi gian tuy chon.
    - Co ho tro ca 2 giao thuc POST/GET cho API gui va doc du lieu:
      POST de GUI, GET de DOC.
    - Du lieu gui len duoc luu vao Database phai co ID, thoi gian gui len,
      ten thiet bi gui len va co ho tro bao mat dang API_KEY (khong luu
      API vao Database).

Hai route duy nhat:
    POST /du-lieu    gui du lieu (nhan ca JSON va form-urlencoded)
    GET  /du-lieu     doc du lieu (?n=..&tu=..&den=..)

Ca hai deu doi API_KEY qua header "X-API-Key" hoac query "?api_key=..".

Cau hinh doc tu file .env cung thu muc (xem .env.example) hoac bien moi
truong cung ten. Chay:

    python3 server.py
"""

import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

# ---------------------------------------------------------------------------
# Cau hinh - doc file .env cung thu muc, bien moi truong (neu co) duoc uu
# tien hon.
# ---------------------------------------------------------------------------


def _doc_file_env() -> dict[str, str]:
    gia_tri: dict[str, str] = {}
    file_env = Path(__file__).with_name(".env")
    if file_env.exists():
        for dong in file_env.read_text(encoding="utf-8").splitlines():
            dong = dong.strip()
            if dong and not dong.startswith("#") and "=" in dong:
                ten, gt = dong.split("=", 1)
                gia_tri[ten.strip()] = gt.strip().strip('"').strip("'")
    return gia_tri


_ENV = _doc_file_env()


def _cau_hinh(ten: str, mac_dinh: str = "") -> str:
    return os.environ.get(ten, _ENV.get(ten, mac_dinh))


MONGODB_URI = _cau_hinh("MONGODB_URI")
API_KEY = _cau_hinh("API_KEY")
MONGODB_DB = _cau_hinh("MONGODB_DB", "iot_buoi8")
MONGODB_COLLECTION = _cau_hinh("MONGODB_COLLECTION", "du_lieu_cam_bien")
HOST = _cau_hinh("HOST", "0.0.0.0")
PORT = int(_cau_hinh("PORT", "8000"))

VN = timezone(timedelta(hours=7))  # DB luu UTC, API nhan/tra ve gio Viet Nam


# ---------------------------------------------------------------------------
# Du lieu vao / ra
# ---------------------------------------------------------------------------
class DuLieuGui(BaseModel):
    """Du lieu Pi gui len. KHONG co truong api_key: khoa chi di theo header
    hoac query, nen khong co duong nao xuong toi Database."""

    ten_thiet_bi: str = Field(min_length=1, max_length=64)
    nhiet_do: float = Field(ge=-40, le=125)
    do_am: float = Field(ge=0, le=100)
    led1: int = Field(ge=0, le=1)
    led2: int = Field(ge=0, le=1)
    led3: int = Field(ge=0, le=1)


class ThamSoDoc(BaseModel):
    n: int = Field(default=10, ge=1, le=1000)
    tu: Optional[datetime] = None
    den: Optional[datetime] = None

    @field_validator("tu", "den")
    @classmethod
    def gan_gio_vn(cls, gia_tri: Optional[datetime]) -> Optional[datetime]:
        if gia_tri and gia_tri.tzinfo is None:
            gia_tri = gia_tri.replace(tzinfo=VN)
        return gia_tri

    @model_validator(mode="after")
    def kiem_tra_khoang(self) -> "ThamSoDoc":
        if self.tu and self.den and self.tu > self.den:
            raise ValueError("tu phai truoc den")
        return self


# ---------------------------------------------------------------------------
# Bao mat - API_KEY qua header X-API-Key hoac query ?api_key=
# ---------------------------------------------------------------------------
async def kiem_tra_api_key(request: Request) -> None:
    khoa = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not API_KEY or not khoa or not secrets.compare_digest(khoa, API_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Thieu hoac sai API_KEY")


# ---------------------------------------------------------------------------
# Database (MongoDB Atlas qua motor - driver bat dong bo, hop voi FastAPI)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MONGODB_URI or len(API_KEY) < 16:
        raise RuntimeError(
            "Thieu MONGODB_URI hoac API_KEY (toi thieu 16 ky tu) trong server/.env"
        )
    client = AsyncIOMotorClient(MONGODB_URI, tz_aware=True, tzinfo=timezone.utc)
    app.state.bo_suu_tap = client[MONGODB_DB][MONGODB_COLLECTION]
    yield
    client.close()


app = FastAPI(title="IoT Buoi 8 - Muc do 3", lifespan=lifespan)


def _dinh_dang_ban_ghi(tai_lieu: dict) -> dict:
    thoi_gian = tai_lieu["thoi_gian_gui"]
    if thoi_gian.tzinfo is None:
        thoi_gian = thoi_gian.replace(tzinfo=timezone.utc)
    return {
        "id": str(tai_lieu["_id"]),
        "thoi_gian_gui": thoi_gian.astimezone(VN).isoformat(),
        "ten_thiet_bi": tai_lieu["ten_thiet_bi"],
        "nhiet_do": tai_lieu["nhiet_do"],
        "do_am": tai_lieu["do_am"],
        "led1": tai_lieu["led1"],
        "led2": tai_lieu["led2"],
        "led3": tai_lieu["led3"],
    }


# ---------------------------------------------------------------------------
# API GUI - POST /du-lieu (json hoac form-urlencoded tren cung 1 route)
# ---------------------------------------------------------------------------
@app.post("/du-lieu", dependencies=[Depends(kiem_tra_api_key)])
async def gui_du_lieu(request: Request):
    if "application/json" in request.headers.get("content-type", ""):
        than = await request.json()
    else:
        than = dict(await request.form())

    try:
        du_lieu = DuLieuGui(**than)
    except ValidationError as loi:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(loi))

    tai_lieu = du_lieu.model_dump()
    tai_lieu["thoi_gian_gui"] = datetime.now(timezone.utc)  # server tu gan gio
    ket_qua = await request.app.state.bo_suu_tap.insert_one(tai_lieu)
    tai_lieu["_id"] = ket_qua.inserted_id
    return {"thanh_cong": True, "ban_ghi": _dinh_dang_ban_ghi(tai_lieu)}


# ---------------------------------------------------------------------------
# API DOC - GET /du-lieu?n=..&tu=..&den=..
# ---------------------------------------------------------------------------
@app.get("/du-lieu", dependencies=[Depends(kiem_tra_api_key)])
async def doc_du_lieu(request: Request, tham_so: ThamSoDoc = Depends()):
    khoang: dict = {}
    if tham_so.tu:
        khoang["$gte"] = tham_so.tu.astimezone(timezone.utc)
    if tham_so.den:
        khoang["$lte"] = tham_so.den.astimezone(timezone.utc)
    bo_loc = {"thoi_gian_gui": khoang} if khoang else {}

    con_tro = (
        request.app.state.bo_suu_tap.find(bo_loc)
        .sort("thoi_gian_gui", -1)
        .limit(tham_so.n)
    )
    ban_ghi = [_dinh_dang_ban_ghi(tai_lieu) async for tai_lieu in con_tro]
    return {"thanh_cong": True, "so_luong": len(ban_ghi), "ban_ghi": ban_ghi}


if __name__ == "__main__":
    print(f"Server: http://{HOST}:{PORT}  (tai lieu API tu sinh: /docs)")
    uvicorn.run(app, host=HOST, port=PORT)
