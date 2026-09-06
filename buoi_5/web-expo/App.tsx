import React, { useCallback } from 'react';
import { SafeAreaView, ScrollView, Text, View, StyleSheet, useWindowDimensions } from 'react-native';
import { StatusBar } from 'expo-status-bar';

import { useThingSpeakData } from './hooks/useThingSpeakData';
import { useMqttMode } from './hooks/useMqttMode';
import { useDeviceCommand } from './hooks/useDeviceCommand';
import ModeToggle from './components/ModeToggle';
import DeviceControlPanel from './components/DeviceControlPanel';
import LatestReadingCard from './components/LatestReadingCard';
import ClockCard from './components/ClockCard';
import TempHumiChart from './components/TempHumiChart';
import { DeviceKey } from './types';

/** Bo cuc dang luoi: 2 cot tren man hinh rong (iPad ngang / desktop),
 *  1 cot tren man hinh hep (dien thoai / iPad doc). */
function useResponsiveColumns() {
  const { width } = useWindowDimensions();
  return width >= 700;
}

export default function App() {
  const isWide = useResponsiveColumns();

  // Kenh HTTP: cam bien (chart, gia tri moi nhat) + trang thai LED/Buzzer/Relay
  const { history, deviceState, latest, error, loading } = useThingSpeakData();
  // Kenh MQTT rieng: che do Auto/Manual (MQTT + du phong HTTP, xem hook)
  const { mode, connected: mqttConnected, changeMode } = useMqttMode();
  // Gui lenh LED/Buzzer/Relay - BAT BUOC qua HTTP
  const { sendCommand, sending } = useDeviceCommand();

  const handleToggleDevice = useCallback(
    (device: DeviceKey, nextValue: boolean) => {
      sendCommand(device, nextValue);
    },
    [sendCommand],
  );

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="auto" />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.header}>Giám sát & Điều khiển - Nhóm 4</Text>

        <View style={[styles.grid, isWide && styles.gridWide]}>
          <View style={[styles.gridItem, isWide && styles.gridItemHalf]}>
            <ModeToggle mode={mode} mqttConnected={mqttConnected} onChangeMode={changeMode} />
          </View>
          <View style={[styles.gridItem, isWide && styles.gridItemHalf]}>
            <ClockCard />
          </View>
          <View style={[styles.gridItem, isWide && styles.gridItemHalf]}>
            <LatestReadingCard
              temp={latest.temp}
              humi={latest.humi}
              updatedAt={latest.updatedAt}
              loading={loading}
              error={error}
            />
          </View>
          <View style={[styles.gridItem, isWide && styles.gridItemHalf]}>
            <DeviceControlPanel
              mode={mode}
              led={deviceState.led}
              buzzer={deviceState.buzzer}
              relay={deviceState.relay}
              sendingDevice={sending}
              onToggleDevice={handleToggleDevice}
            />
          </View>
          <View style={styles.gridItem}>
            <TempHumiChart history={history} />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  scrollContent: { padding: 16, paddingBottom: 40 },
  header: { fontSize: 22, fontWeight: '700', textAlign: 'center', marginBottom: 16, color: '#222' },
  grid: { flexDirection: 'column' },
  gridWide: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -8 },
  // width: '100%' bat buoc phai co ngay ca khi khong isWide, neu khong khi
  // nam trong container flex-row (isWide) ma khong co chieu rong co dinh,
  // View bao ngoai bieu do se tu dong gian ra theo noi dung (SVG do rong
  // qua onLayout), tao vong lap do lech: container rong theo SVG, SVG lai
  // rong theo container -> width tang khong kiem soat tren web.
  gridItem: { marginBottom: 16, width: '100%' },
  gridItemHalf: { width: '50%', paddingHorizontal: 8 },
});
