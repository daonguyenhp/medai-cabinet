export const DEMO_DEVICE = {
  device_id: 'medai-esp32-001',
  device_name: 'MedAI Cabinet',
  status: 'offline',
};

export const DEMO_TELEMETRY = {
  device_id: 'medai-esp32-001',
  timestamp: new Date().toISOString(),
  temperature: 26.5,
  humidity: 58.2,
  wifi_ssid: 'LongChau-Home',
  wifi_rssi: -65,
  wifi_ip: '192.168.1.42',
  firmware_version: '1.2.0',
  uptime_seconds: 86400,
  free_heap: 180000,
  compartment_status: [
    { compartment_id: 1, is_open: false },
    { compartment_id: 2, is_open: false },
    { compartment_id: 3, is_open: false },
  ],
};

export const DEMO_TELEMETRY_HISTORY = Array.from({ length: 24 }, (_, i) => ({
  time: `${String(i).padStart(2, '0')}:00`,
  temp: parseFloat((25 + Math.random() * 3).toFixed(1)),
  humidity: parseFloat((55 + Math.random() * 10).toFixed(1)),
}));

export const DEMO_DASHBOARD = {
  medications: { total: 5, expired: 1, near_expiry: 2, low_stock: 1, out_of_stock: 0, healthy: 2 },
  today_schedule: {
    total_doses: 3,
    taken: 1,
    remaining: 2,
    completion_rate: 33,
    next_dose: { time: '14:00', medication_name: 'Paracetamol', dosage_count: 2, unit: 'viên' },
  },
  adherence: { rate_7d: 82, label: 'Tốt' },
  alerts: { unresolved: 3, by_severity: { info: 1, warning: 2, critical: 0 }, recent: [] },
  device: { online: false, temperature: 26.5, humidity: 58, wifi_ssid: 'LongChau-Home', wifi_rssi: -65, wifi_ip: '192.168.1.42' },
};

export const WIFI_STRENGTH_LEVELS = [
  { threshold: -50, label: 'Rất tốt', colorClass: 'text-success' },
  { threshold: -70, label: 'Tốt',     colorClass: 'text-success' },
  { threshold: -80, label: 'Trung bình', colorClass: 'text-warning' },
  { threshold: -Infinity, label: 'Yếu', colorClass: 'text-danger' },
];
