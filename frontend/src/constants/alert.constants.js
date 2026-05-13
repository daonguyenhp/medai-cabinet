export const SEVERITY_CONFIG = {
  critical: { label: 'Khẩn cấp',  badgeClass: 'badge-danger',  icon: '🔴', rowClass: 'alert-row-critical' },
  warning:  { label: 'Cảnh báo',  badgeClass: 'badge-warning', icon: '🟡', rowClass: 'alert-row-warning' },
  info:     { label: 'Thông tin', badgeClass: 'badge-info',    icon: '🔵', rowClass: '' },
};

export const ALERT_TYPE_ICONS = {
  expired:           '⛔',
  expiry_critical:   '🔴',
  expiry_warning:    '🟡',
  low_stock:         '📦',
  missed_dose:       '💊',
  high_temperature:  '🌡️',
  high_humidity:     '💧',
  low_battery:       '🔋',
  device_offline:    '📡',
  triage_see_doctor: '🏥',
};

export const DEMO_ALERTS = [
  {
    alert_id: '1',
    type: 'expiry_critical',
    message: '🔴 Thuốc Vitamin C 1000mg sắp hết hạn trong 5 ngày!',
    severity: 'critical',
    timestamp: new Date().toISOString(),
    resolved: false,
  },
  {
    alert_id: '2',
    type: 'low_stock',
    message: '📦 Thuốc Vitamin C 1000mg sắp hết: còn 3 viên',
    severity: 'warning',
    timestamp: new Date(Date.now() - 3_600_000).toISOString(),
    resolved: false,
  },
  {
    alert_id: '3',
    type: 'expired',
    message: '⛔ Thuốc nhỏ mắt Rohto đã hết hạn. Không sử dụng!',
    severity: 'critical',
    timestamp: new Date(Date.now() - 7_200_000).toISOString(),
    resolved: false,
  },
  {
    alert_id: '4',
    type: 'missed_dose',
    message: '⚠️ Bỏ lỡ liều thuốc Paracetamol lúc 08:00',
    severity: 'warning',
    timestamp: new Date(Date.now() - 86_400_000).toISOString(),
    resolved: true,
    resolved_at: new Date(Date.now() - 3_600_000).toISOString(),
  },
];
