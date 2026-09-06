import { useCallback, useEffect, useRef, useState } from 'react';
import mqtt, { MqttClient } from 'mqtt';
import {
  MQTT_CHANNEL_ID,
  MQTT_CHANNEL_READ_API_KEY,
  MQTT_CLIENT_ID,
  MQTT_HOST,
  MQTT_MODE_FIELD,
  MQTT_PASSWORD,
  MQTT_USERNAME,
  MQTT_WSS_PORT,
  POLL_INTERVAL_MS,
  THINGSPEAK_HTTP_BASE,
} from '../config';
import { Mode } from '../types';

function toMode(value: unknown): Mode {
  return Number(value) === 1 ? 'manual' : 'auto';
}

/**
 * Quan ly toan bo che do Auto/Manual: publish + subscribe qua MQTT (BAT
 * BUOC theo de bai), CONG VOI mot lop du phong doc qua HTTP.
 *
 * LUU Y QUAN TRONG (phat hien khi test that voi phan cung): ThingSpeak yeu
 * cau client_id MQTT phai trung voi username, nen Web va Raspberry Pi buoc
 * phai dung CHUNG 1 danh tinh MQTT - moi lan mot ben ket noi/publish se lam
 * ben kia bi ngat tam thoi, va ThingSpeak KHONG luu retained message that su
 * tren topic dang channel-feed nay. Vi vay MQTT chi la duong nhanh; HTTP
 * polling (channel MQTT rieng, chi co 1 field ten "Mode") la nguon du lieu
 * chac chan, dam bao khong bao gio mat cap nhat che do.
 */
export function useMqttMode() {
  const [mode, setMode] = useState<Mode>('auto');
  const [connected, setConnected] = useState(false);
  const clientRef = useRef<MqttClient | null>(null);

  // -- Duong nhanh: MQTT subscribe (topic so 1 - toan bo channel feed) --
  useEffect(() => {
    const client = mqtt.connect(`wss://${MQTT_HOST}:${MQTT_WSS_PORT}/mqtt`, {
      clientId: MQTT_CLIENT_ID,
      username: MQTT_USERNAME,
      password: MQTT_PASSWORD,
      reconnectPeriod: 3000,
    });
    clientRef.current = client;

    client.on('connect', () => {
      setConnected(true);
      client.subscribe(`channels/${MQTT_CHANNEL_ID}/subscribe`);
    });
    client.on('reconnect', () => setConnected(false));
    client.on('close', () => setConnected(false));
    client.on('error', (err) => console.warn('[MQTT] Loi ket noi:', err.message));
    client.on('message', (_topic, payload) => {
      try {
        const data = JSON.parse(payload.toString());
        if (data[MQTT_MODE_FIELD] != null) setMode(toMode(data[MQTT_MODE_FIELD]));
      } catch (e) {
        console.warn('[MQTT] Payload khong hop le:', e);
      }
    });

    return () => {
      client.end(true);
    };
  }, []);

  // -- Duong du phong: HTTP polling dinh ky tren kenh MQTT --
  useEffect(() => {
    let cancelled = false;
    const fetchMode = async () => {
      try {
        const url =
          `${THINGSPEAK_HTTP_BASE}/channels/${MQTT_CHANNEL_ID}/feeds.json` +
          `?api_key=${MQTT_CHANNEL_READ_API_KEY}&results=10`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const feeds: Array<Record<string, unknown>> = data.feeds ?? [];
        for (let i = feeds.length - 1; i >= 0; i--) {
          const value = feeds[i][MQTT_MODE_FIELD];
          if (value != null && value !== '') {
            if (!cancelled) setMode(toMode(value));
            break;
          }
        }
      } catch (e) {
        console.warn('[HTTP] Doc che do du phong that bai:', e);
      }
    };
    fetchMode();
    const timer = setInterval(fetchMode, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const changeMode = useCallback(
    (next: Mode) => {
      setMode(next); // phan hoi lac quan tren giao dien, se duoc HTTP xac nhan lai sau
      const client = clientRef.current;
      if (!client || !connected) {
        console.warn('[MQTT] Chua ket noi, khong the gui che do.');
        return;
      }
      const value = next === 'manual' ? '1' : '0';
      client.publish(`channels/${MQTT_CHANNEL_ID}/publish/fields/${MQTT_MODE_FIELD}`, value, {
        retain: true,
      });
    },
    [connected],
  );

  return { mode, connected, changeMode };
}
