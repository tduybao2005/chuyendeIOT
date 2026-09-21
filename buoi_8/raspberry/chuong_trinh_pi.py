#!/usr/bin/env python3
"""Client Pi toi gian cho API IoT buoi 8."""

import argparse
import sys
from time import sleep

import requests

import cau_hinh_pi as cfg
from logic_led import den_dang_sang, mo_ta_den


class PhanCung:
    def __init__(self):
        from gpiozero import LED
        from seeed_dht import DHT

        self.cam_bien = DHT(cfg.LOAI_DHT, cfg.CHAN_DHT)
        self.den = (
            LED(cfg.CHAN_LED_DO, initial_value=False),
            LED(cfg.CHAN_LED_VANG, initial_value=False),
            LED(cfg.CHAN_LED_XANH, initial_value=False),
        )

    def doc(self):
        return self.cam_bien.read()

    def bat_den(self, trang_thai):
        for den, bat in zip(self.den, trang_thai):
            den.on() if bat else den.off()

    def tat_den(self):
        for den in self.den:
            den.off()


class MayChu:
    def __init__(self):
        self.url = cfg.SERVER_URL.rstrip("/") + "/api/v1/du-lieu"
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": cfg.API_KEY})

    def gui_post_json(self, du_lieu):
        return self._json(self.session.post(self.url, json=du_lieu, timeout=cfg.HTTP_TIMEOUT))

    def gui_get(self, du_lieu):
        return self._json(self.session.get(self.url + "/gui", params=du_lieu, timeout=cfg.HTTP_TIMEOUT))

    def doc_get(self, n, tu=None, den=None):
        return self._json(self.session.get(
            self.url, params=self._tham_so_doc(n, tu, den), timeout=cfg.HTTP_TIMEOUT,
        ))["ban_ghi"]

    def doc_post_json(self, n, tu=None, den=None):
        return self._json(self.session.post(
            self.url + "/doc", json=self._tham_so_doc(n, tu, den),
            timeout=cfg.HTTP_TIMEOUT,
        ))["ban_ghi"]

    @staticmethod
    def _tham_so_doc(n, tu, den):
        tham_so = {"n": n, "ten_thiet_bi": cfg.TEN_THIET_BI}
        if tu:
            tham_so["tu"] = tu
        if den:
            tham_so["den"] = den
        return tham_so

    @staticmethod
    def _json(phan_hoi):
        if phan_hoi.status_code >= 400:
            try:
                ly_do = phan_hoi.json().get("detail", phan_hoi.text)
            except ValueError:
                ly_do = phan_hoi.text
            raise RuntimeError(f"HTTP {phan_hoi.status_code}: {ly_do}")
        return phan_hoi.json()


def doc_tham_so():
    parser = argparse.ArgumentParser(description="Gui va doc du lieu IoT qua HTTP")
    parser.add_argument("--gui", choices=("post", "get"), default="post",
                        help="Giao thuc gui: POST JSON hoac GET")
    parser.add_argument("--doc", choices=("get", "post"), default="get",
                        help="Giao thuc doc: GET hoac POST JSON")
    parser.add_argument("--n", type=int, default=5,
                        help="So ban ghi gan nhat can doc")
    parser.add_argument("--tu", help="Thoi diem bat dau, vi du 2026-09-21T08:00:00")
    parser.add_argument("--den", help="Thoi diem ket thuc, vi du 2026-09-21T09:00:00")
    parser.add_argument("--so-vong", type=int, default=0,
                        help="So lan gui (0 = chay lien tuc)")
    return parser.parse_args()


def in_ban_ghi(ban_ghi):
    for dong in ban_ghi:
        leds = "".join(str(dong.get(f"led{i}", "?")) for i in (1, 2, 3))
        print(
            f"  [{dong.get('thoi_gian_gui', '?')}] "
            f"{dong.get('ten_thiet_bi', '?')} | "
            f"nhiet do {dong.get('nhiet_do', '?')} C | "
            f"do am {dong.get('do_am', '?')} % | LED {leds} | "
            f"ID {dong.get('id', '?')}"
        )


def main():
    args = doc_tham_so()
    if not cfg.API_KEY:
        print("Thieu IOT_BUOI8_API_KEY")
        return 2

    phan_cung = PhanCung()
    may_chu = MayChu()
    print(f"Server: {cfg.SERVER_URL}")
    print(f"Gui: {args.gui.upper()} | Doc: {args.doc.upper()} | Nhip: {cfg.NHIP_GUI}s")
    print("Nhan Ctrl+C de dung.\n")

    try:
        vong = 0
        while not args.so_vong or vong < args.so_vong:
            vong += 1
            led = den_dang_sang(vong - 1)
            phan_cung.bat_den(led)
            do_am, nhiet_do = phan_cung.doc()
            du_lieu = {
                "ten_thiet_bi": cfg.TEN_THIET_BI,
                "nhiet_do": nhiet_do,
                "do_am": do_am,
                "led1": led[0],
                "led2": led[1],
                "led3": led[2],
            }
            if args.gui == "post":
                may_chu.gui_post_json(du_lieu)
            else:
                may_chu.gui_get(du_lieu)

            if args.doc == "get":
                ban_ghi = may_chu.doc_get(args.n, args.tu, args.den)
            else:
                ban_ghi = may_chu.doc_post_json(args.n, args.tu, args.den)
            print(f"[{vong}] Den cuc bo: {mo_ta_den(led)} | Du lieu doc tu server:")
            in_ban_ghi(ban_ghi)
            sleep(cfg.NHIP_GUI)
    except KeyboardInterrupt:
        print("\nDa dung chuong trinh.")
    except (requests.RequestException, RuntimeError, TypeError) as loi:
        print(f"LOI: {loi}")
        return 1
    finally:
        phan_cung.tat_den()
    return 0


if __name__ == "__main__":
    sys.exit(main())
