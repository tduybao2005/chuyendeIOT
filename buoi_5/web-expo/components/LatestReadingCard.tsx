import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface Props {
  temp: number | null;
  humi: number | null;
  updatedAt: string | null;
  loading: boolean;
  error: string | null;
}

function formatUpdatedAt(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('vi-VN');
}

/** "Cua so hien thi gia tri nhiet do, do am doc duoc tu Server" (lan cap
 *  nhat cuoi cung). */
export default function LatestReadingCard({ temp, humi, updatedAt, loading, error }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Giá trị mới nhất từ Server</Text>
      <View style={styles.row}>
        <View style={styles.item}>
          <Text style={styles.value}>{temp !== null ? `${temp.toFixed(1)}°C` : '--'}</Text>
          <Text style={styles.itemLabel}>Nhiệt độ</Text>
        </View>
        <View style={styles.item}>
          <Text style={styles.value}>{humi !== null ? `${humi.toFixed(1)}%` : '--'}</Text>
          <Text style={styles.itemLabel}>Độ ẩm</Text>
        </View>
      </View>
      <Text style={styles.updatedAt}>Cập nhật lúc: {formatUpdatedAt(updatedAt)}</Text>
      {loading && <Text style={styles.hint}>Đang tải...</Text>}
      {error && <Text style={styles.error}>Lỗi: {error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16 },
  title: { fontSize: 13, color: '#777', marginBottom: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-around' },
  item: { alignItems: 'center' },
  value: { fontSize: 26, fontWeight: '700', color: '#222' },
  itemLabel: { fontSize: 12, color: '#999', marginTop: 2 },
  updatedAt: { fontSize: 12, color: '#999', marginTop: 10, textAlign: 'center' },
  hint: { fontSize: 12, color: '#1783B0', marginTop: 4, textAlign: 'center' },
  error: { fontSize: 12, color: '#D32F2F', marginTop: 4, textAlign: 'center' },
});
