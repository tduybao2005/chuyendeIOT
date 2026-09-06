import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Mode } from '../types';

interface Props {
  mode: Mode;
  mqttConnected: boolean;
  onChangeMode: (mode: Mode) => void;
}

/**
 * Nut chon che do Auto/Manual - BAT BUOC gui len Server bang MQTT
 * (xu ly trong hooks/useMqttMode.ts, component nay chi hien thi + goi callback).
 */
export default function ModeToggle({ mode, mqttConnected, onChangeMode }: Props) {
  const isManual = mode === 'manual';

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Chế độ hoạt động</Text>
        <View style={[styles.dot, { backgroundColor: mqttConnected ? '#4CAF50' : '#BDBDBD' }]} />
        <Text style={styles.mqttLabel}>{mqttConnected ? 'MQTT đã kết nối' : 'MQTT mất kết nối'}</Text>
      </View>
      <View style={styles.switchRow}>
        <TouchableOpacity
          style={[styles.option, !isManual && styles.optionActive]}
          onPress={() => onChangeMode('auto')}
        >
          <Text style={[styles.optionText, !isManual && styles.optionTextActive]}>🤖 Auto</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.option, isManual && styles.optionActive]}
          onPress={() => onChangeMode('manual')}
        >
          <Text style={[styles.optionText, isManual && styles.optionTextActive]}>✋ Manual</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16 },
  headerRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  title: { fontSize: 13, color: '#777', flex: 1 },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 4 },
  mqttLabel: { fontSize: 11, color: '#999' },
  switchRow: { flexDirection: 'row', backgroundColor: '#F0F0F0', borderRadius: 10, padding: 4 },
  option: { flex: 1, paddingVertical: 10, alignItems: 'center', borderRadius: 8 },
  optionActive: { backgroundColor: '#1783B0' },
  optionText: { fontSize: 15, fontWeight: '600', color: '#666' },
  optionTextActive: { color: '#fff' },
});
