import '../../styles/schedule.css';
import { DOSE_STATUS } from '../../constants/schedule.constants';

export default function DoseAlert({ dose, onTake, onSkip }) {
  const config    = DOSE_STATUS[dose.status] ?? DOSE_STATUS.pending;
  const isPending = dose.status === 'pending';

  return (
    <div className={`dose-alert dose-${dose.status} ${dose.is_overdue ? 'dose-overdue' : ''}`}>
      <div className="dose-alert-icon">{config.icon}</div>

      <div className="dose-alert-content">
        <div className="dose-alert-name">{dose.medication_name}</div>
        <div className="dose-alert-meta">
          <span className="dose-time">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
            {dose.scheduled_time}
          </span>
          <span className="dose-quantity">{dose.dosage_count} {dose.unit}</span>
          {dose.compartment && (
            <span className="dose-compartment">Ngăn {dose.compartment}</span>
          )}
        </div>
        {dose.instructions && (
          <div className="dose-instructions">{dose.instructions}</div>
        )}
        {dose.minutes_until_dose > 0 && (
          <div className="dose-countdown">
            Còn{' '}
            {dose.minutes_until_dose < 60
              ? `${dose.minutes_until_dose} phút`
              : `${Math.floor(dose.minutes_until_dose / 60)} giờ ${dose.minutes_until_dose % 60} phút`}
          </div>
        )}
      </div>

      <div className="dose-alert-right">
        <span className={`badge ${config.badgeClass}`}>{config.label}</span>
        {isPending && (
          <div className="dose-alert-actions">
            <button className="btn btn-teal btn-sm" onClick={() => onTake?.(dose)}>Đã uống</button>
            <button className="btn btn-ghost btn-sm" onClick={() => onSkip?.(dose)}>Bỏ qua</button>
          </div>
        )}
      </div>
    </div>
  );
}
