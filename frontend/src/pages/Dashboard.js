import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useApp } from '../App';
import { useDashboard } from '../hooks';
import DoseAlert from '../components/schedule/DoseAlert';
import EnvironmentMonitor from '../components/device/EnvironmentMonitor';
import { schedulesApi } from '../api';
import toast from 'react-hot-toast';
import '../styles/dashboard.css';

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'sáng';
  if (h < 18) return 'chiều';
  return 'tối';
}

export default function Dashboard() {
  const { user } = useApp();
  const { dashboard, todaySchedule, telemetryHistory, loading, refetch } = useDashboard(user.user_id);

  const handleTakeDose = async (dose) => {
    try {
      await schedulesApi.recordDose({
        user_id: user.user_id,
        medication_id: dose.medication_id,
        schedule_id: dose.schedule_id,
        scheduled_time: dose.scheduled_datetime,
        taken_time: new Date().toISOString(),
        status: 'taken',
        dosage_count: dose.dosage_count,
      });
      toast.success(`✅ Đã ghi nhận uống thuốc ${dose.medication_name}`);
      refetch();
    } catch {
      toast.error('Không thể ghi nhận. Vui lòng thử lại.');
    }
  };

  const handleSkipDose = async (dose) => {
    try {
      await schedulesApi.recordDose({
        user_id: user.user_id,
        medication_id: dose.medication_id,
        schedule_id: dose.schedule_id,
        scheduled_time: dose.scheduled_datetime,
        status: 'skipped',
        dosage_count: dose.dosage_count,
      });
      toast('Đã bỏ qua liều thuốc', { icon: '⏭️' });
      refetch();
    } catch {
      toast.error('Lỗi. Vui lòng thử lại.');
    }
  };

  if (loading) {
    return <div className="loading-overlay"><div className="spinner" /><span>Đang tải dữ liệu...</span></div>;
  }

  const meds      = dashboard?.medications    ?? {};
  const today     = dashboard?.today_schedule ?? {};
  const adherence = dashboard?.adherence      ?? {};
  const device    = dashboard?.device;
  const alerts    = dashboard?.alerts         ?? {};

  return (
    <div className="dashboard">
      {/* ── Welcome banner ── */}
      <div className="dashboard-welcome">
        <div>
          <h2 className="dashboard-welcome-title">
            Chào buổi {getGreeting()}, {user.name?.split(' ').pop()}! 👋
          </h2>
          <p className="dashboard-welcome-sub">
            {today.remaining > 0
              ? `Bạn còn ${today.remaining} liều thuốc cần uống hôm nay.`
              : today.total_doses > 0
              ? '🎉 Bạn đã uống đủ thuốc hôm nay!'
              : 'Không có lịch uống thuốc hôm nay.'}
          </p>
        </div>
        {today.next_dose && (
          <div className="dashboard-next-dose">
            <div className="next-dose-label">Liều tiếp theo</div>
            <div className="next-dose-time">{today.next_dose.time}</div>
            <div className="next-dose-med">{today.next_dose.medication_name}</div>
            <div className="next-dose-qty">{today.next_dose.dosage_count} {today.next_dose.unit}</div>
          </div>
        )}
      </div>

      {/* ── Stat cards ── */}
      <div className="grid grid-4 mb-6">
        <StatCard
          icon={<PillIcon />}
          value={meds.total ?? 0}
          label="Tổng số thuốc"
          variant="primary"
        />
        <StatCard
          icon={<CalendarIcon />}
          value={(meds.expired ?? 0) + (meds.near_expiry ?? 0)}
          label="Sắp/Đã hết hạn"
          variant={meds.expired > 0 ? 'danger' : meds.near_expiry > 0 ? 'warning' : 'success'}
          valueColor={meds.expired > 0 ? 'var(--color-danger)' : meds.near_expiry > 0 ? 'var(--color-warning-dark)' : undefined}
        />
        <StatCard
          icon={<PulseIcon />}
          value={`${adherence.rate_7d ?? 0}%`}
          label="Tuân thủ 7 ngày"
          variant={(adherence.rate_7d ?? 0) >= 75 ? 'success' : 'warning'}
        />
        <StatCard
          icon={<BellIcon />}
          value={alerts.unresolved ?? 0}
          label="Cảnh báo chưa xử lý"
          variant={(alerts.unresolved ?? 0) > 0 ? 'warning' : 'success'}
          valueColor={(alerts.unresolved ?? 0) > 0 ? 'var(--color-warning-dark)' : undefined}
        />
      </div>

      {/* ── Main grid ── */}
      <div className="dashboard-grid">
        {/* Today's schedule */}
        <div className="card dashboard-schedule">
          <div className="card-header">
            <div className="card-title">
              <CalendarIcon size={20} />
              Lịch hôm nay
            </div>
            <div className="flex items-center gap-3">
              {today.total_doses > 0 && (
                <div className="today-progress">
                  <span className="today-progress-text">{today.taken}/{today.total_doses} liều</span>
                  <div className="progress" style={{ width: 80 }}>
                    <div
                      className={`progress-bar ${today.completion_rate >= 100 ? 'success' : 'primary'}`}
                      style={{ width: `${today.completion_rate ?? 0}%` }}
                    />
                  </div>
                </div>
              )}
              <Link to="/schedule" className="btn btn-outline btn-sm">Xem tất cả</Link>
            </div>
          </div>
          <div className="card-body">
            {todaySchedule.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📅</div>
                <h3>Không có lịch hôm nay</h3>
                <p>Bạn không có lịch uống thuốc nào hôm nay.</p>
                <Link to="/schedule" className="btn btn-primary mt-4">Tạo lịch uống thuốc</Link>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {todaySchedule.slice(0, 5).map((dose, i) => (
                  <DoseAlert key={i} dose={dose} onTake={handleTakeDose} onSkip={handleSkipDose} />
                ))}
                {todaySchedule.length > 5 && (
                  <Link to="/schedule" className="btn btn-ghost btn-sm text-center">
                    Xem thêm {todaySchedule.length - 5} liều...
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-5">
          <div className="card">
            <div className="card-header">
              <div className="card-title"><MonitorIcon size={20} /> Môi trường tủ thuốc</div>
              <Link to="/device" className="btn btn-ghost btn-sm">Chi tiết</Link>
            </div>
            <div className="card-body">
              <EnvironmentMonitor telemetry={device} isOnline={device?.online ?? false} />
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">Thao tác nhanh</div>
            </div>
            <div className="card-body">
              <div className="quick-actions">
                <Link to="/medications" className="quick-action-btn">
                  <span className="quick-action-icon">💊</span><span>Thêm thuốc</span>
                </Link>
                <Link to="/schedule" className="quick-action-btn">
                  <span className="quick-action-icon">📅</span><span>Đặt lịch</span>
                </Link>
                <Link to="/ai-triage" className="quick-action-btn quick-action-ai">
                  <span className="quick-action-icon">🤖</span><span>Tư vấn AI</span>
                </Link>
                <Link to="/alerts" className="quick-action-btn">
                  <span className="quick-action-icon">🔔</span><span>Cảnh báo</span>
                  {(alerts.unresolved ?? 0) > 0 && (
                    <span className="quick-action-badge">{alerts.unresolved}</span>
                  )}
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Telemetry chart ── */}
      {telemetryHistory.length > 0 && (
        <div className="card mt-6">
          <div className="card-header">
            <div className="card-title"><PulseIcon size={20} /> Nhiệt độ & Độ ẩm (6 giờ qua)</div>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={telemetryHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                <XAxis dataKey="time" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} />
                <YAxis tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} />
                <Tooltip contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)' }} />
                <Line type="monotone" dataKey="temp"     stroke="var(--color-danger)" strokeWidth={2} dot={false} name="Nhiệt độ (°C)" />
                <Line type="monotone" dataKey="humidity" stroke="var(--color-teal)"   strokeWidth={2} dot={false} name="Độ ẩm (%)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Small reusable stat card ──────────────────────────────────────────────────
function StatCard({ icon, value, label, variant, valueColor }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${variant}`}>{icon}</div>
      <div>
        <div className="stat-value" style={valueColor ? { color: valueColor } : undefined}>{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

// ── Inline SVG icons (no extra dep) ──────────────────────────────────────────
const iconProps = (size = 24) => ({
  width: size, height: size, viewBox: '0 0 24 24',
  fill: 'none', stroke: 'currentColor', strokeWidth: 2,
  strokeLinecap: 'round', strokeLinejoin: 'round',
});

const PillIcon     = ({ size }) => <svg {...iconProps(size)}><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/></svg>;
const CalendarIcon = ({ size }) => <svg {...iconProps(size)}><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>;
const PulseIcon    = ({ size }) => <svg {...iconProps(size)}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>;
const BellIcon     = ({ size }) => <svg {...iconProps(size)}><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>;
const MonitorIcon  = ({ size }) => <svg {...iconProps(size)}><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>;
