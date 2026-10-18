import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import sleep

import paho.mqtt.client as mqtt
from pymongo import DESCENDING, MongoClient

from he_thong import TOPIC_NHAN, HeThong, LoiDuLieu


def _doc_file_env():
    gia_tri = {}
    file_env = Path(__file__).with_name(".env")
    if file_env.exists():
        for dong in file_env.read_text(encoding="utf-8").splitlines():
            dong = dong.strip()
            if dong and not dong.startswith("#") and "=" in dong:
                ten, gt = dong.split("=", 1)
                gia_tri[ten.strip()] = gt.strip().strip('"').strip("'")
    return gia_tri


_ENV = _doc_file_env()


def _cau_hinh(ten, mac_dinh=""):
    return os.environ.get(ten, _ENV.get(ten, mac_dinh))


MONGODB_URI = _cau_hinh("MONGODB_URI")
MONGODB_DB = _cau_hinh("MONGODB_DB", "iot_buoi11")
MQTT_HOST = _cau_hinh("MQTT_HOST", "localhost")
MQTT_PORT = int(_cau_hinh("MQTT_PORT", "1883"))
HTTP_PORT = int(_cau_hinh("HTTP_PORT", "8000"))
if not MONGODB_URI:
    raise RuntimeError("Thieu MONGODB_URI - dien trong master/.env")

TRANG_WEB = Path(__file__).with_name("web.html").read_bytes()

db = MongoClient(MONGODB_URI, tz_aware=True, serverSelectionTimeoutMS=5000)[MONGODB_DB]
hang_doi_db = queue.Queue(maxsize=10000)


def luu_db(bang, ban_ghi):
    try:
        hang_doi_db.put_nowait((bang, ban_ghi))
    except queue.Full:
        print("[DB] hang doi day - bo 1 ban ghi", bang)


def vong_db():
    while True:
        bang, ban_ghi = hang_doi_db.get()
        try:
            db[bang].insert_one(ban_ghi)
        except Exception as loi:
            print(f"[DB] LOI ghi {bang}: {loi}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="master-buoi11")
he_thong = HeThong(
    publish=lambda topic, chuoi: client.publish(topic, chuoi, qos=1, retain=True),
    luu_db=luu_db,
)


def on_connect(client, userdata, connect_flags, reason_code, properties=None):
    print("Da ket noi MQTT:", reason_code)
    client.subscribe([(topic, 1) for topic in TOPIC_NHAN])
    he_thong.gui_lai()


def on_message(client, userdata, msg):
    try:
        he_thong.nhan_mqtt(msg.topic, msg.payload)
    except Exception as loi:
        print(f"[{msg.topic}] LOI: {loi} | {msg.payload!r}")


def vong_1_giay():
    while True:
        he_thong.tinh_lai()
        sleep(1)


def nap_cai_dat_cu():
    try:
        lich = db.cai_dat.find_one({"loai": "lich"}, sort=[("_id", DESCENDING)])
        nguong = db.cai_dat.find_one({"loai": "nguong"}, sort=[("_id", DESCENDING)])
        he_thong.nap_cai_dat(lich, nguong)
        print("Da nap cai dat lan Set cuoi tu Database")
    except Exception as loi:
        print("[DB] Khong nap duoc cai dat cu (dung mac dinh):", loi)


class Handler(BaseHTTPRequestHandler):
    def tra(self, ma, noi_dung, kieu="application/json"):
        if isinstance(noi_dung, str):
            noi_dung = noi_dung.encode()
        self.send_response(ma)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(noi_dung)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(noi_dung)

    def do_GET(self):
        if self.path == "/api/trang_thai":
            self.tra(200, json.dumps(he_thong.anh_chup()))
        elif self.path in ("/", "/index.html"):
            self.tra(200, TRANG_WEB, "text/html; charset=utf-8")
        else:
            self.tra(404, '{"loi": "khong co trang nay"}')

    def do_POST(self):
        try:
            than = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            du_lieu = json.loads(than or b"null")
            if self.path == "/api/nut":
                if not isinstance(du_lieu, dict):
                    raise LoiDuLieu("sai dinh dang")
                ket_qua = he_thong.bam_nut(du_lieu.get("ten"), du_lieu.get("gia_tri"))
            elif self.path == "/api/lich":
                ket_qua = he_thong.luu_lich(du_lieu)
            elif self.path == "/api/nguong":
                ket_qua = he_thong.luu_nguong(du_lieu)
            else:
                return self.tra(404, '{"loi": "khong co API nay"}')
        except ValueError as loi:
            return self.tra(400, json.dumps({"loi": str(loi)}))
        self.tra(200, json.dumps(ket_qua))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    nap_cai_dat_cu()
    threading.Thread(target=vong_db, daemon=True).start()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect_async(MQTT_HOST, MQTT_PORT)
    client.loop_start()
    threading.Thread(target=vong_1_giay, daemon=True).start()
    print(f"Master: web http://localhost:{HTTP_PORT} | MQTT {MQTT_HOST}:{MQTT_PORT} | DB {MONGODB_DB}")
    ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler).serve_forever()
