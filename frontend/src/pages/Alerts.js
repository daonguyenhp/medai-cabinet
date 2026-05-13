import { useState } from 'react';
import toast from 'react-hot-toast';
import { useApp } from '../App';
import { useAlerts } from '../hooks';
import { SEVERITY_CONFIG, ALERT_TYPE_ICONS } from '../constants/alert.constants';
import '../styles/alerts.css';

const VIEW_FILTERS = [
  { key: 'unresolved', label: 'Chưa xử lý' },
  { key: 'resolved',   label: 'Đã xử lý' },
  { key: 'all',        label: 'Tất cả' },
];

export default function Alerts() {
  const { user, setAlertCount } = useApp();
  const [viewFilter, setViewFilter]       = useState('unresolved');
  const [severityFilter, setSeverityFilter] = useState('all');

  const { alerts, loading, resolve, resolveAll, checkMedications } = useAlerts(user.user_id, viewFilter);

  // Keep global badge in sync
  const unresolvedCount = alerts.filter((a) => !a.resolved).length;
  if (typeof setAlertCount === 'function') setAlertCount(unresolvedCount);

  const handleCheckMedications = async () => {
    try {
      await checkMedications();
    } catch (err) {
      toast.error(err.userMessage ?? 'Lỗi kiểm tra thuốc');
    }
  };

  const filtered = severityFilter === 'all'
    ? alerts
    : alerts.filter((a) => a.severity === severityFilter);

  const counts = {
    critical: alerts.filter((a) => a.severity === 'critical' && !a.resolved).length,
    warning:  alerts.filter((a) => a.severity === 'warning'  && !a.resolved).length,
    info:     alerts.filter((a) => a.severity === 'info'     && !a.resolved).length,
  };

  return (
    <div>
      {/* Summary */}
      <div className="alerts-summary">
        <div className="alerts-count-grid">
          {[
            { key: 'critical', label: 'Khẩn cấp', icon: '🔴' },
            { key: 'warning',  label: 'Cảnh báo',  icon: '🟡' },
            { key: 'info',     label: 'Thông tin', icon: '🔵' },
          ].map((s) => (
            <div
              key={s.key}
              className={`alerts-count-card ${severityFilter === s.key ? 'active' : ''}`}
              onClick={() => setSeverityFilter(severityFilter === s.key ? 'all' : s.key)}
            >
              <span className="alerts-count-icon">{s.icon}</span>
              <span className="alerts-count-num">{counts[s.key]}</span>
              <span className="alerts-count-label">{s.label}</span>
            </div>
          ))}
        </div>

        <div className="alerts-actions">
          <button className="btn btn-outline btn-sm" onClick={handleCheckMedications}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
            </svg>
            Kiểm tra thuốc
          </button>
          {counts.critical + counts.warning > 0 && (
            <button className="btn btn-teal btn-sm" onClick={resolveAll}>
              ✓ Xử lý tất cả
            </button>
          )}
        </div>
      </div>

      {/* View filter tabs */}
      <div className="flex items-center gap-3 mb-5">
        {VIEW_FILTERS.map((f) => (
          <button
            key={f.key}
            className={`tab-btn ${viewFilter === f.key ? 'active' : ''}`}
            onClick={() => setViewFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div className="loading-overlay"><div className="spinner" /><span>Đang tải...</span></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔔</div>
          <h3>Không có cảnh báo</h3>
          <p>{viewFilter === 'unresolved' ? 'Tất cả cảnh báo đã được xử lý!' : 'Chưa có cảnh báo nào.'}</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((alert) => {
            const sev      = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.info;
            const typeIcon = ALERT_TYPE_ICONS[alert.type]    ?? '📋';
            return (
              <div
                key={alert.alert_id}
                className={`alert-row ${sev.rowClass} ${alert.resolved ? 'alert-row-resolved' : ''}`}
              >
                <div className="alert-row-icon">{typeIcon}</div>
                <div className="alert-row-content">
                  <div className="alert-row-message">{alert.message}</div>
                  <div className="alert-row-meta">
                    <span className={`badge ${sev.badgeClass}`}>{sev.icon} {sev.label}</span>
                    <span className="text-muted text-sm">
                      {alert.timestamp ? new Date(alert.timestamp).toLocaleString('vi-VN') : ''}
                    </span>
                    {alert.resolved && alert.resolved_at && (
                      <span className="text-muted text-sm">
                        Đã xử lý: {new Date(alert.resolved_at).toLocaleString('vi-VN')}
                      </span>
                    )}
                  </div>
                </div>
                {!alert.resolved ? (
                  <button
                    className="btn btn-outline btn-sm alert-resolve-btn"
                    onClick={() => resolve(alert.alert_id)}
                  >
                    ✓ Xử lý
                  </button>
                ) : (
                  <span className="badge badge-success">✓ Đã xử lý</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
