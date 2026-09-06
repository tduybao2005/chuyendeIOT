import { useCallback, useEffect, useRef, useState } from 'react';
import {
  FIELD,
  HISTORY_RESULTS,
  POLL_INTERVAL_MS,
  THINGSPEAK_CHANNEL_ID,
  THINGSPEAK_HTTP_BASE,
  THINGSPEAK_READ_API_KEY,
} from '../config';
import { ChannelFeed, DeviceState } from '../types';

export interface HistoryPoint {
  createdAt: string;
  temp: number | null;
  humi: number | null;
}

interface LatestReading {
  temp: number | null;
  humi: number | null;
  updatedAt: string | null;
}

function toNumber(v?: string | null): number | null {
  if (v === undefined || v === null || v === '') return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
}

function toBool(v?: string | null): boolean {
  return toNumber(v) === 1;
}

/**
 * Moi lan Web ghi rieng le 1 field (vi du chi ghi field6 khi bam nut LED) se
 * tao ra MOT DONG MOI tren ThingSpeak, cac field con lai cua dong do la null.
 * Vi vay de biet trang thai "hien tai" cua tung field, phai quet nguoc tu
 * ban ghi moi nhat ve cu va lay gia tri KHONG null dau tien.
 */
function deriveLatestDeviceState(feeds: ChannelFeed[]): DeviceState {
  const result: DeviceState = { led: false, buzzer: false, relay: false };
  const found = { led: false, buzzer: false, relay: false };

  for (let i = feeds.length - 1; i >= 0; i--) {
    const f = feeds[i];
    if (!found.led && f[FIELD.led] != null && f[FIELD.led] !== '') {
      result.led = toBool(f[FIELD.led]);
      found.led = true;
    }
    if (!found.buzzer && f[FIELD.buzzer] != null && f[FIELD.buzzer] !== '') {
      result.buzzer = toBool(f[FIELD.buzzer]);
      found.buzzer = true;
    }
    if (!found.relay && f[FIELD.relay] != null && f[FIELD.relay] !== '') {
      result.relay = toBool(f[FIELD.relay]);
      found.relay = true;
    }
    if (found.led && found.buzzer && found.relay) break;
  }

  return result;
}

function deriveLatestSensorReading(feeds: ChannelFeed[]): LatestReading {
  for (let i = feeds.length - 1; i >= 0; i--) {
    const f = feeds[i];
    const temp = toNumber(f[FIELD.temp]);
    const humi = toNumber(f[FIELD.humi]);
    if (temp !== null || humi !== null) {
      return { temp, humi, updatedAt: f.created_at };
    }
  }
  return { temp: null, humi: null, updatedAt: null };
}

function buildHistory(feeds: ChannelFeed[]): HistoryPoint[] {
  return feeds
    .map((f) => ({
      createdAt: f.created_at,
      temp: toNumber(f[FIELD.temp]),
      humi: toNumber(f[FIELD.humi]),
    }))
    .filter((p) => p.temp !== null || p.humi !== null);
}

/**
 * Doc du lieu tu ThingSpeak qua HTTP (GET feeds.json) tren kenh HTTP, dinh
 * ky moi POLL_INTERVAL_MS. Dung de:
 * - Ve bieu do nhiet do/do am.
 * - Hien thi gia tri moi nhat + thoi diem cap nhat.
 * - Suy ra trang thai LED/Buzzer/Relay hien tai (che do Auto/Manual nam o
 *   kenh MQTT rieng - xem hooks/useMqttMode.ts).
 */
export function useThingSpeakData() {
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [deviceState, setDeviceState] = useState<DeviceState>({
    led: false,
    buzzer: false,
    relay: false,
  });
  const [latest, setLatest] = useState<LatestReading>({ temp: null, humi: null, updatedAt: null });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const url =
        `${THINGSPEAK_HTTP_BASE}/channels/${THINGSPEAK_CHANNEL_ID}/feeds.json` +
        `?api_key=${THINGSPEAK_READ_API_KEY}&results=${HISTORY_RESULTS}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const feeds: ChannelFeed[] = data.feeds ?? [];
      setHistory(buildHistory(feeds));
      setDeviceState(deriveLatestDeviceState(feeds));
      setLatest(deriveLatestSensorReading(feeds));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Loi khong xac dinh');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    timerRef.current = setInterval(fetchData, POLL_INTERVAL_MS);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchData]);

  return { history, deviceState, latest, error, loading, refresh: fetchData };
}
