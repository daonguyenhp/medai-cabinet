export const DAYS_VI = {
  monday:    'T2',
  tuesday:   'T3',
  wednesday: 'T4',
  thursday:  'T5',
  friday:    'T6',
  saturday:  'T7',
  sunday:    'CN',
};

export const ALL_DAYS = Object.keys(DAYS_VI);

export const DOSE_STATUS = {
  pending: { label: 'Chờ uống',  badgeClass: 'badge-primary',  icon: '⏳' },
  taken:   { label: 'Đã uống',   badgeClass: 'badge-success',  icon: '✅' },
  late:    { label: 'Uống muộn', badgeClass: 'badge-warning',  icon: '⚠️' },
  missed:  { label: 'Bỏ liều',   badgeClass: 'badge-danger',   icon: '❌' },
  skipped: { label: 'Bỏ qua',    badgeClass: 'badge-primary',  icon: '⏭️' },
};

export const EMPTY_SCHEDULE_FORM = {
  medication_id: '',
  times: ['08:00'],
  days_of_week: Object.keys(DAYS_VI),
  dosage_count: 1,
  instructions: '',
  start_date: '',
  end_date: '',
  is_active: true,
  reminder_enabled: true,
  caregiver_notify: false,
};

export const DEMO_TODAY_SCHEDULE = [
  {
    schedule_id: '1',
    medication_id: '1',
    medication_name: 'Paracetamol 500mg',
    medication_type: 'pill',
    compartment: 1,
    dosage_count: 2,
    unit: 'viên',
    scheduled_time: '08:00',
    scheduled_datetime: new Date().toISOString(),
    status: 'taken',
    instructions: 'Sau ăn sáng',
    is_overdue: false,
  },
  {
    schedule_id: '2',
    medication_id: '2',
    medication_name: 'Vitamin C 1000mg',
    medication_type: 'pill',
    compartment: 2,
    dosage_count: 1,
    unit: 'viên',
    scheduled_time: '12:00',
    scheduled_datetime: new Date().toISOString(),
    status: 'pending',
    instructions: 'Sau ăn trưa',
    is_overdue: false,
    minutes_until_dose: 45,
  },
  {
    schedule_id: '3',
    medication_id: '3',
    medication_name: 'Thuốc huyết áp',
    medication_type: 'pill',
    compartment: 3,
    dosage_count: 1,
    unit: 'viên',
    scheduled_time: '20:00',
    scheduled_datetime: new Date().toISOString(),
    status: 'pending',
    instructions: 'Trước khi ngủ',
    is_overdue: false,
    minutes_until_dose: 480,
  },
];
