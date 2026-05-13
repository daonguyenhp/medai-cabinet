export const MEDICATION_TYPES = [
  { value: 'pill',      label: 'Viên uống',   color: 'primary' },
  { value: 'syrup',     label: 'Siro',         color: 'teal' },
  { value: 'eyedrop',   label: 'Nhỏ mắt',     color: 'info' },
  { value: 'injection', label: 'Thuốc tiêm',  color: 'warning' },
  { value: 'cream',     label: 'Kem bôi',     color: 'success' },
  { value: 'other',     label: 'Khác',        color: 'primary' },
];

export const MEDICATION_TYPE_MAP = Object.fromEntries(
  MEDICATION_TYPES.map((t) => [t.value, t]),
);

export const EXPIRY_STATUS = {
  ok:       { label: 'Còn hạn',     badgeClass: 'badge-success' },
  warning:  { label: 'Sắp hết hạn', badgeClass: 'badge-warning' },
  critical: { label: 'Gần hết hạn', badgeClass: 'badge-danger' },
  expired:  { label: 'Hết hạn',     badgeClass: 'badge-danger' },
};

export const EMPTY_MEDICATION_FORM = {
  name: '',
  generic_name: '',
  medication_type: 'pill',
  compartment: 1,
  stock_count: 0,
  unit: 'viên',
  dosage_strength: '',
  manufacturer: '',
  expiry_date: '',
  opened_date: '',
  post_opening_days: '',
  storage_instructions: '',
  notes: '',
  low_stock_threshold: 5,
};

export const DEMO_MEDICATIONS = [
  {
    medication_id: '1',
    name: 'Paracetamol 500mg',
    medication_type: 'pill',
    compartment: 1,
    stock_count: 20,
    unit: 'viên',
    dosage_strength: '500mg',
    expiry_date: '2025-12-31',
    expiry_status: 'ok',
    days_until_expiry: 180,
    low_stock_threshold: 5,
  },
  {
    medication_id: '2',
    name: 'Vitamin C 1000mg',
    medication_type: 'pill',
    compartment: 2,
    stock_count: 3,
    unit: 'viên',
    dosage_strength: '1000mg',
    expiry_date: '2024-03-15',
    expiry_status: 'warning',
    days_until_expiry: 20,
    warning_message: '🟡 Thuốc còn 20 ngày đến hết hạn',
    low_stock_threshold: 5,
  },
  {
    medication_id: '3',
    name: 'Thuốc nhỏ mắt Rohto',
    medication_type: 'eyedrop',
    compartment: 3,
    stock_count: 1,
    unit: 'lọ',
    expiry_date: '2024-01-10',
    expiry_status: 'expired',
    days_until_expiry: -5,
    warning_message: '⛔ Thuốc đã hết hạn 5 ngày trước. Không sử dụng!',
    low_stock_threshold: 1,
  },
];
