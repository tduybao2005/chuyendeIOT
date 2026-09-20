"""
LOGIC LED - phan THUAN TINH TOAN cua chuong trinh Pi.

Tach rieng khoi chuong_trinh_pi.py de test duoc tren may tinh: file nay
khong import gpiozero, khong import seeed_dht, khong goi mang. Chay
`pytest raspberry/tests` la kiem tra duoc toan bo luat bat den ma khong can
cam Pi vao dau ca.

Nguoc lai, phan cham GPIO va doc cam bien DHT thi nam het trong
chuong_trinh_pi.py va phai kiem tra bang tay tren phan cung that.

=========================================================================
LUAT BAT DEN
=========================================================================
Pi TU quyet dinh bat den theo nhiet do doc duoc (khong cho lenh tu server),
roi gui trang thai 3 den do len server cung voi nhiet do va do am.

    nhiet do < 28 C        ->  LED XANH   (mat)
    28 <= nhiet do < 32    ->  LED VANG   (am)
    nhiet do >= 32 C       ->  LED DO     (nong)

LUON CHI MOT DEN SANG: nhin bang den la doc duoc ngay muc nhiet, khong phai
giai ma to hop. Va khi demo thi ha hoi vao cam bien la thay den doi ngay -
chung minh duoc ca chuoi cam bien -> LED -> server -> doc nguoc ve.
"""

# Hai nguong chia ba muc. Dat quanh nhiet do phong o Viet Nam de khi ha hoi
# vao cam bien (hoi tho ~34 C, do am gan 100%) la den doi mau ngay - khong
# phai cho troi nong len moi thay duoc.
NGUONG_AM = 28.0    # tu day tro len: het mat, sang vang
NGUONG_NONG = 32.0  # tu day tro len: nong, sang do


def quyet_dinh_led(nhiet_do: float) -> tuple[int, int, int]:
    """Tu nhiet do ra trang thai 3 LED: (led1_do, led2_vang, led3_xanh).

    Dung dung nguong thi tinh la DA LEN muc tren (>= chu khong phai >). Neu
    dinh nghia mo ho o diem ranh gioi thi se co gia tri nhiet do ma khong
    LED nao sang, va loi do chi lo ra dung luc nhiet do roi vao so do - rat
    kho gap luc thu, rat de gap luc dang cham bai.
    """
    if nhiet_do >= NGUONG_NONG:
        return (1, 0, 0)
    if nhiet_do >= NGUONG_AM:
        return (0, 1, 0)
    return (0, 0, 1)


def mo_ta_muc_nhiet(nhiet_do: float) -> str:
    """Chu in kem ra terminal cho de doc, vi du 'NONG'."""
    if nhiet_do >= NGUONG_NONG:
        return "NONG"
    if nhiet_do >= NGUONG_AM:
        return "AM"
    return "MAT"
