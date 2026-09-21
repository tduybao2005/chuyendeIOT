"""HTTP API toi gian cho bai IoT buoi 8."""

import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, field_validator, model_validator


def _doc_env() -> dict[str, str]:
    values = {}
    env_file = Path(__file__).with_name(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                values[name.strip()] = value.strip().strip('"').strip("'")
    return values


_ENV = _doc_env()
MONGODB_URI = os.getenv("MONGODB_URI", _ENV.get("MONGODB_URI", ""))
API_KEY = os.getenv("API_KEY", _ENV.get("API_KEY", ""))
DATABASE = os.getenv("MONGODB_DB", _ENV.get("MONGODB_DB", "iot_buoi8"))
COLLECTION = os.getenv(
    "MONGODB_COLLECTION", _ENV.get("MONGODB_COLLECTION", "du_lieu_cam_bien")
)
HOST = os.getenv("HOST", _ENV.get("HOST", "0.0.0.0"))
PORT = int(os.getenv("PORT", _ENV.get("PORT", "8000")))
VN = timezone(timedelta(hours=7))
URL = "/api/v1/du-lieu"


class DuLieuGui(BaseModel):
    ten_thiet_bi: str = Field(min_length=1, max_length=64)
    nhiet_do: float = Field(ge=-40, le=125)
    do_am: float = Field(ge=0, le=100)
    led1: int = Field(ge=0, le=1)
    led2: int = Field(ge=0, le=1)
    led3: int = Field(ge=0, le=1)

    @field_validator("ten_thiet_bi")
    @classmethod
    def cat_ten(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ten_thiet_bi khong duoc rong")
        return value


class ThamSoDoc(BaseModel):
    n: int = Field(default=10, ge=1, le=1000)
    tu: Optional[datetime] = None
    den: Optional[datetime] = None
    ten_thiet_bi: Optional[str] = None

    @field_validator("tu", "den")
    @classmethod
    def gio_viet_nam(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value and value.tzinfo is None:
            value = value.replace(tzinfo=VN)
        return value

    @model_validator(mode="after")
    def kiem_tra_khoang_thoi_gian(self):
        if self.tu and self.den and self.tu > self.den:
            raise ValueError("tu phai truoc den")
        return self


def _thoi_gian(value: Optional[datetime]) -> Optional[datetime]:
    return value.astimezone(timezone.utc) if value else None


def _bo_loc(tham_so: ThamSoDoc) -> dict:
    bo_loc = {}
    if tham_so.ten_thiet_bi:
        bo_loc["ten_thiet_bi"] = tham_so.ten_thiet_bi.strip()
    khoang = {}
    if tham_so.tu:
        khoang["$gte"] = _thoi_gian(tham_so.tu)
    if tham_so.den:
        khoang["$lte"] = _thoi_gian(tham_so.den)
    if khoang:
        bo_loc["thoi_gian_gui"] = khoang
    return bo_loc


def _tra_ban_ghi(tai_lieu: dict) -> dict:
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


async def _api_key(request: Request) -> None:
    received = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not API_KEY or not received or not secrets.compare_digest(received, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thieu hoac sai API_KEY",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MONGODB_URI or len(API_KEY) < 16:
        raise RuntimeError("Can dien MONGODB_URI va API_KEY trong server/.env")
    client = AsyncIOMotorClient(MONGODB_URI, tz_aware=True, tzinfo=timezone.utc)
    app.state.client = client
    app.state.collection = client[DATABASE][COLLECTION]
    await app.state.collection.create_index(
        [("ten_thiet_bi", 1), ("thoi_gian_gui", -1)],
        name="thiet_bi_va_thoi_gian",
    )
    try:
        yield
    finally:
        client.close()


app = FastAPI(title="IoT Buoi 8 API", lifespan=lifespan)


def _collection(request: Request):
    return request.app.state.collection


async def _doc(request: Request, params: ThamSoDoc) -> list[dict]:
    cursor = (
        _collection(request)
        .find(_bo_loc(params))
        .sort("thoi_gian_gui", -1)
        .limit(params.n)
    )
    return [_tra_ban_ghi(document) async for document in cursor]


@app.post(URL, dependencies=[Depends(_api_key)])
async def gui_post(data: DuLieuGui, request: Request):
    document = data.model_dump()
    document["thoi_gian_gui"] = datetime.now(timezone.utc)
    result = await _collection(request).insert_one(document)
    document["_id"] = result.inserted_id
    return {"thanh_cong": True, "ban_ghi": _tra_ban_ghi(document)}


@app.get(URL, dependencies=[Depends(_api_key)])
async def doc_get(request: Request, params: ThamSoDoc = Depends()):
    records = await _doc(request, params)
    return {"thanh_cong": True, "so_luong": len(records), "ban_ghi": records}
