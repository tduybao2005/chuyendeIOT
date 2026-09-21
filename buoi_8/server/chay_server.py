#!/usr/bin/env python3
"""
CHAY SERVER - diem khoi dong cho nguoi dung.

    cd buoi_8/server
    ../.venv/bin/python chay_server.py

Tuong duong `uvicorn main:app --host ... --port ...` nhung co them ba thu
lam kha nhieu khac biet luc chay thuc te:

  1. Doc HOST/PORT tu .env, khong phai go lai tham so moi lan.
  2. BAO LOI CAU HINH BANG TIENG NGUOI. Thieu MONGODB_URI thi uvicorn nem
     ra mot vet loi Pydantic dai ba chuc dong - o day bat lai va in dung
     cau can sua.
  3. IN SAN DIA CHI LAN de dien vao Pi. Day la thu hay mat thoi gian nhat
     luc lap rap: phai doan xem Pi goi vao dia chi nao.
"""

import socket
import sys

import uvicorn

from cau_hinh import doc_cau_hinh


def dia_chi_lan() -> str:
    """Doan dia chi LAN cua may nay, de in ra cho nguoi dung dien vao Pi.

    Mo mot socket UDP toi 8.8.8.8 roi hoi he dieu hanh "dinh di ra bang card
    nao". UDP khong bat tay nen KHONG co goi tin nao thuc su duoc gui di va
    khong can Internet - chi la cach hoi bang dinh tuyen.

    Dung socket.gethostbyname(hostname) thay the thi tren nhieu may Linux no
    tra ve 127.0.1.1 (dong trong /etc/hosts) - dia chi do Pi khong goi duoc.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "<chay 'hostname -I' de xem dia chi>"


def main() -> None:
    try:
        cau_hinh = doc_cau_hinh()
    except Exception as loi:
        print("=" * 70)
        print("KHONG DOC DUOC CAU HINH")
        print("=" * 70)
        print(loi)
        print()
        print("Kiem tra: da tao file .env chua?")
        print("    cd buoi_8/server")
        print("    cp .env.example .env")
        print("    nano .env          # dien MONGODB_URI va API_KEY")
        print()
        print("Huong dan lay MONGODB_URI: buoi_8/HUONG_DAN_ATLAS.md")
        sys.exit(2)

    dia_chi = dia_chi_lan()
    print("=" * 70)
    print("IoT buoi 8 - muc do 3 | HTTP Server (FastAPI + MongoDB Atlas)")
    print("=" * 70)
    print(f"  Database   : {cau_hinh.mongodb_db}.{cau_hinh.mongodb_collection}")
    print(f"  Tai lieu   : http://{dia_chi}:{cau_hinh.port}/docs")
    print()
    print("  DIEN DONG NAY VAO RASPBERRY PI:")
    print(f"      export IOT_BUOI8_SERVER=\"http://{dia_chi}:{cau_hinh.port}\"")
    print()
    print("  API_KEY khong in ra day. Xem trong file .env neu can.")
    print("=" * 70)

    uvicorn.run(
        "main:app",
        host=cau_hinh.host,
        port=cau_hinh.port,
        # reload=False: bat reload thi uvicorn chay them mot tien trinh theo
        # doi file, moi lan luu file la mo LAI ket noi toi Atlas. Goi free M0
        # gioi han so ket noi, sua file vai chuc lan la cham tran.
        reload=False,
        log_level="info",
        # ==============================================================
        # KEEP-ALIVE PHAI DAI HON NHIP GUI CUA CLIENT
        #
        # Mac dinh cua uvicorn la 5 GIAY, ma nhip gui cua Pi cung dung 5
        # giay (NHIP_GUI trong cau_hinh_pi.py). Hai con so trung nhau nen
        # giua hai chu ky, ket noi nam khong dung bang thoi gian cho phep:
        # server dong no dung luc Pi dinh dung lai -> Pi nhan
        # RemoteDisconnected.
        #
        # Da do thuc te tu pi4-tdbao qua WiFi ngay 2026-09-21:
        #     nhip 1s -> 0/12 loi        nhip 5s -> 5/12 loi
        #
        # Dat 65 giay: dai hon han moi nhip client hop ly, nen ket noi
        # khong con bi dong giua chung. Doi lai server giu socket lau hon
        # mot chut - khong dang ke voi vai thiet bi trong phong hoc.
        # ==============================================================
        timeout_keep_alive=65,
    )


if __name__ == "__main__":
    main()
