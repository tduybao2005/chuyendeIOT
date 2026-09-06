export type Mode = 'auto' | 'manual';

export type DeviceKey = 'led' | 'buzzer' | 'relay';

/** Mot ban ghi (feed) tra ve tu ThingSpeak feeds.json. Cac field co the null
 *  neu lan ghi do khong dua gia tri cho field nay. */
export interface ChannelFeed {
  created_at: string;
  entry_id: number;
  field1?: string | null;
  field2?: string | null;
  field3?: string | null;
  field4?: string | null;
  field5?: string | null;
  field6?: string | null;
  field7?: string | null;
  field8?: string | null;
}

/** Trang thai 3 thiet bi tren kenh HTTP (khong bao gom mode - mode nam o
 *  kenh MQTT rieng, xem hooks/useMqttMode.ts). */
export interface DeviceState {
  led: boolean;
  buzzer: boolean;
  relay: boolean;
}
