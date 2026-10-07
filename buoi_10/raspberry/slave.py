import json
import socket

from gpiozero import LED
from seeed_dht import DHT

UDP_PORT = 5005

cam_bien = DHT("11", 5)
den = (LED(16), LED(24), LED(22))


def doc_cam_bien():
    try:
        do_am, nhiet_do = cam_bien.read()
        return float(nhiet_do), float(do_am)
    except Exception as loi:
        print("Loi doc DHT11:", loi)
        return None, None


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))
print("Slave cho UDP o cong", UDP_PORT)

while True:
    goi, dia_chi = sock.recvfrom(1024)
    try:
        led = json.loads(goi)["led"]
    except Exception as loi:
        print("Goi sai:", loi, goi)
        continue
    for bong, bat in zip(den, led):
        bong.on() if bat else bong.off()
    nhiet_do, do_am = doc_cam_bien()
    sock.sendto(json.dumps({"nhiet_do": nhiet_do, "do_am": do_am}).encode(), dia_chi)
    print(f"led(do,vang,xanh)={led} | {nhiet_do} C, {do_am}%")
