#!/usr/bin/env python3
"""
KIEM TRA KET NOI MONGODB ATLAS - chay truoc khi khoi dong server lan dau.

    cd buoi_8/server
    ../.venv/bin/python kiem_tra_atlas.py

=========================================================================
VI SAO CAN FILE NAY
=========================================================================
Bo test (pytest) chay OFFLINE - no dung kho du lieu gia trong bo nho nen
khong cham toi Atlas. Do la co y: test phai chay duoc moi luc, khong phu
thuoc mang, khong lam ban database that.

Nhung nhu vay test KHONG chung minh duoc Atlas da cau hinh dung. File nay
lam not phan do: no thu lam that ca ba viec (ket noi, ghi, doc) roi xoa ban
ghi thu di.

Ba loi hay gap nhat khi noi Atlas lan dau - deu duoc file nay chi ro:
  1. Quen mo Network Access -> Atlas chan dia chi IP cua may ban.
  2. Sai mat khau database user (hay nham voi mat khau tai khoan Atlas).
  3. Mat khau co ky tu dac biet ma chua ma hoa URL.
"""

import asyncio
import sys
from datetime import datetime, timezone

from pymongo.errors import (ConfigurationError, OperationFailure,
                            ServerSelectionTimeoutError)

from cau_hinh import doc_cau_hinh
from kho_du_lieu import mo_ket_noi
from mo_hinh import DuLieuGui, ThamSoDoc

TEN_THIET_BI_THU = "__kiem_tra_ket_noi__"


async def chay() -> int:
    try:
        cau_hinh = doc_cau_hinh()
    except Exception as loi:
        print("[X] Cau hinh chua dung:")
        print(f"    {loi}")
        print("\n    Tao file .env: cp .env.example .env  roi dien vao.")
        return 2

    print(f"[.] Dang ket noi toi database '{cau_hinh.mongodb_db}' ...")
    client, kho = mo_ket_noi(
        cau_hinh.mongodb_uri, cau_hinh.mongodb_db, cau_hinh.mongodb_collection,
    )

    try:
        # --- 1. Ket noi -------------------------------------------------
        # ping la lenh nhe nhat de kiem tra "co noi chuyen duoc khong".
        await asyncio.wait_for(client.admin.command("ping"), timeout=20)
        print("[v] Ket noi Atlas THANH CONG")

        # --- 2. Tao index ------------------------------------------------
        await kho.tao_index()
        print("[v] Tao index thanh cong (quyen ghi OK)")

        # --- 3. Ghi thu --------------------------------------------------
        ban_ghi = await kho.them(DuLieuGui(
            ten_thiet_bi=TEN_THIET_BI_THU, nhiet_do=28.5, do_am=70.0,
            led1=0, led2=1, led3=0,
        ))
        print(f"[v] Ghi thu thanh cong, ID = {ban_ghi.id}")

        # --- 4. Doc lai --------------------------------------------------
        doc_ve = await kho.doc(ThamSoDoc(n=1, ten_thiet_bi=TEN_THIET_BI_THU))
        if not doc_ve or doc_ve[0].id != ban_ghi.id:
            print("[X] Ghi duoc nhung doc lai khong thay ban ghi vua ghi.")
            return 1
        print(f"[v] Doc lai thanh cong: {doc_ve[0].nhiet_do} C, "
              f"{doc_ve[0].do_am} %, luc {doc_ve[0].thoi_gian_gui}")

        # --- 5. Kiem tra KHONG luu API_KEY -------------------------------
        # De bai: "khong luu API vao Database". Doc thang tai lieu tho tu
        # MongoDB (khong qua mo hinh, vi mo hinh se loc mat) de nhin tan mat
        # nhung gi that su nam trong Atlas.
        collection = client[cau_hinh.mongodb_db][cau_hinh.mongodb_collection]
        from bson import ObjectId
        tai_lieu_tho = await collection.find_one({"_id": ObjectId(ban_ghi.id)})
        if cau_hinh.api_key in str(tai_lieu_tho):
            print("[X] API_KEY BI LUU XUONG DATABASE - sai yeu cau de bai!")
            return 1
        print("[v] Ban ghi trong Atlas KHONG chua API_KEY (dung yeu cau de bai)")
        print(f"    Cac truong thuc te: {sorted(tai_lieu_tho.keys())}")

        # --- 6. Don dep --------------------------------------------------
        await collection.delete_many({"ten_thiet_bi": TEN_THIET_BI_THU})
        print("[v] Da xoa ban ghi thu, database sach")

        print("\n=== TAT CA DEU TOT - chay duoc server: python chay_server.py ===")
        return 0

    except (ServerSelectionTimeoutError, asyncio.TimeoutError):
        print("[X] KHONG KET NOI DUOC TOI ATLAS (het thoi gian cho).")
        print("\n    Nguyen nhan hay gap nhat la CHUA MO NETWORK ACCESS:")
        print("      Atlas > Network Access > Add IP Address")
        print("      > Allow Access from Anywhere (0.0.0.0/0) > Confirm")
        print("      Doi khoang 1-2 phut cho trang thai chuyen sang 'Active'.")
        print("\n    Ngoai ra kiem tra: may co vao duoc Internet khong, va")
        print("    ten cluster trong MONGODB_URI da go dung chua.")
        return 1

    except OperationFailure as loi:
        print(f"[X] ATLAS TU CHOI: {loi}")
        print("\n    Thuong la sai ten dang nhap / mat khau DATABASE USER.")
        print("    Luu y: day KHONG phai mat khau tai khoan Atlas, ma la user")
        print("    tao rieng o muc 'Database Access'.")
        print("    Doi mat khau: Atlas > Database Access > Edit > Edit Password")
        return 1

    except ConfigurationError as loi:
        print(f"[X] CHUOI KET NOI SAI DINH DANG: {loi}")
        print("\n    Kiem tra MONGODB_URI trong .env:")
        print("      - Da thay <db_password> bang mat khau that chua?")
        print("      - Mat khau co ky tu dac biet (@ : / ? # [ ] %) khong?")
        print("        Neu co thi phai ma hoa URL:")
        print('          python3 -c "import urllib.parse,sys; '
              'print(urllib.parse.quote_plus(sys.argv[1]))" \'mat_khau\'')
        return 1

    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(chay()))
