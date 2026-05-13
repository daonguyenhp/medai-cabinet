import { useState } from 'react';
import toast from 'react-hot-toast';
import { useApp } from '../App';
import { useSchedules } from '../hooks';
import DoseAlert from '../components/schedule/DoseAlert';
import ScheduleForm from '../components/schedule/ScheduleForm';
import { DAYS_VI, EMPTY_SCHEDULE_FORM } from '../constants/schedule.constants';
import { useMedications } from '../hooks';
import '../styles/schedule.css';

const TABS = [
  { key: 'today',     label: 'Hôm nay' },
  { key: 'schedules', label: 'Tất cả lịch' },
  { key: 'history',   label: 'Lịch sử' },
];

const STATUS_LABEL = {
  taken:   '✅ Đã uống',
  missed:  '❌ Bỏ liều',
  late:    '⚠️ Muộn',
  skipped: '⏭️ Bỏ qua',
  pending: '⏳ Chờ',
};

const STATUS_BADGE = {
  taken:   'badge-success',
  missed:  'badge-danger',
  late:    'badge-warning',
  skipped: 'badge-primary',
  pending: 'badge-primary',
};

export default function Schedule() {
  const { user } = useApp();
  const { schedules, todaySchedule, history, loading, create, remove, recordTaken, recordSkipped } =
    useSchedules(user.user_id);
  const { medications } = useMedications(user.user_id);

  const [activeTab, setActiveTab] = useState('today');
  const [showForm, setShowForm]   = useState(false);
  const [form, setForm]           = useState(EMPTY_SCHEDULE_FORM);
  const [saving, setSaving]       = useState(false);

  const handleSave = async () => {
    if (!form.medication_id) { toast.error('Chọn thuốc'); return; }
    if (!form.times.length)  { toast.error('Thêm ít nhất 1 giờ uống'); return; }
    setSaving(true);
    try {
      await create({ ...form, dosage_count: parseInt(form.dosage_count, 10) });
      setShowForm(false);
      setForm(EMPTY_SCHEDULE_FORM);
    } catch (err) {
      toast.error(err.userMessage ?? 'Lỗi tạo lịch');
    } finally {
      setSaving(false);
    }
  };

  const takenToday = todaySchedule.filter((d) => d.status === 'taken').length;
  const totalToday = todaySchedule.length;
  const pct        = totalToday > 0 ? Math.round((takenToday / totalToday) * 100) : 0;

  return (
    <div>
      {/* Summary bar */}
      <div className="schedule-summary">
        <div className="schedule-summary-stat">
          <span className="schedule-summary-num">{takenToday}/{totalToday}</span>
          <span className="schedule-summary-label">Liều hôm nay</span>
        </div>
        <div className="schedule-summary-progress">
          <div className="progress" style={{ height: 12 }}>
            <div
              className={`progress-bar ${takenToday === totalToday && totalToday > 0 ? 'success' : 'primary'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="schedule-summary-pct">{pct}% hoàn thành</span>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Tạo lịch mới
        </button>
      </div>

      {/* Tabs */}
      <div className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Today */}
      {activeTab === 'today' && (
        loading ? (
          <div className="loading-overlay"><div className="spinner" /><span>Đang tải...</span></div>
        ) : todaySchedule.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📅</div>
            <h3>Không có lịch hôm nay</h3>
            <p>Tạo lịch uống thuốc để nhận nhắc nhở.</p>
            <button className="btn btn-primary mt-4" onClick={() => setShowForm(true)}>Tạo lịch</button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {todaySchedule.map((dose, i) => (
              <DoseAlert key={i} dose={dose} onTake={recordTaken} onSkip={recordSkipped} />
            ))}
          </div>
        )
      )}

      {/* All schedules */}
      {activeTab === 'schedules' && (
        schedules.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📋</div>
            <h3>Chưa có lịch nào</h3>
            <button className="btn btn-primary mt-4" onClick={() => setShowForm(true)}>Tạo lịch đầu tiên</button>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {schedules.map((sched) => (
              <div key={sched.schedule_id} className="schedule-card">
                <div className="schedule-card-header">
                  <div>
                    <div className="schedule-card-name">{sched.medication_name ?? 'Thuốc'}</div>
                    <div className="schedule-card-times">
                      {sched.times?.map((t) => (
                        <span key={t} className="schedule-time-badge">{t}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`badge ${sched.is_active ? 'badge-success' : 'badge-primary'}`}>
                      {sched.is_active ? 'Đang hoạt động' : 'Tạm dừng'}
                    </span>
                    <button className="btn btn-ghost btn-sm" onClick={() => remove(sched.schedule_id)}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div className="schedule-card-meta">
                  <span>💊 {sched.dosage_count} {sched.unit ?? 'viên'}/lần</span>
                  <span>📅 {sched.days_of_week?.map((d) => DAYS_VI[d]).join(', ')}</span>
                  {sched.instructions && <span>📋 {sched.instructions}</span>}
                </div>
              </div>
            ))}
          </div>
        )
      )}

      {/* History */}
      {activeTab === 'history' && (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Thuốc</th>
                  <th>Giờ dự kiến</th>
                  <th>Giờ uống</th>
                  <th>Trạng thái</th>
                  <th>Số lượng</th>
                </tr>
              </thead>
              <tbody>
                {history.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center text-muted" style={{ padding: 'var(--space-8)' }}>
                      Chưa có lịch sử
                    </td>
                  </tr>
                ) : (
                  history.map((h) => (
                    <tr key={h.history_id}>
                      <td className="font-semibold">{h.medication_name ?? h.medication_id}</td>
                      <td>{h.scheduled_time ? new Date(h.scheduled_time).toLocaleString('vi-VN') : '--'}</td>
                      <td>{h.taken_time    ? new Date(h.taken_time).toLocaleString('vi-VN')    : '--'}</td>
                      <td>
                        <span className={`badge ${STATUS_BADGE[h.status] ?? 'badge-primary'}`}>
                          {STATUS_LABEL[h.status] ?? h.status}
                        </span>
                      </td>
                      <td>{h.dosage_count}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal */}
      {showForm && (
        <ScheduleForm
          form={form}
          onChange={setForm}
          medications={medications}
          onSave={handleSave}
          onClose={() => setShowForm(false)}
          saving={saving}
        />
      )}
    </div>
  );
}
