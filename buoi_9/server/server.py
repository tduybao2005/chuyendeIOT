"""
Buoi 9 - Bai tap muc do 3 (10 diem): MQTT Broker co Database.

De bai:
    - Topic gui TUNG du lieu (nhiet do / do am / trang thai tung LED) len Server.
    - Topic gui TOAN BO du lieu (nhiet do + do am + ca 3 LED) len Server.
    - Topic doc TUNG du lieu moi nhat tu Server.
    - Topic doc TOAN BO du lieu moi nhat tu Server.
    - Du lieu ho tro ca json va form-urlencoded (moi loai 2 topic rieng).
    Luu y bat buoc:
    - Gui TUNG cung phai kich hoat (cap nhat) topic doc TOAN BO.
    - Gui TOAN BO cung phai kich hoat (cap nhat) topic doc TUNG.
    - Gui bang topic json thi ben Subscribe bang topic form-urlencoded (va
      nguoc lai) van phai thay du lieu.

Thiet ke (giai thich trong README):
    8 topic = {gui, doc} x {tung, toanbo} x {json, form}. Server SUBSCRIBE 4
    topic "gui", moi khi co tin nhan thi: (1) luu vao MongoDB kem ID (Mongo
    tu sinh), thoi gian (server tu gan), ten thiet bi; (2) cap nhat trang
    thai moi nhat trong bo nho; (3) PUBLISH (retain=True) lai tren CA 4 topic
    "doc" (tung+toanbo, json+form) - retain=True de client moi subscribe vao
    la co ngay gia tri moi nhat, dung y nghia "doc du lieu moi nhat tu
    Server" cua MQTT (khong can hoi lai nhu HTTP GET).

Chay:
    python3 server.py
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

import paho.mqtt.client as mqtt
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Cau hinh - doc file .env cung thu muc (neu co), bien moi truong duoc uu
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
MONGODB_DB = _cau_hinh("MONGODB_DB", "iot_buoi9")
MONGODB_COLLECTION = _cau_hinh("MONGODB_COLLECTION", "du_lieu_mqtt")
MQTT_HOST = _cau_hinh("MQTT_HOST", "localhost")  # broker Mosquitto chay ngay tren may nay
MQTT_PORT = int(_cau_hinh("MQTT_PORT", "1883"))

if not MONGODB_URI:
    raise RuntimeError("Thieu MONGODB_URI - dien trong server/.env")

# ---------------------------------------------------------------------------
# Topic - 8 topic = {gui, doc} x {tung, toanbo} x {json, form}
#
# "gui"/"doc" la TEN GOI THEO CONG DUNG cua topic (dung nguyen van de bai:
# "Topic dung de GUI... len Server" / "Topic dung de DOC... tu Server"),
# KHONG PHAI ten thiet bi nao dang publish. De khong nham:
#
#   topic GUI  -> Pi PUBLISH, SERVER SUBSCRIBE (server la noi NHAN du lieu)
#   topic DOC  -> SERVER PUBLISH (retain=True), Pi SUBSCRIBE (Pi la noi DOC)
# ---------------------------------------------------------------------------
GUI_TUNG_JSON = "buoi9/gui/tung/json"
GUI_TUNG_FORM = "buoi9/gui/tung/form"
GUI_TOANBO_JSON = "buoi9/gui/toanbo/json"
GUI_TOANBO_FORM = "buoi9/gui/toanbo/form"

DOC_TUNG_JSON = "buoi9/doc/tung/json"
DOC_TUNG_FORM = "buoi9/doc/tung/form"
DOC_TOANBO_JSON = "buoi9/doc/toanbo/json"
DOC_TOANBO_FORM = "buoi9/doc/toanbo/form"

CAC_TRUONG_TOANBO = ("nhiet_do", "do_am", "led1", "led2", "led3")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
_mongo = MongoClient(MONGODB_URI, tz_aware=True, tzinfo=timezone.utc)
bo_suu_tap = _mongo[MONGODB_DB][MONGODB_COLLECTION]

# Trang thai moi nhat tung thiet bi, giu trong bo nho de tra loi ngay cho
# "Luu y bat buoc" (gui tung phai kich hoat duoc topic doc toan bo va nguoc
# lai) ma khong can doc lai Database moi lan.
trang_thai_hien_tai: dict[str, dict] = {}


def luu_db(ban_ghi: dict) -> None:
    tai_lieu = dict(ban_ghi)
    tai_lieu["thoi_gian_gui"] = datetime.now(timezone.utc)
    bo_suu_tap.insert_one(tai_lieu)


# ---------------------------------------------------------------------------
# Ma hoa / giai ma json va form-urlencoded
# ---------------------------------------------------------------------------
def giai_ma(payload: bytes, dinh_dang: str) -> dict:
    chuoi = payload.decode("utf-8")
    if dinh_dang == "json":
        return json.loads(chuoi)
    return dict(parse_qsl(chuoi))


def ma_hoa(du_lieu: dict, dinh_dang: str) -> str:
    if dinh_dang == "json":
        return json.dumps(du_lieu)
    return urlencode(du_lieu)


# ---------------------------------------------------------------------------
# Xu ly khi nhan duoc tin nhan tren cac topic GUI
# ---------------------------------------------------------------------------
def xu_ly_tung(client: mqtt.Client, du_lieu: dict) -> None:
    ten_thiet_bi = str(du_lieu["ten_thiet_bi"])
    ten_truong = str(du_lieu["ten_truong"])
    if ten_truong not in CAC_TRUONG_TOANBO:
        raise ValueError(f"ten_truong khong hop le: {ten_truong}")
    gia_tri = float(du_lieu["gia_tri"])

    luu_db({"loai": "tung", "ten_thiet_bi": ten_thiet_bi, "ten_truong": ten_truong, "gia_tri": gia_tri})

    trang_thai = trang_thai_hien_tai.setdefault(ten_thiet_bi, {})
    trang_thai[ten_truong] = gia_tri

    tung = {"ten_thiet_bi": ten_thiet_bi, "ten_truong": ten_truong, "gia_tri": gia_tri}
    client.publish(DOC_TUNG_JSON, ma_hoa(tung, "json"), retain=True)
    client.publish(DOC_TUNG_FORM, ma_hoa(tung, "form"), retain=True)

    # Luu y bat buoc: gui TUNG cung phai kich hoat topic doc TOAN BO.
    toan_bo = {"ten_thiet_bi": ten_thiet_bi, **trang_thai}
    client.publish(DOC_TOANBO_JSON, ma_hoa(toan_bo, "json"), retain=True)
    client.publish(DOC_TOANBO_FORM, ma_hoa(toan_bo, "form"), retain=True)


def xu_ly_toanbo(client: mqtt.Client, du_lieu: dict) -> None:
    ten_thiet_bi = str(du_lieu["ten_thiet_bi"])
    cac_gia_tri = {truong: float(du_lieu[truong]) for truong in CAC_TRUONG_TOANBO}

    luu_db({"loai": "toanbo", "ten_thiet_bi": ten_thiet_bi, **cac_gia_tri})
    trang_thai_hien_tai[ten_thiet_bi] = dict(cac_gia_tri)

    toan_bo = {"ten_thiet_bi": ten_thiet_bi, **cac_gia_tri}
    client.publish(DOC_TOANBO_JSON, ma_hoa(toan_bo, "json"), retain=True)
    client.publish(DOC_TOANBO_FORM, ma_hoa(toan_bo, "form"), retain=True)

    # Luu y bat buoc: gui TOAN BO cung phai kich hoat topic doc TUNG (phat
    # rieng le tung truong mot).
    for ten_truong, gia_tri in cac_gia_tri.items():
        tung = {"ten_thiet_bi": ten_thiet_bi, "ten_truong": ten_truong, "gia_tri": gia_tri}
        client.publish(DOC_TUNG_JSON, ma_hoa(tung, "json"), retain=True)
        client.publish(DOC_TUNG_FORM, ma_hoa(tung, "form"), retain=True)


def on_connect(client, userdata, connect_flags, reason_code, properties=None):
    print("Da ket noi MQTT broker, ma:", reason_code)
    for topic in (GUI_TUNG_JSON, GUI_TUNG_FORM, GUI_TOANBO_JSON, GUI_TOANBO_FORM):
        client.subscribe(topic, qos=1)
        print("  subscribe:", topic)


def on_message(client, userdata, msg):
    dinh_dang = "json" if msg.topic.endswith("/json") else "form"
    try:
        du_lieu = giai_ma(msg.payload, dinh_dang)
        if "/tung/" in msg.topic:
            xu_ly_tung(client, du_lieu)
        else:
            xu_ly_toanbo(client, du_lieu)
        print(f"[{msg.topic}] OK: {du_lieu}")
    except Exception as loi:
        print(f"[{msg.topic}] LOI: {loi} | payload={msg.payload!r}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="server-buoi9")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    print(f"Server buoi 9 - MQTT broker {MQTT_HOST}:{MQTT_PORT} | DB {MONGODB_DB}.{MONGODB_COLLECTION}")
    client.loop_forever()


if __name__ == "__main__":
    main()
