"""
LOGIC LED - den sang DUOI.

Tach rieng khoi chuong_trinh_pi.py de test duoc tren may tinh: file nay
khong import gpiozero, khong import seeed_dht, khong goi mang. Chay
`pytest raspberry/tests` la kiem tra duoc toan bo luat sang duoi ma khong
can cam Pi vao dau ca.

=========================================================================
LUAT SANG DUOI
=========================================================================
Ba den sang duoi nhau, moi 1 giay chuyen sang den ke tiep, vong tron:

    buoc 0   ->  [DO]  vang  xanh        (1, 0, 0)
    buoc 1   ->   do  [VANG] xanh        (0, 1, 0)
    buoc 2   ->   do   vang [XANH]       (0, 0, 1)
    buoc 3   ->  [DO]  vang  xanh        quay lai tu dau
    ...

LUON CHI MOT DEN SANG. Neu co luc hai den cung sang, hoac khong den nao
sang, thi khong con la "duoi" nua - nhin vao khong biet diem sang dang o
dau. Co test rieng khang dinh dieu nay cho 12 buoc lien tiep.

Trang thai ba den nay duoc DAY LEN SERVER cung nhiet do va do am; terminal
thi in lai gia tri DOC VE TU SERVER, khong in bien cuc bo (xem giai thich
day du trong giao_tiep.py).
"""

# So den trong day duoi. Doi so nay thi ca vong duoi tu dai ra, nhung con
# phai them chan GPIO trong cau_hinh_pi.py va them truong ledN ben server -
# khong phai sua mot cho la xong.
SO_DEN = 3

# Ten tung den, theo dung thu tu (led1, led2, led3) = (D16, D22, D24).
TEN_DEN = ("DO", "VANG", "XANH")


def den_dang_sang(buoc: int) -> tuple[int, ...]:
    """Tu so buoc ra trang thai 3 den: (led1_do, led2_vang, led3_xanh).

    Dung phep chia lay du (%) de vong lai tu dau thay vi dem roi tu dat ve
    0: khong can bien nho trang thai, va so buoc cua chuong trinh chinh co
    tang den bao nhieu cung khong tran.
    """
    vi_tri = buoc % SO_DEN
    return tuple(1 if i == vi_tri else 0 for i in range(SO_DEN))


def mo_ta_den(trang_thai) -> str:
    """Chu in kem ra terminal, vi du 'VANG'.

    Chiu duoc moi to hop chu khong chi ba to hop cua vong duoi: ham nay con
    dung de in ban ghi DOC VE TU SERVER, ma du lieu tren server co the do
    chuong trinh khac gui len voi to hop bat ky (ca 3 den cung sang, hay
    khong den nao sang).
    """
    dang_sang = [TEN_DEN[i] for i, bat in enumerate(trang_thai) if bat]
    return "+".join(dang_sang) if dang_sang else "TAT"
