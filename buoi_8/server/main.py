"""
HTTP SERVER - Buoi 8 muc do 3 (10 diem). FastAPI + MongoDB Atlas.

=========================================================================
DOI CHIEU DE BAI - MOI GACH DAU DONG NAM O DAU
=========================================================================

  "API de gui du lieu nhiet do, do am, gia tri trang thai cua 3 LED len
   Server. Du lieu co the theo dinh dang json hoac form-urlencoded."
        -> POST /api/v1/du-lieu       (nhan ca hai dinh dang, xem dau_vao.py)

  "API doc du lieu ... Co the chon doc N du lieu gan nhat, truy xuat du lieu
   trong mot khoang thoi gian tuy chon."
        -> GET  /api/v1/du-lieu?n=...&tu=...&den=...
        -> GET  /api/v1/du-lieu/moi-nhat

  "Co ho tro ca 2 giao thuc POST/GET cho API gui va doc du lieu."
        -> GUI: POST /api/v1/du-lieu      va  GET  /api/v1/du-lieu/gui
        -> DOC: GET  /api/v1/du-lieu      va  POST /api/v1/du-lieu/doc

  "Du lieu ... phai co thong tin ID, thoi gian gui len, ten thiet bi gui len"
        -> mo_hinh.BanGhi + kho_du_lieu.chuan_bi_ban_ghi()

  "co ho tro bao mat dang API_KEY (khong luu API vao Database)"
        -> bao_mat.kiem_tra_api_key gan vao TAT CA route du lieu; con ve
           "khong luu" thi DuLieuGui khong he co truong api_key nen khoa
           khong co duong nao di xuong Database.

=========================================================================
CACH CHAY
=========================================================================
    cd buoi_8/server
    cp .env.example .env        # roi dien MONGODB_URI va API_KEY
    ../.venv/bin/python chay_server.py

Tai lieu API tu sinh (bam thu duoc tung endpoint): http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

from bao_mat import kiem_tra_api_key
from dau_vao import doc_than_request, validate_hoac_422
from kho_du_lieu import KhoDuLieu, mo_ket_noi
from mo_hinh import BanGhi, DuLieuGui, KetQuaDoc, KetQuaGui, ThamSoDoc

DUONG_DAN_GOC = "/api/v1/du-lieu"


# =========================================================================
# CAC ROUTE
#
# Tat ca deu nhan `kho` tu request.app.state chu khong dung bien toan cuc.
# Nho vay test bom duoc kho gia (tests/kho_gia.py) va chay offline, con
# server that thi bom KhoMongo vao dung cho do.
# =========================================================================
def _lay_kho(request: Request) -> KhoDuLieu:
    kho = getattr(request.app.state, "kho", None)
    if kho is None:
        # Chi xay ra khi mat ket noi Atlas luc khoi dong. Tra 503 (dich vu
        # tam thoi khong san sang) chu khong phai 500: loi o phia ha tang,
        # khong phai request cua nguoi goi sai.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server chua ket noi duoc Database. Kiem tra MONGODB_URI "
                   "va muc Network Access tren MongoDB Atlas.",
        )
    return kho


def tao_ung_dung(kho: Optional[KhoDuLieu] = None,
                 api_key: Optional[str] = None) -> FastAPI:
    """Tao ung dung FastAPI.

    Nhan `kho` va `api_key` tu ngoai vao (dependency injection) thay vi tu
    doc cau hinh ben trong. Hai ly do:

      1. Test chay duoc offline: bom tests/kho_gia.KhoBoNho vao, khong can
         MongoDB Atlas, khong can mang, khong lam ban database that.
      2. Doc cau hinh luc import module se lam `import main` that bai neu
         chua co file .env - luc do khong chay noi ca bo test.

    Goi khong tham so (tao_ung_dung()) thi ung dung tu ket noi Atlas theo
    .env luc khoi dong - day la duong ma chay_server.py dung.
    """
    @asynccontextmanager
    async def vong_doi(ung_dung: FastAPI):
        """Mo ket noi luc khoi dong, dong lai luc tat.

        Mo mot lan roi dung lai suot doi tien trinh. Moi request mo mot ket
        noi moi thi bat tay TLS toi Atlas (~100-300ms moi lan) se lam nhip
        gui cua Pi cham han, va Atlas goi free M0 chi cho 500 ket noi.
        """
        client = None
        if getattr(ung_dung.state, "kho", None) is None:
            from cau_hinh import doc_cau_hinh

            cau_hinh = doc_cau_hinh()
            ung_dung.state.api_key = cau_hinh.api_key
            client, kho_mongo = mo_ket_noi(
                cau_hinh.mongodb_uri,
                cau_hinh.mongodb_db,
                cau_hinh.mongodb_collection,
            )
            await kho_mongo.tao_index()
            ung_dung.state.kho = kho_mongo
        try:
            yield
        finally:
            if client is not None:
                client.close()

    ung_dung = FastAPI(
        title="IoT Buoi 8 - HTTP Server (muc do 3)",
        description=(
            "Server nhan nhiet do, do am va trang thai 3 LED tu Raspberry Pi, "
            "luu vao MongoDB Atlas. Moi API du lieu deu can API_KEY: gui qua "
            "header 'X-API-Key' hoac tham so '?api_key=...'."
        ),
        version="1.0.0",
        lifespan=vong_doi,
    )

    # Gan san kho/khoa neu duoc bom tu ngoai (duong cua test).
    ung_dung.state.kho = kho
    ung_dung.state.api_key = api_key

    # CORS: de sau nay co lam trang web tinh doc du lieu thi trinh duyet
    # khong chan. Bai tap chay trong LAN nen mo rong; neu dua len Internet
    # that thi phai thu hep allow_origins ve dung ten mien cua minh.
    ung_dung.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    _dang_ky_route(ung_dung)
    return ung_dung


def _dang_ky_route(ung_dung: FastAPI) -> None:
    can_khoa = [Depends(kiem_tra_api_key)]

    # ---------------------------------------------------------------------
    # Trang thong tin - KHONG can khoa
    #
    # Co tinh de mo: de biet "server song hay chet" thi khong nen phai co
    # khoa. Trang nay tuyet doi khong duoc in ra API_KEY hay connection
    # string (co test rieng kiem tra dieu do).
    # ---------------------------------------------------------------------
    @ung_dung.get("/", tags=["thong tin"], summary="Thong tin API")
    async def trang_chu():
        return {
            "ten": "IoT Buoi 8 - HTTP Server (muc do 3)",
            "tai_lieu": "/docs",
            "bao_mat": "Gui API_KEY qua header 'X-API-Key' hoac '?api_key=...'",
            "endpoint": {
                "gui_post": f"POST {DUONG_DAN_GOC}",
                "gui_get": f"GET {DUONG_DAN_GOC}/gui?nhiet_do=..&do_am=..&led1=..",
                "doc_get": f"GET {DUONG_DAN_GOC}?n=10&tu=..&den=..&ten_thiet_bi=..",
                "doc_post": f"POST {DUONG_DAN_GOC}/doc",
                "doc_moi_nhat": f"GET {DUONG_DAN_GOC}/moi-nhat",
            },
        }

    # =====================================================================
    # API GUI DU LIEU  -  ho tro ca POST lan GET
    # =====================================================================
    @ung_dung.post(
        DUONG_DAN_GOC,
        response_model=KetQuaGui,
        status_code=status.HTTP_201_CREATED,
        dependencies=can_khoa,
        tags=["gui du lieu"],
        summary="Gui du lieu (POST, json hoac form-urlencoded)",
    )
    async def gui_bang_post(request: Request):
        """Nhan CA hai dinh dang tren cung mot duong dan - xem dau_vao.py."""
        du_lieu = validate_hoac_422(DuLieuGui, await doc_than_request(request))
        return KetQuaGui(ban_ghi=await _lay_kho(request).them(du_lieu))

    @ung_dung.get(
        f"{DUONG_DAN_GOC}/gui",
        response_model=KetQuaGui,
        status_code=status.HTTP_201_CREATED,
        dependencies=can_khoa,
        tags=["gui du lieu"],
        summary="Gui du lieu (GET, tham so tren query string)",
    )
    async def gui_bang_get(
        request: Request,
        ten_thiet_bi: str = Query(description="Ten thiet bi, vi du 'pi4-tdbao'"),
        nhiet_do: float = Query(description="Nhiet do (do C)"),
        do_am: float = Query(description="Do am (%)"),
        led1: str = Query(description="Trang thai LED 1: 0/1"),
        led2: str = Query(description="Trang thai LED 2: 0/1"),
        led3: str = Query(description="Trang thai LED 3: 0/1"),
    ):
        """De bai bat "ho tro ca 2 giao thuc POST/GET cho API gui".

        LUU Y VE CHUAN HTTP: theo dung chuan thi GET la thao tac chi doc,
        khong duoc thay doi du lieu tren server - ghi du lieu bang GET la
        sai chuan (trinh duyet co the tu goi lai khi nguoi dung bam F5, va
        cac may chu trung gian duoc phep cache lai ket qua). O day van lam
        vi de bai yeu cau ro, va no tien that khi demo: dan mot duong link
        vao trinh duyet la gui duoc du lieu, khong can curl hay Postman.
        Chuong trinh Pi thi luon dung POST.
        """
        du_lieu = validate_hoac_422(DuLieuGui, {
            "ten_thiet_bi": ten_thiet_bi, "nhiet_do": nhiet_do, "do_am": do_am,
            "led1": led1, "led2": led2, "led3": led3,
        })
        return KetQuaGui(ban_ghi=await _lay_kho(request).them(du_lieu))

    # =====================================================================
    # API DOC DU LIEU  -  ho tro ca GET lan POST
    # =====================================================================
    @ung_dung.get(
        DUONG_DAN_GOC,
        response_model=KetQuaDoc,
        dependencies=can_khoa,
        tags=["doc du lieu"],
        summary="Doc N ban ghi gan nhat (GET)",
    )
    async def doc_bang_get(
        request: Request,
        n: int = Query(default=10, description="So ban ghi gan nhat"),
        tu: Optional[str] = Query(
            default=None,
            description="Moc dau, vi du 2026-09-20T10:00:00 (gio Viet Nam)",
        ),
        den: Optional[str] = Query(
            default=None,
            description="Moc cuoi, vi du 2026-09-20T11:00:00 (gio Viet Nam)",
        ),
        ten_thiet_bi: Optional[str] = Query(
            default=None, description="Chi lay du lieu cua mot thiet bi",
        ),
    ):
        tham_so = validate_hoac_422(ThamSoDoc, {
            "n": n, "tu": tu, "den": den, "ten_thiet_bi": ten_thiet_bi,
        })
        return await _doc(request, tham_so)

    @ung_dung.post(
        f"{DUONG_DAN_GOC}/doc",
        response_model=KetQuaDoc,
        dependencies=can_khoa,
        tags=["doc du lieu"],
        summary="Doc N ban ghi gan nhat (POST, json hoac form-urlencoded)",
    )
    async def doc_bang_post(request: Request):
        tham_so = validate_hoac_422(ThamSoDoc, await doc_than_request(request))
        return await _doc(request, tham_so)

    @ung_dung.get(
        f"{DUONG_DAN_GOC}/moi-nhat",
        response_model=KetQuaGui,
        dependencies=can_khoa,
        tags=["doc du lieu"],
        summary="Doc ban ghi cuoi cung",
    )
    async def doc_moi_nhat(
        request: Request,
        ten_thiet_bi: Optional[str] = Query(default=None),
    ):
        """Duong tat cho viec hay dung nhat: 'gia tri cuoi cung la bao nhieu'.

        Tuong duong GET /api/v1/du-lieu?n=1 nhung tra ve THANG mot ban ghi
        thay vi mang mot phan tu, nen ben goi khong phai viet [0] va khong
        phai xu ly truong hop mang rong.
        """
        tham_so = ThamSoDoc(n=1, ten_thiet_bi=ten_thiet_bi)
        ban_ghi = await _lay_kho(request).doc(tham_so)
        if not ban_ghi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chua co ban ghi nao trong Database"
                       + (f" cho thiet bi '{ten_thiet_bi}'" if ten_thiet_bi else ""),
            )
        return KetQuaGui(ban_ghi=ban_ghi[0])

    async def _doc(request: Request, tham_so: ThamSoDoc) -> KetQuaDoc:
        """Than chung cua ca hai duong doc (GET va POST).

        Viet mot lan o day de hai duong khong the tra ve ket qua khac nhau -
        co test rieng khang dinh dieu do (test_get_va_post_cho_ket_qua_doc
        _giong_nhau).
        """
        ban_ghi: list[BanGhi] = await _lay_kho(request).doc(tham_so)
        return KetQuaDoc(so_luong=len(ban_ghi), ban_ghi=ban_ghi)


# Bien `app` cho uvicorn goi theo kieu quen thuoc: `uvicorn main:app`.
# Ket noi Atlas dien ra trong lifespan (luc khoi dong server), KHONG phai luc
# import module - nho vay `import main` trong test khong doi hoi file .env.
app = tao_ung_dung()
