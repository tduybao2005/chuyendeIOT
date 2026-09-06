import React, { useState } from 'react';
import { View, Text, StyleSheet, LayoutChangeEvent } from 'react-native';
import Svg, { Polyline, Line } from 'react-native-svg';
import { HistoryPoint } from '../hooks/useThingSpeakData';

interface Props {
  history: HistoryPoint[];
}

const CHART_HEIGHT = 200;
const PADDING = 24;

type Point = { x: number; y: number } | null;

/** Chuyen 1 mang gia tri (co the co null) thanh toa do diem tren SVG. */
function buildPoints(values: (number | null)[], width: number, min: number, max: number): Point[] {
  const usableWidth = width - PADDING * 2;
  const usableHeight = CHART_HEIGHT - PADDING * 2;
  const range = max - min || 1;
  return values.map((v, i) => {
    if (v === null) return null;
    const x = PADDING + (values.length <= 1 ? 0 : (i / (values.length - 1)) * usableWidth);
    const y = PADDING + usableHeight - ((v - min) / range) * usableHeight;
    return { x, y };
  });
}

function toPolylineString(points: Point[]): string {
  return points
    .filter((p): p is { x: number; y: number } => p !== null)
    .map((p) => `${p.x},${p.y}`)
    .join(' ');
}

function ChartLegend() {
  return (
    <View style={styles.legendRow}>
      <View style={styles.legendItem}>
        <View style={[styles.legendDot, { backgroundColor: '#E53935' }]} />
        <Text style={styles.legendText}>Nhiệt độ (°C)</Text>
      </View>
      <View style={styles.legendItem}>
        <View style={[styles.legendDot, { backgroundColor: '#1E88E5' }]} />
        <Text style={styles.legendText}>Độ ẩm (%)</Text>
      </View>
    </View>
  );
}

/** "Do thi the hien hai gia tri nhiet do va do am doc duoc tu Server". */
export default function TempHumiChart({ history }: Props) {
  const [width, setWidth] = useState(300);

  const handleLayout = (e: LayoutChangeEvent) => setWidth(e.nativeEvent.layout.width);

  if (history.length === 0) {
    return (
      <View style={styles.card} onLayout={handleLayout}>
        <Text style={styles.title}>Biểu đồ nhiệt độ / độ ẩm</Text>
        <Text style={styles.empty}>Chưa có dữ liệu</Text>
      </View>
    );
  }

  const temps = history.map((h) => h.temp);
  const humis = history.map((h) => h.humi);
  const allValues = [...temps, ...humis].filter((v): v is number => v !== null);
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);

  const tempPoints = buildPoints(temps, width, min, max);
  const humiPoints = buildPoints(humis, width, min, max);

  return (
    <View style={styles.card} onLayout={handleLayout}>
      <Text style={styles.title}>Biểu đồ nhiệt độ / độ ẩm</Text>
      <ChartLegend />
      <Svg width={width} height={CHART_HEIGHT}>
        <Line
          x1={PADDING}
          y1={CHART_HEIGHT - PADDING}
          x2={width - PADDING}
          y2={CHART_HEIGHT - PADDING}
          stroke="#E0E0E0"
          strokeWidth={1}
        />
        <Polyline points={toPolylineString(tempPoints)} fill="none" stroke="#E53935" strokeWidth={2} />
        <Polyline points={toPolylineString(humiPoints)} fill="none" stroke="#1E88E5" strokeWidth={2} />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16 },
  title: { fontSize: 13, color: '#777', marginBottom: 8 },
  legendRow: { flexDirection: 'row', marginBottom: 8 },
  legendItem: { flexDirection: 'row', alignItems: 'center', marginRight: 16 },
  legendDot: { width: 8, height: 8, borderRadius: 4, marginRight: 4 },
  legendText: { fontSize: 12, color: '#666' },
  empty: { textAlign: 'center', color: '#999', paddingVertical: 30 },
});
