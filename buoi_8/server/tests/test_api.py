"""
Test API - doi chieu truc tiep voi tung gach dau dong cua de bai muc do 3.

    o API de gui du lieu nhiet do, do am, gia tri trang thai cua 3 LED len
      Server. Du lieu co the theo dinh dang json hoac form-urlencoded.
    o API doc du lieu nhiet do, do am, gia tri trang thai cua 3 LED tu
      Server. Co the chon doc N du lieu gan nhat, truy xuat du lieu trong
      mot khoang thoi gian tuy chon.
    o Co ho tro ca 2 giao thuc POST/GET cho API gui va doc du lieu.
    o Du lieu gui len duoc luu vao Database phai co thong tin ID, thoi gian
      gui len, ten thiet bi gui len va co ho tro bao mat dang API_KEY
      (khong luu API vao Database).
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from kho_gia import KhoBoNho
from main import tao_ung_dung

KHOA = "khoa-test-du-dai-32-ky-tu-abcdef"
DAU_KHOA = {"X-API-Key": KHOA}

DU_LIEU_MAU = {
    "ten_thiet_bi": "pi4-tdbao",
    "nhiet_do": 28.5,
    "do_am": 70.0,
    "led1": 0,
    "led2": 1,
    "led3": 0,
}


@pytest.fixture
def kho():
    return KhoBoNho()


@pytest.fixture
async def client(kho):
    ung_dung = tao_ung_dung(kho=kho, api_key=KHOA)
    async with AsyncClient(
        transport=ASGITransport(app=ung_dung), base_url="http://test"
    ) as phien:
        yield phien


async def _gui(client, **ghi_de):
    du_lieu = {**DU_LIEU_MAU, **ghi_de}
    return await client.post("/api/v1/du-lieu", json=du_lieu, headers=DAU_KHOA)


# =========================================================================
# GACH DAU DONG 1 - API GUI, nhan CA json LAN form-urlencoded
# =========================================================================
async def test_gui_bang_json(client):
    phan_hoi = await client.post("/api/v1/du-lieu", json=DU_LIEU_MAU, headers=DAU_KHOA)
    assert phan_hoi.status_code == 201
    ban_ghi = phan_hoi.json()["ban_ghi"]
    assert ban_ghi["nhiet_do"] == 28.5
    assert ban_ghi["do_am"] == 70.0
    assert (ban_ghi["led1"], ban_ghi["led2"], ban_ghi["led3"]) == (0, 1, 0)


async def test_gui_bang_form_urlencoded(client):
    """form-urlencoded chi truyen duoc CHUOI - ket qua phai y het json."""
    phan_hoi = await client.post(
        "/api/v1/du-lieu",
        data={k: str(v) for k, v in DU_LIEU_MAU.items()},
        headers=DAU_KHOA,
    )
    assert phan_hoi.status_code == 201
    ban_ghi = phan_hoi.json()["ban_ghi"]
    assert ban_ghi["nhiet_do"] == 28.5
    assert (ban_ghi["led1"], ban_ghi["led2"], ban_ghi["led3"]) == (0, 1, 0)


async def test_json_va_form_cho_ket_qua_giong_het_nhau(client, kho):
    await client.post("/api/v1/du-lieu", json=DU_LIEU_MAU, headers=DAU_KHOA)
    await client.post(
        "/api/v1/du-lieu",
        data={k: str(v) for k, v in DU_LIEU_MAU.items()},
        headers=DAU_KHOA,
    )
    assert len(kho.tai_lieu) == 2
    bo_qua = {"_id", "thoi_gian_gui"}
    thu_nhat = {k: v for k, v in kho.tai_lieu[0].items() if k not in bo_qua}
    thu_hai = {k: v for k, v in kho.tai_lieu[1].items() if k not in bo_qua}
    assert thu_nhat == thu_hai


async def test_form_gui_led_kieu_checkbox_on_off(client):
    """Checkbox cua HTML gui chuoi 'on'/'off', khong phai 1/0."""
    phan_hoi = await client.post(
        "/api/v1/du-lieu",
        data={"ten_thiet_bi": "pi", "nhiet_do": "25", "do_am": "50",
              "led1": "on", "led2": "off", "led3": "true"},
        headers=DAU_KHOA,
    )
    assert phan_hoi.status_code == 201
    ban_ghi = phan_hoi.json()["ban_ghi"]
    assert (ban_ghi["led1"], ban_ghi["led2"], ban_ghi["led3"]) == (1, 0, 1)


# =========================================================================
# GACH DAU DONG 3 - CA POST LAN GET cho API GUI
# =========================================================================
async def test_gui_bang_giao_thuc_get(client):
    phan_hoi = await client.get(
        "/api/v1/du-lieu/gui",
        params={**DU_LIEU_MAU}, headers=DAU_KHOA,
    )
    assert phan_hoi.status_code == 201
    assert phan_hoi.json()["ban_ghi"]["nhiet_do"] == 28.5


async def test_gui_bang_get_va_bang_post_cho_ban_ghi_nhu_nhau(client, kho):
    await client.post("/api/v1/du-lieu", json=DU_LIEU_MAU, headers=DAU_KHOA)
    await client.get("/api/v1/du-lieu/gui", params=DU_LIEU_MAU, headers=DAU_KHOA)
    bo_qua = {"_id", "thoi_gian_gui"}
    assert ({k: v for k, v in kho.tai_lieu[0].items() if k not in bo_qua}
            == {k: v for k, v in kho.tai_lieu[1].items() if k not in bo_qua})


# =========================================================================
# GACH DAU DONG 4 - ban ghi phai co ID, THOI GIAN GUI, TEN THIET BI
# =========================================================================
async def test_ban_ghi_tra_ve_co_du_id_thoi_gian_ten_thiet_bi(client):
    ban_ghi = (await _gui(client)).json()["ban_ghi"]
    assert ban_ghi["id"]
    assert ban_ghi["thoi_gian_gui"]
    assert ban_ghi["ten_thiet_bi"] == "pi4-tdbao"


async def test_moi_ban_ghi_co_id_khac_nhau(client):
    thu_nhat = (await _gui(client)).json()["ban_ghi"]["id"]
    thu_hai = (await _gui(client)).json()["ban_ghi"]["id"]
    assert thu_nhat != thu_hai


async def test_thoi_gian_gui_do_server_gan_chu_khong_lay_cua_client(client, kho):
    """Pi khong co pin RTC, mat dien bat len co the bao nam 1970.

    Client co co tinh gui thoi gian sai thi server van phai gan gio that.
    """
    truoc = datetime.now(timezone.utc) - timedelta(seconds=5)
    await _gui(client, thoi_gian_gui="1970-01-01T00:00:00Z")
    sau = datetime.now(timezone.utc) + timedelta(seconds=5)
    assert truoc <= kho.tai_lieu[0]["thoi_gian_gui"] <= sau


# =========================================================================
# GACH DAU DONG 4 - BAO MAT API_KEY
# =========================================================================
async def test_khong_gui_khoa_thi_bi_tu_choi_khi_gui_du_lieu(client, kho):
    phan_hoi = await client.post("/api/v1/du-lieu", json=DU_LIEU_MAU)
    assert phan_hoi.status_code == 401
    assert kho.tai_lieu == []          # va khong ghi duoc gi xuong Database


async def test_sai_khoa_thi_bi_tu_choi(client):
    phan_hoi = await client.post(
        "/api/v1/du-lieu", json=DU_LIEU_MAU, headers={"X-API-Key": "khoa-sai-hoan-toan"}
    )
    assert phan_hoi.status_code == 401


async def test_khong_gui_khoa_thi_bi_tu_choi_khi_doc_du_lieu(client):
    assert (await client.get("/api/v1/du-lieu")).status_code == 401
    assert (await client.get("/api/v1/du-lieu/moi-nhat")).status_code == 401
    assert (await client.post("/api/v1/du-lieu/doc", json={})).status_code == 401
    assert (await client.get("/api/v1/du-lieu/gui", params=DU_LIEU_MAU)).status_code == 401


async def test_gui_khoa_qua_query_string_de_test_tren_trinh_duyet(client):
    phan_hoi = await client.get("/api/v1/du-lieu", params={"api_key": KHOA})
    assert phan_hoi.status_code == 200


async def test_khong_bao_gio_luu_api_key_xuong_database(client, kho):
    """De bai: 'khong luu API vao Database'.

    Ke ca khi client co nhet api_key vao than request thi ban ghi trong
    Database van khong duoc co no.
    """
    await client.post(
        "/api/v1/du-lieu",
        json={**DU_LIEU_MAU, "api_key": KHOA, "X-API-Key": KHOA},
        headers=DAU_KHOA,
    )
    tai_lieu = kho.tai_lieu[0]
    assert KHOA not in str(tai_lieu)
    assert not any("api" in khoa.lower() or "key" in khoa.lower() for khoa in tai_lieu)


async def test_ban_ghi_tra_ve_cung_khong_lo_api_key(client):
    than = (await _gui(client)).text
    assert KHOA not in than


# =========================================================================
# GACH DAU DONG 2 - API DOC: N ban ghi gan nhat, loc theo khoang thoi gian
# =========================================================================
async def test_doc_tra_ve_ban_ghi_moi_nhat_truoc(client, kho):
    goc = datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)
    for phut in range(3):
        kho.dat_thoi_diem(goc + timedelta(minutes=phut))
        await _gui(client, nhiet_do=20.0 + phut)

    ban_ghi = (await client.get("/api/v1/du-lieu", headers=DAU_KHOA)).json()["ban_ghi"]
    assert [b["nhiet_do"] for b in ban_ghi] == [22.0, 21.0, 20.0]


async def test_doc_n_ban_ghi_gan_nhat(client, kho):
    goc = datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)
    for phut in range(5):
        kho.dat_thoi_diem(goc + timedelta(minutes=phut))
        await _gui(client, nhiet_do=20.0 + phut)

    phan_hoi = await client.get("/api/v1/du-lieu", params={"n": 2}, headers=DAU_KHOA)
    ket_qua = phan_hoi.json()
    assert ket_qua["so_luong"] == 2
    assert [b["nhiet_do"] for b in ket_qua["ban_ghi"]] == [24.0, 23.0]


async def test_doc_trong_mot_khoang_thoi_gian_tuy_chon(client, kho):
    """Moc thoi gian go vao la GIO VIET NAM (xem MUI_GIO_VN trong mo_hinh)."""
    goc = datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)   # = 10:00 gio VN
    for phut in range(5):
        kho.dat_thoi_diem(goc + timedelta(minutes=phut))
        await _gui(client, nhiet_do=20.0 + phut)

    phan_hoi = await client.get(
        "/api/v1/du-lieu",
        params={"tu": "2026-09-20T10:01:00", "den": "2026-09-20T10:03:00", "n": 100},
        headers=DAU_KHOA,
    )
    assert [b["nhiet_do"] for b in phan_hoi.json()["ban_ghi"]] == [23.0, 22.0, 21.0]


async def test_doc_loc_theo_ten_thiet_bi(client, kho):
    await _gui(client, ten_thiet_bi="pi4-tdbao")
    await _gui(client, ten_thiet_bi="pi4-hnc")

    phan_hoi = await client.get(
        "/api/v1/du-lieu", params={"ten_thiet_bi": "pi4-hnc"}, headers=DAU_KHOA
    )
    ban_ghi = phan_hoi.json()["ban_ghi"]
    assert len(ban_ghi) == 1
    assert ban_ghi[0]["ten_thiet_bi"] == "pi4-hnc"


async def test_doc_khi_chua_co_du_lieu_tra_ve_danh_sach_rong(client):
    phan_hoi = await client.get("/api/v1/du-lieu", headers=DAU_KHOA)
    assert phan_hoi.status_code == 200
    assert phan_hoi.json() == {"thanh_cong": True, "so_luong": 0, "ban_ghi": []}


async def test_bao_loi_khi_khoang_thoi_gian_nguoc(client):
    phan_hoi = await client.get(
        "/api/v1/du-lieu",
        params={"tu": "2026-09-20T11:00:00", "den": "2026-09-20T10:00:00"},
        headers=DAU_KHOA,
    )
    assert phan_hoi.status_code == 422


# =========================================================================
# GACH DAU DONG 3 - CA POST LAN GET cho API DOC
# =========================================================================
async def test_doc_bang_giao_thuc_post_json(client, kho):
    goc = datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)
    for phut in range(3):
        kho.dat_thoi_diem(goc + timedelta(minutes=phut))
        await _gui(client, nhiet_do=20.0 + phut)

    phan_hoi = await client.post("/api/v1/du-lieu/doc", json={"n": 2}, headers=DAU_KHOA)
    assert phan_hoi.status_code == 200
    assert [b["nhiet_do"] for b in phan_hoi.json()["ban_ghi"]] == [22.0, 21.0]


async def test_doc_bang_post_form_urlencoded(client, kho):
    await _gui(client)
    phan_hoi = await client.post(
        "/api/v1/du-lieu/doc", data={"n": "1"}, headers=DAU_KHOA
    )
    assert phan_hoi.status_code == 200
    assert phan_hoi.json()["so_luong"] == 1


async def test_doc_bang_post_khong_can_than_request(client):
    """Goi POST /doc rong phai dung mac dinh, khong duoc bao loi."""
    phan_hoi = await client.post("/api/v1/du-lieu/doc", headers=DAU_KHOA)
    assert phan_hoi.status_code == 200


async def test_get_va_post_cho_ket_qua_doc_giong_nhau(client, kho):
    goc = datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)
    for phut in range(3):
        kho.dat_thoi_diem(goc + timedelta(minutes=phut))
        await _gui(client, nhiet_do=20.0 + phut)

    qua_get = await client.get("/api/v1/du-lieu", params={"n": 2}, headers=DAU_KHOA)
    qua_post = await client.post("/api/v1/du-lieu/doc", json={"n": 2}, headers=DAU_KHOA)
    assert qua_get.json() == qua_post.json()


# =========================================================================
# API doc ban ghi CUOI CUNG (muc do 1 & 2 cua de van yeu cau)
# =========================================================================
async def test_doc_ban_ghi_cuoi_cung(client, kho):
    goc = datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc)
    for phut in range(3):
        kho.dat_thoi_diem(goc + timedelta(minutes=phut))
        await _gui(client, nhiet_do=20.0 + phut)

    phan_hoi = await client.get("/api/v1/du-lieu/moi-nhat", headers=DAU_KHOA)
    assert phan_hoi.status_code == 200
    assert phan_hoi.json()["ban_ghi"]["nhiet_do"] == 22.0


async def test_doc_ban_ghi_cuoi_cung_khi_chua_co_du_lieu(client):
    phan_hoi = await client.get("/api/v1/du-lieu/moi-nhat", headers=DAU_KHOA)
    assert phan_hoi.status_code == 404


async def test_doc_ban_ghi_cuoi_cung_cua_mot_thiet_bi(client):
    await _gui(client, ten_thiet_bi="pi4-hnc", nhiet_do=30.0)
    await _gui(client, ten_thiet_bi="pi4-tdbao", nhiet_do=25.0)

    phan_hoi = await client.get(
        "/api/v1/du-lieu/moi-nhat",
        params={"ten_thiet_bi": "pi4-hnc"}, headers=DAU_KHOA,
    )
    assert phan_hoi.json()["ban_ghi"]["nhiet_do"] == 30.0


# =========================================================================
# CHAN DU LIEU RAC
# =========================================================================
@pytest.mark.parametrize("truong,gia_tri_xau", [
    ("nhiet_do", 999),
    ("do_am", 150),
    ("led1", 5),
    ("ten_thiet_bi", ""),
])
async def test_tu_choi_du_lieu_rac_va_khong_ghi_xuong_database(
    client, kho, truong, gia_tri_xau
):
    phan_hoi = await _gui(client, **{truong: gia_tri_xau})
    assert phan_hoi.status_code == 422
    assert kho.tai_lieu == []


async def test_thieu_truong_bat_buoc_thi_bao_loi(client):
    phan_hoi = await client.post(
        "/api/v1/du-lieu", json={"ten_thiet_bi": "pi"}, headers=DAU_KHOA
    )
    assert phan_hoi.status_code == 422


async def test_than_request_khong_phai_json_hop_le(client):
    phan_hoi = await client.post(
        "/api/v1/du-lieu",
        content=b"khong phai json",
        headers={**DAU_KHOA, "Content-Type": "application/json"},
    )
    assert phan_hoi.status_code == 422


# =========================================================================
# TRANG THONG TIN - khong can khoa, de biet server song hay chet
# =========================================================================
async def test_trang_chu_khong_can_khoa(client):
    phan_hoi = await client.get("/")
    assert phan_hoi.status_code == 200
    assert "endpoint" in phan_hoi.json()


async def test_trang_chu_khong_lo_api_key(client):
    assert KHOA not in (await client.get("/")).text
