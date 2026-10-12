"""
Buoi 11+12 - cua so trung binh dung chung cho 2 slave (copy file nay len ca 2 Pi).

Moi giay goi them() 1 lan voi 1 mau {ten_cam_bien: gia_tri hoac None}. Du
SO_MAU lan (20 lan = 20 giay) thi tra ve trung binh tung cam bien de gui 1
goi tin ve master - giong buoi 5 gom 20 giay roi moi gui ThingSpeak. Lan doc
loi (None) khong tinh vao trung binh; ca 20 lan deu loi thi ra None.
"""

SO_MAU = 20


class CuaSoTrungBinh:
    def __init__(self, so_mau=SO_MAU, chu_so=2):
        self.so_mau = so_mau
        self.chu_so = chu_so
        self._bat_dau_lai()

    def _bat_dau_lai(self):
        self._dem = 0
        self._tong = {}
        self._so_lan = {}

    def them(self, mau):
        self._dem += 1
        for ten, gia_tri in mau.items():
            self._tong.setdefault(ten, 0.0)
            self._so_lan.setdefault(ten, 0)
            if gia_tri is not None:
                self._tong[ten] += float(gia_tri)
                self._so_lan[ten] += 1
        if self._dem < self.so_mau:
            return None
        ket_qua = {
            ten: round(self._tong[ten] / self._so_lan[ten], self.chu_so) if self._so_lan[ten] else None
            for ten in self._tong
        }
        ket_qua["so_mau"] = self._dem
        self._bat_dau_lai()
        return ket_qua
