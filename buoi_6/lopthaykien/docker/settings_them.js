// ===========================================================================
// KHOI NAY DUOC NOI THEM VAO CUOI ~/iot_buoi6/node-red-data/settings.js
// ===========================================================================
// VAN DE: Node-RED khoi dong chi in
//     "Server now running at http://127.0.0.1:1880/"
// 127.0.0.1 la dia chi BEN TRONG container. Mo tren laptop khong vao duoc -
// nguoi doc log de bi dan di sai duong.
//
// settings.js la mot module JS thong thuong: code o cap cao nhat CHAY NGAY khi
// Node-RED nap file, tuc la truoc ca khi server len. Nho vay chi can console.log
// o day la dong URL that hien trong "docker compose logs".
//
// IP that duoc truyen vao qua bien moi truong HOST_IP_* (khai trong
// docker-compose.yml, do chay.sh do duoc). Neu chay "docker compose up -d"
// thang thi 2 bien rong -> bo qua, khong bao loi.
//
// CACH NOI THEM (da lam san tren Pi, chay lai khong sao vi co kiem tra dau):
//     cd ~/iot_buoi6
//     grep -q "IOT_BUOI6_URL" node-red-data/settings.js \
//       || cat docker/settings_them.js >> node-red-data/settings.js
//     docker restart iot_buoi6_web
// ===========================================================================

// IOT_BUOI6_URL - dau nhan dien de khong noi them hai lan
//
// DAU CHAM PHAY MO DAU LA BAT BUOC, KHONG DUOC BO:
// settings.js goc ket thuc bang "}" cua module.exports = { ... } va KHONG co
// dau cham phay. Neu khoi nay bat dau thang bang "(" thi JavaScript ghep hai
// thu lai thanh mot LOI GOI HAM tren object:  module.exports = {...}(...)
// -> Node-RED chet ngay khi khoi dong voi loi
//    "TypeError: {(intermediate value)...} is not a function"
// va container roi vao vong restarting (unhealthy). Da gap dung loi nay.
;(function inUrlThat() {
    const cong = 1880;
    const ts = process.env.HOST_IP_TAILSCALE || '';
    const lan = process.env.HOST_IP_LAN || '';
    if (!ts && !lan) return;   // chay truc tiep khong qua chay.sh

    const dong = ['', '='.repeat(64), '  CT1 - GIAO DIEN WEB  ·  mo mot trong cac dia chi sau:'];
    if (ts) dong.push(`    Tailscale (moi mang)  ->  http://${ts}:${cong}/ui`);
    if (lan) dong.push(`    LAN (cung Wi-Fi)      ->  http://${lan}:${cong}/ui`);
    if (ts) dong.push(`    Editor sua flow       ->  http://${ts}:${cong}`);
    dong.push('  (dong "Server now running at http://127.0.0.1:1880" ben duoi la');
    dong.push('   dia chi BEN TRONG container - khong mo duoc tu may khac)');
    dong.push('='.repeat(64), '');
    console.log(dong.join('\n'));
})();
