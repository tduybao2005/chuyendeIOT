/**
 * Cau hinh ket noi ThingSpeak - HAY DIEN THONG TIN THAT CUA BAN VAO DAY
 * truoc khi chay ung dung (giong nhu cach an API key trong code Raspberry).
 *
 * LUU Y: du an nay dung 2 CHANNEL RIENG (giong quy uoc da dung o buoi_4) vi
 * thiet bi MQTT chi duoc cap quyen subscribe tren 1 channel rieng, khac voi
 * channel dung cho HTTP:
 *   - THINGSPEAK_CHANNEL_ID (kenh HTTP): doc/ghi field1-4 (cam bien) va
 *     field5-7 (lenh LED/Buzzer/Relay, BAT BUOC gui bang HTTP).
 *   - MQTT_CHANNEL_ID (kenh MQTT): channel nay CHI CO 1 field duy nhat ten
 *     "Mode" va no la field1 CUA CHINH KENH NAY (khac voi field1 = nhiet do
 *     cua kenh HTTP) - dung de publish/subscribe che do Auto/Manual, BAT
 *     BUOC gui bang MQTT.
 */

export const THINGSPEAK_CHANNEL_ID = 'DIEN_CHANNEL_ID_HTTP_CUA_BAN';
export const THINGSPEAK_READ_API_KEY = 'DIEN_READ_API_KEY_CUA_BAN';
export const THINGSPEAK_WRITE_API_KEY = 'DIEN_WRITE_API_KEY_CUA_BAN';

export const THINGSPEAK_HTTP_BASE = 'https://api.thingspeak.com';

// MQTT qua WebSocket (bat buoc de nut chon che do Auto/Manual dung MQTT tu
// trinh duyet). ThingSpeak ho tro WebSocket tai port 443 (wss, co TLS) hoac
// 80 (ws, khong TLS), voi duong dan co dinh la "/mqtt".
export const MQTT_HOST = 'mqtt3.thingspeak.com';
export const MQTT_WSS_PORT = 443;
export const MQTT_CHANNEL_ID = 'DIEN_CHANNEL_ID_MQTT_CUA_BAN';
// Dung de doc du phong che do qua HTTP (xem hooks/useMqttMode.ts) - phong khi
// MQTT bi mat goi tin do Web/Pi phai dung chung 1 client_id (ThingSpeak yeu
// cau client_id trung username).
export const MQTT_CHANNEL_READ_API_KEY = 'DIEN_READ_API_KEY_CUA_KENH_MQTT_CUA_BAN';
export const MQTT_CLIENT_ID = 'DIEN_MQTT_CLIENT_ID_CUA_BAN';
export const MQTT_USERNAME = 'DIEN_MQTT_USERNAME_CUA_BAN';
export const MQTT_PASSWORD = 'DIEN_MQTT_PASSWORD_CUA_BAN'; // MQTT API Key

// Kenh HTTP: field1..field4 Pi ghi (trung binh cam bien moi 20s), field5..7
// Web ghi (lenh dieu khien, BAT BUOC qua HTTP) - dat ten LED/Buzzer/Relay
// dung theo thu tu field da cau hinh tren channel ThingSpeak.
export const FIELD = {
  temp: 'field1',
  humi: 'field2',
  voltage: 'field3',
  distance: 'field4',
  led: 'field5',
  buzzer: 'field6',
  relay: 'field7',
} as const;

// Kenh MQTT (channel rieng, chi co 1 field ten "Mode" = field1 CUA KENH NAY)
export const MQTT_MODE_FIELD = 'field1';

export const HISTORY_RESULTS = 30; // so ban ghi gan nhat lay ve de ve bieu do
export const POLL_INTERVAL_MS = 15000; // chu ky doc lai du lieu qua HTTP (ms)
