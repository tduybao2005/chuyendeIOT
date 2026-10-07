import json
import os
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import sleep

import paho.mqtt.client as mqtt

MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
HTTP_PORT = int(os.environ.get("HTTP_PORT", "8000"))
VN = timezone(timedelta(hours=7))

GUI_CONGTAC = "buoi10/gui/congtac"
GUI_NHIET_DO = "buoi10/gui/nhiet_do_do_am"
DOC_LED = "buoi10/doc/led"
DOC_DEN_NODE = "buoi10/doc/den_node"
TRUONG_GUI = {GUI_CONGTAC: ("sw1", "sw2"), GUI_NHIET_DO: ("nhiet_do", "do_am")}

trang_thai = {
    "che_do": "tay",
    "led": [0, 0, 0],
    "sw1": 0,
    "sw2": 0,
    "den_chieu_sang": 0,
    "den_canh_bao": 0,
    "nhiet_do": None,
    "do_am": None,
    "lich": {
        "den_chieu_sang": {"bat": "18:00", "tat": "06:00"},
        "den_canh_bao": {"bat": "22:00", "tat": "05:00"},
    },
}

khoa = threading.Lock()
da_gui = {}

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="server-buoi10")


def trong_khung(bat, tat, bay_gio):
    if bat <= tat:
        return bat <= bay_gio < tat
    return bay_gio >= bat or bay_gio < tat


def tinh_den():
    if trang_thai["che_do"] == "tay":
        return {"den_chieu_sang": trang_thai["sw1"], "den_canh_bao": trang_thai["sw2"]}
    bay_gio = datetime.now(VN).strftime("%H:%M")
    return {ten: int(trong_khung(l["bat"], l["tat"], bay_gio)) for ten, l in trang_thai["lich"].items()}


def cap_nhat(thay_doi=None):
    with khoa:
        trang_thai.update(thay_doi or {})
        trang_thai.update(tinh_den())
        for dich, noi_dung in (
            (DOC_LED, {"led": trang_thai["led"]}),
            (DOC_DEN_NODE, {k: trang_thai[k] for k in ("den_chieu_sang", "den_canh_bao")}),
        ):
            chuoi = json.dumps(noi_dung, sort_keys=True)
            if da_gui.get(dich) != chuoi:
                da_gui[dich] = chuoi
                client.publish(dich, chuoi, qos=1, retain=True)


def on_connect(client, userdata, connect_flags, reason_code, properties=None):
    print("Da ket noi MQTT:", reason_code)
    client.subscribe([(GUI_CONGTAC, 1), (GUI_NHIET_DO, 1)])


def on_message(client, userdata, msg):
    try:
        du_lieu = json.loads(msg.payload)
        cap_nhat({k: du_lieu[k] for k in TRUONG_GUI[msg.topic] if k in du_lieu})
    except Exception as loi:
        print(f"[{msg.topic}] LOI: {loi} | {msg.payload!r}")


def vong_lich():
    while True:
        cap_nhat()
        sleep(1)


TRANG_WEB = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IoT buoi 10</title>
<style>
body{font-family:sans-serif;max-width:600px;margin:1em auto;padding:0 1em}
.o{border:1px solid #ccc;border-radius:8px;padding:.6em 1em;margin:.7em 0}
button{padding:.5em 1em;margin:.2em;border:1px solid #888;border-radius:6px;background:#ddd;cursor:pointer}
button.do.on{background:#f44}button.vang.on{background:#fc0}button.xanh.on{background:#4c4}
</style></head><body>
<h2>IoT - Bài tập mức độ 3</h2>
<div class="o"><b>Cảm biến (Pi)</b><br>Nhiệt độ: <span id="nhiet_do">-</span> °C &nbsp; Độ ẩm: <span id="do_am">-</span> %</div>
<div class="o"><b>Node</b><br>
Công tắc Light: <span id="sw1"></span> &nbsp; Công tắc Alarm: <span id="sw2"></span><br>
Light (đèn chiếu sáng): <span id="den_chieu_sang"></span> &nbsp; Alarm Light (đèn cảnh báo): <span id="den_canh_bao"></span></div>
<div class="o"><b>3 LED trên Pi</b><br>
<button id="led0" class="do" onclick="bam(0)"></button><button id="led1" class="vang" onclick="bam(1)"></button><button id="led2" class="xanh" onclick="bam(2)"></button></div>
<div class="o"><b>Chế độ đèn Node</b><br>
<label><input type="radio" name="che_do" value="tay" onchange="luu()"> Bằng tay (công tắc trên Node)</label><br>
<label><input type="radio" name="che_do" value="tu_dong" onchange="luu()"> Tự động (theo giờ)</label><br>
Đèn chiếu sáng: bật <input type="time" id="cs_bat"> tắt <input type="time" id="cs_tat"><br>
Đèn cảnh báo: bật <input type="time" id="cb_bat"> tắt <input type="time" id="cb_tat"><br>
<button onclick="luu()">Lưu cài đặt</button> <span id="da_luu"></span></div>
<script>
const $ = id => document.getElementById(id), bt = v => v ? "BẬT" : "TẮT", TEN = ["LED đỏ", "LED vàng", "LED xanh"];
let tt = {}, daNap = false;
const gui = (url, du_lieu) => fetch(url, {method: "POST", body: JSON.stringify(du_lieu)});
async function lam() {
  tt = await (await fetch("/api/trang_thai")).json();
  $("nhiet_do").textContent = tt.nhiet_do ?? "-"; $("do_am").textContent = tt.do_am ?? "-";
  for (const k of ["sw1", "sw2", "den_chieu_sang", "den_canh_bao"]) $(k).textContent = bt(tt[k]);
  tt.led.forEach((v, i) => { $("led" + i).textContent = TEN[i] + ": " + bt(v); $("led" + i).className = $("led" + i).className.split(" ")[0] + (v ? " on" : ""); });
  if (!daNap) {
    document.querySelector(`input[name=che_do][value=${tt.che_do}]`).checked = true;
    $("cs_bat").value = tt.lich.den_chieu_sang.bat; $("cs_tat").value = tt.lich.den_chieu_sang.tat;
    $("cb_bat").value = tt.lich.den_canh_bao.bat; $("cb_tat").value = tt.lich.den_canh_bao.tat;
    daNap = true;
  }
}
const bam = i => gui("/api/led", {i, v: 1 - tt.led[i]}).then(lam);
const luu = () => gui("/api/cai_dat", {
  che_do: document.querySelector("input[name=che_do]:checked").value,
  lich: {den_chieu_sang: {bat: $("cs_bat").value, tat: $("cs_tat").value}, den_canh_bao: {bat: $("cb_bat").value, tat: $("cb_tat").value}},
}).then(() => { $("da_luu").textContent = "Đã lưu"; lam(); });
setInterval(lam, 1000); lam();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def tra(self, noi_dung, kieu):
        du_lieu = noi_dung.encode()
        self.send_response(200)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(du_lieu)))
        self.end_headers()
        self.wfile.write(du_lieu)

    def do_GET(self):
        if self.path == "/api/trang_thai":
            with khoa:
                self.tra(json.dumps(trang_thai), "application/json")
        else:
            self.tra(TRANG_WEB, "text/html; charset=utf-8")

    def do_POST(self):
        du_lieu = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/led":
            with khoa:
                led = list(trang_thai["led"])
            led[int(du_lieu["i"])] = int(du_lieu["v"])
            cap_nhat({"led": led})
        elif self.path == "/api/cai_dat":
            cap_nhat({"che_do": du_lieu["che_do"], "lich": du_lieu["lich"]})
        self.tra("{}", "application/json")

    def log_message(self, *args):
        pass


client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, 1883)
client.loop_start()
cap_nhat()
threading.Thread(target=vong_lich, daemon=True).start()
print(f"Server: web http://localhost:{HTTP_PORT} | MQTT {MQTT_HOST}:1883")
ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler).serve_forever()
