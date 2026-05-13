export const QUICK_SYMPTOMS = [
  'Đau đầu, chóng mặt',
  'Sốt, cảm cúm',
  'Đau bụng, tiêu chảy',
  'Ho, đau họng',
  'Đau lưng, nhức mỏi',
  'Mất ngủ, lo âu',
  'Huyết áp cao',
  'Đau tim, khó thở',
];

export const SEVERITY_DISPLAY = {
  mild:     { label: 'Nhẹ',        badgeClass: 'badge-success', icon: '🟢' },
  moderate: { label: 'Trung bình', badgeClass: 'badge-warning', icon: '🟡' },
  severe:   { label: 'Nặng',       badgeClass: 'badge-danger',  icon: '🔴' },
  unknown:  { label: 'Chưa rõ',    badgeClass: 'badge-primary', icon: '⚪' },
};

export const INITIAL_AI_MESSAGE = {
  role: 'assistant',
  content:
    'Xin chào! Tôi là trợ lý y tế AI của MedAI Cabinet. Hãy mô tả triệu chứng của bạn và tôi sẽ đề xuất thuốc phù hợp từ tủ thuốc của bạn. Lưu ý: đây chỉ là tư vấn sơ bộ, không thay thế bác sĩ.',
};

export const DEMO_QUICK_CHECK = {
  total_medications: 5,
  expired: [{ name: 'Thuốc nhỏ mắt Rohto', days_overdue: 5 }],
  near_expiry: [{ name: 'Vitamin C 1000mg', days_remaining: 20 }],
  low_stock: [{ name: 'Vitamin C 1000mg', remaining: 3, unit: 'viên' }],
  needs_attention: 3,
};
