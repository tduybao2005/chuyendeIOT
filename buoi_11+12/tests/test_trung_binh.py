from trung_binh import SO_MAU, CuaSoTrungBinh


def test_mac_dinh_20_mau():
    assert SO_MAU == 20


def test_chua_du_20_mau_thi_chua_gui():
    cs = CuaSoTrungBinh()
    assert all(cs.them({"x": 1}) is None for _ in range(19))


def test_du_20_mau_tra_ve_trung_binh():
    cs = CuaSoTrungBinh()
    kq = [cs.them({"x": i, "y": 2}) for i in range(1, 21)]
    assert kq[-1] == {"x": 10.5, "y": 2.0, "so_mau": 20}


def test_bo_qua_lan_doc_loi():
    cs = CuaSoTrungBinh()
    for i in range(20):
        kq = cs.them({"x": None if i < 10 else 4})
    assert kq["x"] == 4.0


def test_ca_20_lan_loi_thi_none():
    cs = CuaSoTrungBinh()
    for _ in range(20):
        kq = cs.them({"x": None})
    assert kq == {"x": None, "so_mau": 20}


def test_cua_so_moi_khong_lan_du_lieu_cu():
    cs = CuaSoTrungBinh()
    for _ in range(20):
        cs.them({"x": 100})
    assert cs.them({"x": 1}) is None
    for _ in range(19):
        kq = cs.them({"x": 1})
    assert kq == {"x": 1.0, "so_mau": 20}


def test_lam_tron_2_chu_so():
    cs = CuaSoTrungBinh(so_mau=3)
    cs.them({"x": 1})
    cs.them({"x": 1})
    assert cs.them({"x": 2}) == {"x": 1.33, "so_mau": 3}
