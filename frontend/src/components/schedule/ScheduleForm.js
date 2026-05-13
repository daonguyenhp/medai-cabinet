import '../../styles/modal.css';
import '../../styles/schedule.css';
import { DAYS_VI, ALL_DAYS } from '../../constants/schedule.constants';

/**
 * Create schedule modal form.
 */
export default function ScheduleForm({ form, onChange, medications, onSave, onClose, saving }) {
  const set = (field, value) => onChange({ ...form, [field]: value });

  const addTime    = () => set('times', [...form.times, '12:00']);
  const removeTime = (i) => set('times', form.times.filter((_, idx) => idx !== i));
  const updateTime = (i, val) => set('times', form.times.map((t, idx) => (idx === i ? val : t)));

  const toggleDay = (day) => {
    const days = form.days_of_week.includes(day)
      ? form.days_of_week.filter((d) => d !== day)
      : [...form.days_of_week, day];
    set('days_of_week', days);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Tạo lịch uống thuốc</h3>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label className="form-label">Chọn thuốc *</label>
            <select className="form-control" value={form.medication_id} onChange={(e) => set('medication_id', e.target.value)}>
              <option value="">-- Chọn thuốc --</option>
              {medications.map((m) => (
                <option key={m.medication_id} value={m.medication_id}>{m.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Giờ uống thuốc</label>
            {form.times.map((t, i) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <input type="time" className="form-control" value={t} onChange={(e) => updateTime(i, e.target.value)} style={{ maxWidth: 160 }} />
                {form.times.length > 1 && (
                  <button className="btn btn-ghost btn-sm" onClick={() => removeTime(i)}>✕</button>
                )}
              </div>
            ))}
            <button className="btn btn-outline btn-sm" onClick={addTime}>+ Thêm giờ</button>
          </div>

          <div className="form-group">
            <label className="form-label">Các ngày trong tuần</label>
            <div className="day-selector">
              {ALL_DAYS.map((day) => (
                <button
                  key={day}
                  className={`day-btn ${form.days_of_week.includes(day) ? 'active' : ''}`}
                  onClick={() => toggleDay(day)}
                >
                  {DAYS_VI[day]}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-2">
            <div className="form-group">
              <label className="form-label">Số lượng mỗi lần</label>
              <input type="number" className="form-control" value={form.dosage_count} onChange={(e) => set('dosage_count', e.target.value)} min={1} max={20} />
            </div>
            <div className="form-group">
              <label className="form-label">Hướng dẫn</label>
              <input className="form-control" value={form.instructions} onChange={(e) => set('instructions', e.target.value)} placeholder="Sau ăn, trước khi ngủ..." />
            </div>
          </div>

          <div className="form-group">
            <label className="flex items-center gap-3" style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={form.caregiver_notify}
                onChange={(e) => set('caregiver_notify', e.target.checked)}
                style={{ width: 20, height: 20 }}
              />
              <span className="form-label" style={{ margin: 0 }}>
                Thông báo người chăm sóc khi bỏ liều
              </span>
            </label>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Hủy</button>
          <button className="btn btn-primary" onClick={onSave} disabled={saving}>
            {saving ? 'Đang lưu...' : 'Tạo lịch'}
          </button>
        </div>
      </div>
    </div>
  );
}
