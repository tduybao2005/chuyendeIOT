import { useCallback, useState } from 'react';
import { FIELD, THINGSPEAK_HTTP_BASE, THINGSPEAK_WRITE_API_KEY } from '../config';
import { DeviceKey } from '../types';

const MAX_ATTEMPTS = 3;
const RETRY_DELAY_MS = 3000;

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Gui 1 lan HTTP POST update.json, tra ve true neu ThingSpeak thuc su tao
 * ban ghi moi (entry_id > 0). ThingSpeak tra ve HTTP 200 kem noi dung "0"
 * khi bi tu choi (vi du: chua du 15s ke tu lan ghi truoc len CUNG channel
 * nay - co the la lan ghi cua chinh Raspberry Pi) - phai kiem tra noi dung
 * tra ve, khong chi dua vao `res.ok`.
 */
async function postOnce(field: string, value: boolean): Promise<boolean> {
  const body = new URLSearchParams({
    api_key: THINGSPEAK_WRITE_API_KEY,
    [field]: value ? '1' : '0',
  });
  const res = await fetch(`${THINGSPEAK_HTTP_BASE}/update.json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const result = await res.json();
  return typeof result === 'object' && result !== null && Number(result.entry_id) > 0;
}

/**
 * Gui lenh bat/tat LED, Buzzer, Relay len ThingSpeak qua HTTP - BAT BUOC
 * dung HTTP theo de bai (khac voi nut chon che do dung MQTT trong
 * useMqttMode.ts). Tu dong thu lai vi ThingSpeak gioi han toi thieu 15s
 * giua 2 lan ghi len CUNG 1 channel (channel nay cung duoc Raspberry Pi ghi
 * trung binh cam bien moi 20s, nen co the trung nhip).
 */
export function useDeviceCommand() {
  const [sending, setSending] = useState<DeviceKey | null>(null);

  const sendCommand = useCallback(async (device: DeviceKey, value: boolean) => {
    setSending(device);
    try {
      const field = FIELD[device]; // 'field6' | 'field7' | 'field8'
      for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
        try {
          const ok = await postOnce(field, value);
          if (ok) return;
        } catch (e) {
          console.warn(`[HTTP] Gui lenh dieu khien loi (lan ${attempt}):`, e);
        }
        if (attempt < MAX_ATTEMPTS) await delay(RETRY_DELAY_MS);
      }
      console.warn('[HTTP] Gui lenh dieu khien that bai sau nhieu lan thu (co the do gioi han 15s/lan ghi cua ThingSpeak)');
    } finally {
      setSending(null);
    }
  }, []);

  return { sendCommand, sending };
}
