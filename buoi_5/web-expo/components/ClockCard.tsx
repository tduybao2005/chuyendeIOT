import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';

function formatClock(date: Date) {
  return date.toLocaleTimeString('vi-VN', { hour12: false });
}

function formatDate(date: Date) {
  return date.toLocaleDateString('vi-VN');
}

/** "Cua so hien thi thoi gian hien tai" - dong ho lay theo gio cua thiet bi,
 *  tu cap nhat moi giay. */
export default function ClockCard() {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <View style={styles.card}>
      <Text style={styles.label}>Thời gian hiện tại</Text>
      <Text style={styles.clock}>{formatClock(now)}</Text>
      <Text style={styles.date}>{formatDate(now)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  label: { fontSize: 13, color: '#777', marginBottom: 4 },
  clock: { fontSize: 28, fontWeight: '700', color: '#1783B0' },
  date: { fontSize: 13, color: '#999', marginTop: 2 },
});
