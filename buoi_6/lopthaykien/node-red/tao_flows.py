#!/usr/bin/env python3
"""
Sinh file flows.json cua Node-RED tu dashboard_template.html.

VI SAO CAN SCRIPT NAY: noi dung node ui_template la mot chuoi HTML dai 800+
dong nam trong JSON. Neu sua truc tiep trong flows.json thi moi dau nhay, moi
xuong dong deu phai escape - khong the doc hay diff duoc tren GitHub. Tach ra:
sua HTML trong dashboard_template.html cho de nhin, roi chay script nay de
dung lai flows.json.

    python3 tao_flows.py

Sau do nap flows.json vao Node-RED (xem README.md cung thu muc).
"""

import json
import os

THU_MUC = os.path.dirname(os.path.abspath(__file__))

# ===========================================================================
# CAC HANG SO DUNG CHUNG GIUA CAC NODE
# ===========================================================================
KHOA_SAU_KHI_GHI_MS = 15000  # Sau moi lan ghi THANH CONG, khoa ca 8 nut dung
                             # 15 giay - vua khop gioi han ghi cua ThingSpeak,
                             # vua la quy tac nguoi dung yeu cau: moi lan chi
                             # bam duoc 1 nut.
KHOA_SAU_KHI_HONG_MS = 5000  # Ghi hong (ThingSpeak tu choi) thi cho 5 giay roi
                             # cho bam lai - bam lai ngay thi cung bi tu choi.
SO_BAN_GHI_CAM_BIEN = 30     # ve do thi ~10 phut (CT2 ghi moi 20s)
SO_BAN_GHI_LENH = 10         # du de quet nguoc tim gia tri moi nhat tung field


def doc_html():
    with open(os.path.join(THU_MUC, "dashboard_template.html"), encoding="utf-8") as f:
        return f.read()


# ===========================================================================
# MA NGUON CAC NODE FUNCTION
# ===========================================================================

MA_CAU_HINH = r"""
// Node nay KHONG can noi day vao dau ca. Toan bo ma nam o tab "On Start"
// (Setup) nen Node-RED chay no NGAY KHI khoi dong flow, truoc moi message.
// Nho vay cac node khac luon doc duoc cau hinh, khong bi dua nhau luc dau.
return msg;
"""

MA_CAU_HINH_KHOI_DONG = r"""
// ===========================================================================
// DIEN THONG TIN THINGSPEAK CUA BAN VAO DAY  -  DUY NHAT MOT CHO
// ===========================================================================
// Phai khop voi raspberry/cau_hinh.py ben Raspberry Pi.
flow.set('cauHinh', {

    // --- Channel A: CAM BIEN (CT2 ghi, Web doc de ve do thi) ---
    camBienId:       '',      // vi du '3486158'
    camBienReadKey:  '',      // de trong neu channel de che do Public

    // --- Channel B: LENH (Web ghi, CT3/CT4/CT5 doc) ---
    lenhId:          '',      // vi du '3486161'
    lenhReadKey:     '',
    lenhWriteKey:    '',      // BAT BUOC - Web dung key nay de ghi lenh

    // --- Khong can sua ---
    soBanGhiCamBien:  %(SO_BAN_GHI_CAM_BIEN)d,
    soBanGhiLenh:     %(SO_BAN_GHI_LENH)d,

    // Khoa 8 nut bao lau sau moi lan ghi. Phai khop voi KHOA_NUT_SAU_KHI_GHI
    // trong raspberry/cau_hinh.py.
    khoaSauKhiGhiMs:  %(KHOA_SAU_KHI_GHI_MS)d,
    khoaSauKhiHongMs: %(KHOA_SAU_KHI_HONG_MS)d
});
node.warn('Da nap cau hinh ThingSpeak cho flow buoi 6');
""" % {
    "SO_BAN_GHI_CAM_BIEN": SO_BAN_GHI_CAM_BIEN,
    "SO_BAN_GHI_LENH": SO_BAN_GHI_LENH,
    "KHOA_SAU_KHI_GHI_MS": KHOA_SAU_KHI_GHI_MS,
    "KHOA_SAU_KHI_HONG_MS": KHOA_SAU_KHI_HONG_MS,
}

MA_URL_CAM_BIEN = r"""
// Dung URL doc channel CAM BIEN.
// Node "http request" phia sau lay dia chi tu msg.url.
const c = flow.get('cauHinh') || {};
if (!c.camBienId) {
    node.error('Chua dien camBienId trong node CAU HINH THINGSPEAK');
    return null;
}
let url = `https://api.thingspeak.com/channels/${c.camBienId}/feeds.json`
        + `?results=${c.soBanGhiCamBien}`;
// Channel de Public thi khong can api_key; de Private thi bat buoc.
if (c.camBienReadKey) url += `&api_key=${c.camBienReadKey}`;
msg.url = url;
return msg;
"""

MA_PHAN_TICH_CAM_BIEN = r"""
// Doi ban ghi tho cua ThingSpeak thanh du lieu ve do thi.
//
//   field1 = nhiet do trung binh 20s   (CT2 ghi)
//   field2 = do am   trung binh 20s    (CT2 ghi)
//
// Ban ghi nao thieu field thi giu null - ham ve do thi ben dashboard tu bo
// qua diem null thay vi ve tut xuong 0 (se lam do thi gay hinh rang cua).
if (msg.statusCode !== 200) {
    msg.payload = { loai: 'du_lieu_cam_bien', ok: false, lichSu: [], moiNhat: null };
    return msg;
}

const feeds = (msg.payload && msg.payload.feeds) || [];

const soHoacNull = (v) => (v === null || v === undefined || v === '') ? null : Number(v);

const lichSu = feeds.map(f => ({
    nhietDo:  soHoacNull(f.field1),
    doAm:     soHoacNull(f.field2),
    thoiGian: f.created_at
}));

// Ban ghi moi nhat CO gia tri - quet nguoc vi ban ghi cuoi co the thieu field.
let moiNhat = { nhietDo: null, doAm: null, thoiGian: null, mocIso: null };
for (let i = lichSu.length - 1; i >= 0; i--) {
    if (moiNhat.nhietDo === null && lichSu[i].nhietDo !== null) {
        moiNhat.nhietDo = lichSu[i].nhietDo;
        moiNhat.thoiGian = new Date(lichSu[i].thoiGian).toLocaleTimeString('vi-VN', { hour12: false });
        // Gui kem moc ISO THO de giao dien tu tinh duoc so lieu da cu bao lau.
        // Chi co chuoi "14:59:19" thi khong biet no cua hom nay hay hom qua.
        moiNhat.mocIso = lichSu[i].thoiGian;
    }
    if (moiNhat.doAm === null && lichSu[i].doAm !== null) moiNhat.doAm = lichSu[i].doAm;
    if (moiNhat.nhietDo !== null && moiNhat.doAm !== null) break;
}

msg.payload = { loai: 'du_lieu_cam_bien', ok: true, lichSu, moiNhat };
return msg;
"""

MA_URL_LENH = r"""
// Dung URL doc channel LENH (de dong bo giao dien voi gia tri that tren server).
const c = flow.get('cauHinh') || {};
if (!c.lenhId) {
    node.error('Chua dien lenhId trong node CAU HINH THINGSPEAK');
    return null;
}
let url = `https://api.thingspeak.com/channels/${c.lenhId}/feeds.json`
        + `?results=${c.soBanGhiLenh}`;
if (c.lenhReadKey) url += `&api_key=${c.lenhReadKey}`;
msg.url = url;
return msg;
"""

MA_PHAN_TICH_LENH = r"""
// Lay gia tri MOI NHAT cua tung field tren channel LENH.
//
// VI SAO PHAI QUET NGUOC TUNG FIELD thay vi lay ban ghi cuoi:
// moi lan ghi, ThingSpeak tao mot dong moi va dat null cho cac field khong
// duoc gui trong lan do. Neu ai do (vd curl) ghi le mot field thi dong cuoi
// se co 5 o null - nhin moi dong cuoi se tuong 5 field kia da bi xoa.
if (msg.statusCode !== 200) {
    msg.payload = { loai: 'trang_thai_server', ok: false, giaTri: null };
    return msg;
}

const feeds = (msg.payload && msg.payload.feeds) || [];

// Ten dung trong giao dien -> so field tren channel LENH
const BAN_DO = { led1: 'field1', led2: 'field2', led3: 'field3',
                 relay: 'field4', text: 'field5', lich: 'field6' };

const giaTri = {};
for (const ten of Object.keys(BAN_DO)) giaTri[ten] = null;

for (let i = feeds.length - 1; i >= 0; i--) {     // moi -> cu
    for (const [ten, field] of Object.entries(BAN_DO)) {
        if (giaTri[ten] !== null) continue;
        const v = feeds[i][field];
        if (v !== null && v !== undefined && v !== '') giaTri[ten] = v;
    }
    if (Object.values(giaTri).every(v => v !== null)) break;
}

msg.payload = { loai: 'trang_thai_server', ok: true, giaTri };
return msg;
"""

MA_DIEU_PHOI_GHI = r"""
// ===========================================================================
// DIEU PHOI GHI LENH LEN THINGSPEAK  -  MOI LAN MOT NUT, KHOA 15 GIAY
// ===========================================================================
// HAI RANG BUOC PHAI DAP UNG CUNG LUC:
//
//   (1) Nguoi dung chi duoc bam 1 nut, roi phai cho 15 giay moi bam nut tiep.
//   (2) Tu luc BAM NUT den luc Pi bat den phai DUOI 2 GIAY.
//
// Hai cai nay do hai quang KHAC NHAU nen khong he mau thuan:
//
//     bam ─┬────────────── duoi 2 giay ──────────────┐
//          │  POST ~0.5s   ThingSpeak   CT3 poll 0.5s│
//          └─────────────────────────────────────────┘
//          └────────────── khoa 15 giay ─────────────────────┤ moi bam tiep
//
// VI SAO KHONG CAN HANG DOI: channel LENH chi co Web ghi, ma Web tu khoa 15
// giay giua 2 lan ghi, nen khong bao gio cham gioi han cua ThingSpeak ->
// khong bi tu choi -> khong can xep hang, khong can thu lai.
//
// VI SAO PHAI BAN POST NGAY (khong cho nhip tick): neu de nhip tick 1 giay
// bat len roi moi gui thi mat oan toi 1 giay trong ngan sach 2 giay. Nhip
// tick o day CHI de cap nhat dong ho dem nguoc tren giao dien.
//
// Ba loai message di vao, phan biet bang msg.topic:
//   'lenh'    tu dashboard   - nguoi dung vua bam nut
//   'ket_qua' tu node kiem tra ket qua HTTP
//   'tick'    tu inject 1s   - chi de dem nguoc
//
// Hai duong ra:
//   [0] -> node "http request" POST update.json
//   [1] -> dashboard (khoa/mo nut, dem nguoc, ket qua ghi)
// ===========================================================================

const c = flow.get('cauHinh') || {};
const KHOA_OK   = c.khoaSauKhiGhiMs  || 15000;
const KHOA_HONG = c.khoaSauKhiHongMs || 5000;

let dangGui  = flow.get('dangGui')  || null;   // lenh dang bay tren mang
let moKhoaLuc = flow.get('moKhoaLuc') || 0;    // moc ms duoc phep gui tiep

const bayGio = Date.now();
const gioMs  = (t) => new Date(t).toLocaleTimeString('vi-VN', { hour12: false })
                    + '.' + String(new Date(t).getMilliseconds()).padStart(3, '0');

function conLai() { return Math.max(0, Math.ceil((moKhoaLuc - bayGio) / 1000)); }
function baoKhoa(ghiChu) {
    return { payload: { loai: 'khoa',
                        dangKhoa: !!dangGui || conLai() > 0,
                        dangGui: !!dangGui,
                        conLai: conLai(),
                        ghiChu: ghiChu || '' } };
}

// ------------------------------- ghi chu tu giao dien (KHONG phai lenh gui di)
// Dashboard bao sang moi khi nguoi dung BAM MA KHONG GUI DUOC (dang khoa, hoac
// noi dung khong khac server). Khong co nhanh nay thi khi nguoi dung keu "bam
// khong an", log phia server trong tron - khong phan biet duoc "ho chua he bam"
// voi "ho co bam nhung bi chan". Da mat mot luc lau moi truy ra dung chuyen do.
if (msg.topic === 'ghi_chu') {
    node.warn(`GIAO DIEN luc ${gioMs(bayGio)}: ${msg.payload.moTa}`);
    return [null, null];
}

// --------------------------------------------------- nguoi dung vua bam nut
if (msg.topic === 'lenh') {
    // Giao dien KHONG con disable nut nua (nut disabled thi bam vao trinh duyet
    // khong sinh su kien, khong biet nguoi dung da bam hay chua). No tu chan va
    // bao ly do. Hai dieu kien duoi day la chot chan cuoi - phong khi mo 2
    // trinh duyet cung luc.
    if (dangGui) {
        return [null, baoKhoa('Lenh truoc chua co ket qua, cho mot chut')];
    }
    if (conLai() > 0) {
        return [null, baoKhoa(`Con ${conLai()}s nua moi duoc gui lenh tiep`)];
    }
    if (!c.lenhWriteKey) {
        node.error('Chua dien lenhWriteKey trong node CAU HINH THINGSPEAK');
        return [null, { payload: { loai: 'ket_qua_ghi', ok: false,
                                   thongBao: 'Chua dien Write API key cua channel LENH' } }];
    }

    dangGui = Object.assign({}, msg.payload, { tNhan: bayGio });
    flow.set('dangGui', dangGui);

    // MOC THOI GIAN DAU de do do tre that. Doi chieu voi moc "DA AP DUNG XONG"
    // trong ~/iot_buoi6/logs/ct3_led.log - ca hai cung dong ho cua Pi.
    node.warn(`NHAN LENH TU WEB luc ${gioMs(bayGio)} | ${msg.payload.moTa || ''}`);

    // Ban POST di NGAY trong chinh message nay, khong cho nhip nao ca.
    return [{
        url: 'https://api.thingspeak.com/update.json',
        payload: {
            api_key: c.lenhWriteKey,
            field1: msg.payload.led1,
            field2: msg.payload.led2,
            field3: msg.payload.led3,
            field4: msg.payload.relay,
            field5: msg.payload.text,
            field6: msg.payload.lich
        }
    }, baoKhoa('Dang gui len ThingSpeak...')];
}

// ------------------------------------------------------------ ket qua ghi ve
if (msg.topic === 'ket_qua') {
    const kq = msg.payload;
    const moTa = dangGui ? (dangGui.moTa || '') : '';
    const doTreGhi = dangGui ? (bayGio - dangGui.tNhan) : null;

    if (kq.ok) {
        moKhoaLuc = bayGio + KHOA_OK;
        node.warn(`GHI THANH CONG luc ${gioMs(bayGio)} | entry_id=${kq.entryId} `
                + `| POST mat ${doTreGhi}ms | khoa nut ${KHOA_OK / 1000}s`);
    } else {
        // Bam lai NGAY cung se bi tu choi tiep (ThingSpeak van dang trong cua
        // so 15 giay), nen cho 5 giay roi moi mo nut - do la khoang du de lan
        // sau gan nhu chac chan qua duoc.
        moKhoaLuc = bayGio + KHOA_HONG;
        node.warn(`GHI THAT BAI luc ${gioMs(bayGio)} | ${kq.thongBao} `
                + `| cho ${KHOA_HONG / 1000}s roi cho bam lai`);
    }

    dangGui = null;
    flow.set('dangGui', null);
    flow.set('moKhoaLuc', moKhoaLuc);

    return [null, { payload: Object.assign({ loai: 'ket_qua_ghi', moTa,
                                             doTreGhi, conLai: conLai() }, kq) }];
}

// ------------------------------------- nhip tick: chi cap nhat dong ho dem nguoc
return [null, baoKhoa()];
"""


MA_KIEM_TRA_GHI = r"""
// ===========================================================================
// KIEM TRA KET QUA GHI
// ===========================================================================
// BAY: khi tu choi vi chua du 15 giay, ThingSpeak KHONG tra loi HTTP - no tra
// ve 200 OK kem noi dung la so 0 (hoac {"entry_id":0}). Chi nhin statusCode
// se tuong da ghi thanh cong trong khi thuc te lenh roi mat.
let ok = false, entryId = 0, thongBao = '';

if (msg.statusCode === 200) {
    const p = msg.payload;
    if (p && typeof p === 'object' && Number(p.entry_id) > 0) {
        ok = true;
        entryId = p.entry_id;
    } else {
        thongBao = 'ThingSpeak tu choi (chua du ~15 giay ke tu lan ghi truoc)';
    }
} else {
    thongBao = `Loi HTTP ${msg.statusCode || '(khong ket noi duoc)'}`;
}

msg.topic = 'ket_qua';
msg.payload = { ok, entryId, thongBao };
return msg;
"""


# ===========================================================================
# DUNG DANH SACH NODE
# ===========================================================================
def node_function(id_, ten, ma, x, y, day_ra, so_duong_ra=1, ma_khoi_dong="", nhom=None):
    n = {
        "id": id_, "type": "function", "z": "b6k_flow", "name": ten,
        "func": ma.strip() + "\n",
        "outputs": so_duong_ra,
        "timeout": 0, "noerr": 0,
        "initialize": ma_khoi_dong.strip() + "\n" if ma_khoi_dong else "",
        "finalize": "", "libs": [],
        "x": x, "y": y, "wires": day_ra,
    }
    if nhom:
        n["g"] = nhom
    return n


def xay_dung():
    html = doc_html()

    nodes = [
        # ------------------------------------------------------------ tab
        {"id": "b6k_flow", "type": "tab", "label": "Buoi 6 - muc 15 diem",
         "disabled": False,
         "info": "Chuong trinh 1: giao dien Web dieu khien 3 LED + relay (co hen gio)\n"
                 "+ gui text 16x2 len LCD, doc nhiet do/do am tu ThingSpeak.\n\n"
                 "Dien API key tai node 'CAU HINH THINGSPEAK' (tab Setup/On Start).",
         "env": []},

        # ------------------------------------------------------------ khung nhom
        {"id": "b6k_g0", "type": "group", "z": "b6k_flow", "name": "0 · CAU HINH (dien API key o day)",
         "style": {"label": True, "color": "#ffffff", "fill": "#3f3f6b"},
         "nodes": ["b6k_cauhinh"], "x": 54, "y": 39, "w": 332, "h": 82},

        {"id": "b6k_g1", "type": "group", "z": "b6k_flow", "name": "1 · DOC CAM BIEN (channel A, moi 20s)",
         "style": {"label": True, "color": "#ffffff", "fill": "#255d3a"},
         "nodes": ["b6k_tick_cambien", "b6k_url_cambien", "b6k_get_cambien", "b6k_parse_cambien"],
         "x": 54, "y": 159, "w": 752, "h": 82},

        {"id": "b6k_g2", "type": "group", "z": "b6k_flow", "name": "2 · DOC TRANG THAI LENH (channel B, moi 5s)",
         "style": {"label": True, "color": "#ffffff", "fill": "#1f4d6b"},
         "nodes": ["b6k_tick_lenh", "b6k_url_lenh", "b6k_get_lenh", "b6k_parse_lenh"],
         "x": 54, "y": 259, "w": 752, "h": 82},

        {"id": "b6k_g3", "type": "group", "z": "b6k_flow", "name": "3 · GIAO DIEN WEB (Chuong trinh 1)",
         "style": {"label": True, "color": "#ffffff", "fill": "#6b4a1f"},
         "nodes": ["b6k_dashboard"], "x": 854, "y": 199, "w": 292, "h": 82},

        {"id": "b6k_g4", "type": "group", "z": "b6k_flow", "name": "4 · GHI LENH LEN SERVER (moi lan 1 nut, khoa 15s)",
         "style": {"label": True, "color": "#ffffff", "fill": "#6b1f3f"},
         "nodes": ["b6k_tick_ghi", "b6k_dieuphoi", "b6k_post_lenh", "b6k_kiemtra"],
         "x": 54, "y": 379, "w": 752, "h": 122},

        # ------------------------------------------------------------ 0. cau hinh
        node_function("b6k_cauhinh", "CAU HINH THINGSPEAK", MA_CAU_HINH,
                      200, 80, [[]], 1, MA_CAU_HINH_KHOI_DONG, nhom="b6k_g0"),

        # ------------------------------------------------------------ 1. doc cam bien
        {"id": "b6k_tick_cambien", "type": "inject", "z": "b6k_flow", "g": "b6k_g1",
         "name": "moi 20s", "props": [{"p": "payload"}],
         "repeat": "20", "crontab": "", "once": True, "onceDelay": "2",
         "topic": "", "payload": "", "payloadType": "date",
         "x": 140, "y": 200, "wires": [["b6k_url_cambien"]]},

        node_function("b6k_url_cambien", "dung URL", MA_URL_CAM_BIEN,
                      300, 200, [["b6k_get_cambien"]], nhom="b6k_g1"),

        {"id": "b6k_get_cambien", "type": "http request", "z": "b6k_flow", "g": "b6k_g1",
         "name": "GET feeds.json", "method": "GET", "ret": "obj", "paytoqs": "ignore",
         "url": "", "tls": "", "persist": False, "proxy": "", "insecureHTTPParser": False,
         "authType": "", "senderr": True, "headers": [],
         "x": 480, "y": 200, "wires": [["b6k_parse_cambien"]]},

        node_function("b6k_parse_cambien", "phan tich -> do thi", MA_PHAN_TICH_CAM_BIEN,
                      680, 200, [["b6k_dashboard"]], nhom="b6k_g1"),

        # ------------------------------------------------------------ 2. doc lenh
        {"id": "b6k_tick_lenh", "type": "inject", "z": "b6k_flow", "g": "b6k_g2",
         "name": "moi 5s", "props": [{"p": "payload"}],
         "repeat": "5", "crontab": "", "once": True, "onceDelay": "3",
         "topic": "", "payload": "", "payloadType": "date",
         "x": 140, "y": 300, "wires": [["b6k_url_lenh"]]},

        node_function("b6k_url_lenh", "dung URL", MA_URL_LENH,
                      300, 300, [["b6k_get_lenh"]], nhom="b6k_g2"),

        {"id": "b6k_get_lenh", "type": "http request", "z": "b6k_flow", "g": "b6k_g2",
         "name": "GET feeds.json", "method": "GET", "ret": "obj", "paytoqs": "ignore",
         "url": "", "tls": "", "persist": False, "proxy": "", "insecureHTTPParser": False,
         "authType": "", "senderr": True, "headers": [],
         "x": 480, "y": 300, "wires": [["b6k_parse_lenh"]]},

        node_function("b6k_parse_lenh", "lay gia tri moi nhat", MA_PHAN_TICH_LENH,
                      680, 300, [["b6k_dashboard"]], nhom="b6k_g2"),

        # ------------------------------------------------------------ 3. dashboard
        {"id": "b6k_dashboard", "type": "ui_template", "z": "b6k_flow", "g": "b6k_g3",
         "group": "b6k_ui_group", "name": "Giao dien dieu khien", "order": 1,
         "width": "0", "height": "0", "format": html,
         "storeOutMessages": True, "fwdInMessages": False, "resendOnRefresh": True,
         "templateScope": "local", "className": "",
         "x": 1000, "y": 240, "wires": [["b6k_dieuphoi"]]},

        # ------------------------------------------------------------ 4. ghi lenh
        {"id": "b6k_tick_ghi", "type": "inject", "z": "b6k_flow", "g": "b6k_g4",
         "name": "nhip 1s (dem nguoc)", "props": [{"p": "topic", "v": "tick", "vt": "str"}],
         "repeat": "1", "crontab": "", "once": True, "onceDelay": "4",
         "topic": "tick", "payload": "", "payloadType": "date",
         "x": 140, "y": 460, "wires": [["b6k_dieuphoi"]]},

        node_function("b6k_dieuphoi", "DIEU PHOI GHI (khoa 15s/lenh)", MA_DIEU_PHOI_GHI,
                      340, 420, [["b6k_post_lenh"], ["b6k_dashboard"]], 2, nhom="b6k_g4"),

        {"id": "b6k_post_lenh", "type": "http request", "z": "b6k_flow", "g": "b6k_g4",
         "name": "POST update.json", "method": "POST", "ret": "obj", "paytoqs": "ignore",
         "url": "", "tls": "", "persist": False, "proxy": "", "insecureHTTPParser": False,
         "authType": "", "senderr": True,
         "headers": [{"keyType": "other", "keyValue": "Content-Type",
                      "valueType": "other", "valueValue": "application/json"}],
         "x": 560, "y": 420, "wires": [["b6k_kiemtra"]]},

        node_function("b6k_kiemtra", "kiem tra ket qua", MA_KIEM_TRA_GHI,
                      740, 420, [["b6k_dieuphoi"]], nhom="b6k_g4"),

        # ------------------------------------------------------------ cau hinh dashboard
        {"id": "b6k_ui_base", "type": "ui_base",
         "theme": {
             "name": "theme-dark",
             "lightTheme": {"default": "#0094CE", "baseColor": "#0094CE",
                            "baseFont": "-apple-system,Helvetica Neue,Helvetica,Arial",
                            "edited": False, "reset": False},
             "darkTheme": {"default": "#22d3ee", "baseColor": "#22d3ee",
                           "baseFont": "-apple-system,Helvetica Neue,Helvetica,Arial",
                           "edited": True},
             "customTheme": {"name": "Untitled Theme 1", "default": "#4B7930",
                             "baseColor": "#4B7930",
                             "baseFont": "-apple-system,Helvetica Neue,Helvetica,Arial"},
             "themeState": {
                 "base-color": {"value": "#22d3ee", "edited": True},
                 "page-titlebar-backgroundColor": {"value": "#0c1424", "edited": True},
                 "page-backgroundColor": {"value": "#080c17", "edited": True},
                 "page-sidebar-backgroundColor": {"value": "#101827", "edited": True},
                 "group-textColor": {"value": "#e8eef9", "edited": True},
                 "group-borderColor": {"value": "#1f2c45", "edited": True},
                 "group-backgroundColor": {"value": "#101827", "edited": True},
                 "widget-textColor": {"value": "#e8eef9", "edited": True},
                 "widget-backgroundColor": {"value": "#22d3ee", "edited": True},
                 "widget-borderColor": {"value": "#1f2c45", "edited": True},
                 "base-font": {"value": "-apple-system,Helvetica Neue,Helvetica,Arial"}
             },
             "angularTheme": {"primary": "indigo", "accents": "blue",
                              "warn": "red", "background": "grey", "palette": "dark"}
         },
         "site": {"name": "IoT Buoi 6 - Muc 15 diem", "hideToolbar": "true",
                  "allowSwipe": "false", "lockMenu": "true", "allowTempTheme": "false",
                  "dateFormat": "DD/MM/YYYY",
                  "sizes": {"sx": 48, "sy": 48, "gx": 6, "gy": 6,
                            "cx": 6, "cy": 6, "px": 0, "py": 0}}},

        {"id": "b6k_ui_tab", "type": "ui_tab", "name": "Dieu khien",
         "icon": "dashboard", "disabled": False, "hidden": False},

        {"id": "b6k_ui_group", "type": "ui_group", "name": "Bang dieu khien",
         "tab": "b6k_ui_tab", "order": 1, "disp": False, "width": "6", "collapse": False},
    ]
    return nodes


if __name__ == "__main__":
    danh_sach = xay_dung()
    duong_dan = os.path.join(THU_MUC, "flows.json")
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(danh_sach, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Da tao {duong_dan} ({len(danh_sach)} node)")
