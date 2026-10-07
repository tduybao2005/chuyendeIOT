import json
import os
import socket
import threading
from time import sleep

import paho.mqtt.client as mqtt
from IoT_Driver_USB import LORA_USB

MQTT_HOST = os.environ.get("IOT_MQTT_HOST", "localhost")
PI_HOST = os.environ.get("IOT_PI_HOST", "100.116.157.59")
PI_PORT = 5005
LORA_COM = os.environ.get("IOT_LORA_COM", "/dev/ttyUSB0")
NODE = 3

GUI_CONGTAC = "buoi10/gui/congtac"
GUI_NHIET_DO = "buoi10/gui/nhiet_do_do_am"
DOC_LED = "buoi10/doc/led"
DOC_DEN_NODE = "buoi10/doc/den_node"

tu_server = {"led": [0, 0, 0], "den_chieu_sang": None, "den_canh_bao": None}

lora = LORA_USB(COM=LORA_COM, address=0)
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.settimeout(1)


def doc_node(reg):
    lora.ser.reset_input_buffer()
    gia_tri = lora.read_data(NODE, reg)
    return None if gia_tri == -1 else gia_tri


def ghi_den(den):
    lora.write_data(NODE, 9, den[0])
    sleep(0.3)
    lora.write_data(NODE, 8, den[1])
    sleep(0.3)


def on_connect(client, userdata, connect_flags, reason_code, properties=None):
    print("Da ket noi MQTT:", reason_code)
    client.subscribe([(DOC_LED, 1), (DOC_DEN_NODE, 1)])


def on_message(client, userdata, msg):
    tu_server.update(json.loads(msg.payload))


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="gateway-buoi10")
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, 1883)
client.loop_start()


def vong_pi():
    while True:
        try:
            udp.sendto(json.dumps({"led": tu_server["led"]}).encode(), (PI_HOST, PI_PORT))
            du_lieu = json.loads(udp.recvfrom(1024)[0])
            if du_lieu["nhiet_do"] is not None:
                client.publish(GUI_NHIET_DO, json.dumps(du_lieu), qos=1)
            print("Pi", du_lieu, "| led gui di", tu_server["led"])
        except (socket.timeout, OSError) as loi:
            print("Pi khong tra loi:", loi)
        sleep(1)


threading.Thread(target=vong_pi, daemon=True).start()

da_ghi = None

try:
    while True:
        den = (tu_server["den_chieu_sang"], tu_server["den_canh_bao"])
        if None not in den and den != da_ghi:
            ghi_den(den)
            da_ghi = den
            sleep(3)

        cong_tac = {}
        for ten, reg in (("sw1", 6), ("sw2", 5)):
            gia_tri = doc_node(reg)
            if gia_tri is not None:
                cong_tac[ten] = 1 if gia_tri == 0 else 0
            sleep(0.3)
        if cong_tac:
            client.publish(GUI_CONGTAC, json.dumps(cong_tac), qos=1)
            sleep(0.1)

        print(f"cong tac {cong_tac} | tu server {tu_server}")
except KeyboardInterrupt:
    print("\nDa dung gateway.")
finally:
    client.loop_stop()
