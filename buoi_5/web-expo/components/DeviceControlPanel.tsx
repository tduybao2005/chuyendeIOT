import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { DeviceKey, Mode } from '../types';

interface DeviceRowProps {
  label: string;
  icon: string;
  active: boolean;
  disabled: boolean;
  busy: boolean;
  onToggle: () => void;
}

/** 1 hang dieu khien: bieu tuong + trang thai bat/tat + nut bam.
 *  Tach thanh ham rieng de DeviceControlPanel de doc, khong lap code 3 lan. */
function DeviceRow({ label, icon, active, disabled, busy, onToggle }: DeviceRowProps) {
  return (
    <View style={styles.row}>
      <View style={styles.rowLeft}>
        <Text style={styles.icon}>{icon}</Text>
        <Text style={styles.rowLabel}>{label}</Text>
      </View>
      <View style={styles.rowRight}>
        <View style={[styles.badge, { backgroundColor: active ? '#4CAF50' : '#BDBDBD' }]}>
          <Text style={styles.badgeText}>{active ? 'ON' : 'OFF'}</Text>
        </View>
        <TouchableOpacity
          style={[styles.button, disabled && styles.buttonDisabled]}
          disabled={disabled || busy}
          onPress={onToggle}
        >
          <Text style={styles.buttonText}>{busy ? '...' : active ? 'Tắt' : 'Bật'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

interface Props {
  mode: Mode;
  led: boolean;
  buzzer: boolean;
  relay: boolean;
  sendingDevice: DeviceKey | null;
  onToggleDevice: (device: DeviceKey, nextValue: boolean) => void;
}

/**
 * Bieu tuong trang thai + nut bat/tat LED, Buzzer, Relay - BAT BUOC gui len
 * Server bang HTTP (xu ly trong hooks/useDeviceCommand.ts). Cac nut chi hoat
 * dong o che do Manual, dung voi mo ta de bai.
 */
export default function DeviceControlPanel({
  mode,
  led,
  buzzer,
  relay,
  sendingDevice,
  onToggleDevice,
}: Props) {
  const disabled = mode !== 'manual';

  return (
    <View style={styles.card}>
      <Text style={styles.title}>
        Điều khiển thiết bị {disabled ? '(chỉ dùng được ở chế độ Manual)' : ''}
      </Text>
      <DeviceRow
        label="LED"
        icon="💡"
        active={led}
        disabled={disabled}
        busy={sendingDevice === 'led'}
        onToggle={() => onToggleDevice('led', !led)}
      />
      <DeviceRow
        label="Buzzer"
        icon="🔊"
        active={buzzer}
        disabled={disabled}
        busy={sendingDevice === 'buzzer'}
        onToggle={() => onToggleDevice('buzzer', !buzzer)}
      />
      <DeviceRow
        label="Relay"
        icon="🔌"
        active={relay}
        disabled={disabled}
        busy={sendingDevice === 'relay'}
        onToggle={() => onToggleDevice('relay', !relay)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16 },
  title: { fontSize: 13, color: '#777', marginBottom: 8 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  rowLeft: { flexDirection: 'row', alignItems: 'center' },
  icon: { fontSize: 20, marginRight: 8 },
  rowLabel: { fontSize: 15, fontWeight: '600', color: '#333' },
  rowRight: { flexDirection: 'row', alignItems: 'center' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 10, marginRight: 10 },
  badgeText: { color: '#fff', fontSize: 11, fontWeight: '700' },
  button: {
    backgroundColor: '#1783B0',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    minWidth: 56,
    alignItems: 'center',
  },
  buttonDisabled: { backgroundColor: '#CCC' },
  buttonText: { color: '#fff', fontWeight: '600', fontSize: 13 },
});
