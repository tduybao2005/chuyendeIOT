"""
Buoi 7 - Frame truyen du lieu giua Master (may tinh) va Slave (Raspberry Pi).

De bai bat buoc:
    - Nhom 3 (le) -> PHAI dung UDP de trao doi du lieu.
    - Frame phai co CRC.
    - Frame phai "co tinh logic, bao quat duoc tat ca cac truong hop".

File nay KHONG phu thuoc thu vien Grove/GPIO nao ca (thuan Python + struct),
nen dung chung duoc tren ca may tinh (Master) lan Raspberry Pi (Slave).
Khi trien khai, chep file nay ra ca 2 may, dat cung thu muc voi script
tuong ung (slave/chuong_trinh_slave_pi.py va master/chuong_trinh_master_pc.py).

======================================================================
CAU TRUC FRAME (dung cho ca 2 chieu Master<->Slave)
======================================================================
    | STX (1B) | TYPE (1B) | SEQ (1B) | LEN (1B) | PAYLOAD (LEN byte) | CRC16 (2B) | ETX (1B) |

    STX   = 0xAA  - byte danh dau BAT DAU frame. Vi UDP la giao thuc gui
                    tung goi rieng le (khong noi tiep nhu TCP) nen ve ly
                    thuyet khong bi "lech byte" nhu TCP, nhung van giu STX/ETX
                    de nguoi doc code/bao cao thay ro ranh gioi frame va de
                    mo rong sang TCP sau nay ma khong phai thiet ke lai.
    TYPE  = loai ban tin, xem hang so TYPE_* ben duoi. Nho co truong nay,
            1 frame co the mang nhieu loai du lieu khac nhau (cam bien,
            dieu khien LED, ...) ma van dung chung 1 cau truc.
    SEQ   = so thu tu ban tin, tang dan 0..255 roi quay vong. Dung de:
              + Ben nhan biet co bi MAT GOI hay khong (UDP khong dam bao
                gui toi, khong dam bao dung thu tu).
              + Phat hien goi DEN TRE / GOI TRUNG (vd goi LED_CTRL cu den
                sau goi moi thi bo qua, khong ap dung nguoc lai trang thai).
    LEN   = so byte cua PAYLOAD, de ben nhan biet doc bao nhieu byte truoc
            khi toi CRC (ho tro rieng cho truong hop mo rong them TYPE moi
            co do dai payload khac nhau).
    PAYLOAD = du lieu thuc su, cau truc tuy theo TYPE (xem cac ham encode/
              decode ben duoi).
    CRC16 = CRC-16/CCITT (poly 0x1021, init 0xFFFF) tinh tren
            (TYPE + SEQ + LEN + PAYLOAD). Ben nhan tinh lai CRC roi so
            sanh; neu sai lech (nhieu duong truyen, mat byte, ...) thi
            HUY frame, khong xu ly - dam bao khong bao gio ap dung nham
            du lieu bi hong.
    ETX   = 0x55  - byte danh dau KET THUC frame, dung de kiem tra cheo
            them mot lan nua truoc khi tin CRC (neu STX/ETX sai vi tri thi
            chac chan frame hong, khoi can tinh CRC cho ton cong).

======================================================================
CAC LOAI BAN TIN (TYPE)
======================================================================
    TYPE_SENSOR_DATA (0x01) - Slave gui cho Master, moi 1 giay:
        PAYLOAD (5 byte):
            FLAGS  (1B) - bit0: nhiet do hop le (1) hay khong (0)
                          bit1: do am   hop le (1) hay khong (0)
                          (cac bit con lai du phong, luon = 0)
            TEMP   (2B, signed, big-endian) - nhiet do * 10 (1 so le).
                          Neu FLAGS bit0 = 0 thi gia tri nay khong co y
                          nghia (Slave doc loi cam bien), Master phai bo
                          qua khong tinh vao trung binh.
            HUMI   (2B, signed, big-endian) - do am * 10 (1 so le), cung
                          quy uoc nhu TEMP voi FLAGS bit1.
        Dung so nguyen*10 (fixed-point) thay vi float de tranh sai khac
        bieu dien dau phay dong giua cac nen tang/kien truc CPU khac nhau
        khi truyen nhi phan qua mang - so nguyen big-endian luon nhat quan.

    TYPE_LED_CTRL (0x02) - Master gui cho Slave, moi 1 giay:
        PAYLOAD (1 byte):
            LED_MASK (1B) - bit0: LED DO, bit1: LED VANG, bit2: LED XANH
                            (1 = sang, 0 = tat, cac bit con lai du phong).
        Slave chi viec ap dung dung mask nhan duoc len 3 LED vat ly - toan
        bo logic "sang duoi Do->Vang->Xanh moi 1 giay" nam ben Master.

======================================================================
"""

import struct

STX = 0xAA
ETX = 0x55

TYPE_SENSOR_DATA = 0x01
TYPE_LED_CTRL = 0x02

# Vi tri bit trong FLAGS cua SENSOR_DATA
FLAG_TEMP_VALID = 0x01
FLAG_HUMI_VALID = 0x02

# Vi tri bit trong LED_MASK cua LED_CTRL
LED_BIT_RED = 0x01
LED_BIT_YELLOW = 0x02
LED_BIT_GREEN = 0x04

_HEADER_STRUCT = struct.Struct(">BBBB")  # STX, TYPE, SEQ, LEN
_CRC_STRUCT = struct.Struct(">H")        # CRC16, big-endian


def crc16_ccitt(data: bytes, crc: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF), tinh tung bit.

    Day la thuat toan CRC pho bien, thuc hien "tay" (khong dung thu vien
    ngoai) de dung duoc tren moi may (Master la PC, Slave la Raspberry Pi)
    ma khong can cai them goi gi.
    """
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF


def build_frame(msg_type: int, seq: int, payload: bytes) -> bytes:
    """Dong goi (TYPE, SEQ, PAYLOAD) thanh 1 frame hoan chinh de gui qua UDP."""
    seq &= 0xFF
    body = bytes([msg_type & 0xFF, seq, len(payload)]) + payload
    crc = crc16_ccitt(body)
    return bytes([STX]) + body + _CRC_STRUCT.pack(crc) + bytes([ETX])


def parse_frame(data: bytes):
    """Giai ma 1 frame nhan tu socket UDP (moi goi UDP = dung 1 frame).

    Tra ve dict {'type', 'seq', 'payload'} neu frame HOP LE (dung STX/ETX,
    dung do dai, CRC khop). Tra ve None neu frame hong o bat ky buoc kiem
    tra nao - ben goi PHAI bo qua frame None, khong duoc suy doan noi dung.
    """
    # Do dai toi thieu: STX+TYPE+SEQ+LEN(3) + CRC(2) + ETX(1) = 7 byte
    if len(data) < 7:
        return None
    if data[0] != STX or data[-1] != ETX:
        return None

    msg_type = data[1]
    seq = data[2]
    length = data[3]

    expected_len = 4 + length + 2 + 1  # header(4) + payload + crc(2) + etx(1)
    if len(data) != expected_len:
        return None

    payload = data[4:4 + length]
    received_crc = _CRC_STRUCT.unpack(data[4 + length:4 + length + 2])[0]
    body = data[1:4 + length]  # TYPE + SEQ + LEN + PAYLOAD
    if crc16_ccitt(body) != received_crc:
        return None

    return {"type": msg_type, "seq": seq, "payload": payload}


# ---------------------------------------------------------------------------
# SENSOR_DATA (Slave -> Master)
# ---------------------------------------------------------------------------
_SENSOR_PAYLOAD_STRUCT = struct.Struct(">Bhh")  # FLAGS, TEMP*10, HUMI*10


def encode_sensor_data(seq: int, temp, humi, temp_valid: bool, humi_valid: bool) -> bytes:
    flags = (FLAG_TEMP_VALID if temp_valid else 0) | (FLAG_HUMI_VALID if humi_valid else 0)
    temp_fixed = int(round(temp * 10)) if temp_valid and temp is not None else 0
    humi_fixed = int(round(humi * 10)) if humi_valid and humi is not None else 0
    payload = _SENSOR_PAYLOAD_STRUCT.pack(flags, temp_fixed, humi_fixed)
    return build_frame(TYPE_SENSOR_DATA, seq, payload)


def decode_sensor_data(payload: bytes):
    """Tra ve (temp, humi, temp_valid, humi_valid). temp/humi = None neu invalid."""
    if len(payload) != _SENSOR_PAYLOAD_STRUCT.size:
        return None, None, False, False
    flags, temp_fixed, humi_fixed = _SENSOR_PAYLOAD_STRUCT.unpack(payload)
    temp_valid = bool(flags & FLAG_TEMP_VALID)
    humi_valid = bool(flags & FLAG_HUMI_VALID)
    temp = (temp_fixed / 10.0) if temp_valid else None
    humi = (humi_fixed / 10.0) if humi_valid else None
    return temp, humi, temp_valid, humi_valid


# ---------------------------------------------------------------------------
# LED_CTRL (Master -> Slave)
# ---------------------------------------------------------------------------
def encode_led_ctrl(seq: int, red: bool, yellow: bool, green: bool) -> bytes:
    mask = (LED_BIT_RED if red else 0) | (LED_BIT_YELLOW if yellow else 0) | (LED_BIT_GREEN if green else 0)
    payload = bytes([mask])
    return build_frame(TYPE_LED_CTRL, seq, payload)


def decode_led_ctrl(payload: bytes):
    """Tra ve (red, yellow, green) dang bool."""
    if len(payload) != 1:
        return False, False, False
    mask = payload[0]
    return (bool(mask & LED_BIT_RED),
            bool(mask & LED_BIT_YELLOW),
            bool(mask & LED_BIT_GREEN))
