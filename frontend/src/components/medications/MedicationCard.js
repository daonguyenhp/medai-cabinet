import '../../styles/medications.css';
import MedicationTypeIcon from './MedicationTypeIcon';
import { MEDICATION_TYPE_MAP, EXPIRY_STATUS } from '../../constants/medication.constants';

export default function MedicationCard({ medication, onDispense, onEdit, onDelete }) {
  const typeInfo   = MEDICATION_TYPE_MAP[medication.medication_type] ?? MEDICATION_TYPE_MAP.other;
  const statusInfo = EXPIRY_STATUS[medication.expiry_status]         ?? EXPIRY_STATUS.ok;

  const isExpired    = medication.expiry_status === 'expired';
  const isLowStock   = medication.stock_count <= (medication.low_stock_threshold ?? 5);
  const isOutOfStock = medication.stock_count === 0;

  const stockPercent = Math.min(
    100,
    (medication.stock_count / Math.max(medication.stock_count + 10, 20)) * 100,
  );

  return (
    <div className={`med-card ${isExpired ? 'med-card-expired' : ''}`}>
      {/* ── Header ── */}
      <div className="med-card-header">
        <div className={`med-card-icon med-card-icon-${typeInfo.color}`}>
          <MedicationTypeIcon type={medication.medication_type} />
        </div>
        <div className="med-card-info">
          <h3 className="med-card-name">{medication.name}</h3>
          {medication.dosage_strength && (
            <span className="med-card-strength">{medication.dosage_strength}</span>
          )}
        </div>
        <div className="med-card-badges">
          <span className={`badge ${statusInfo.badgeClass}`}>{statusInfo.label}</span>
          <span className="badge badge-primary">Ngăn {medication.compartment}</span>
        </div>
      </div>

      {/* ── Details ── */}
      <div className="med-card-details">
        <div className="med-detail-row">
          <span className="med-detail-label">Loại thuốc</span>
          <span className="med-detail-value">{typeInfo.label}</span>
        </div>
        <div className="med-detail-row">
          <span className="med-detail-label">Hạn dùng</span>
          <span className={`med-detail-value ${isExpired ? 'text-danger' : medication.expiry_status === 'warning' ? 'text-warning' : ''}`}>
            {medication.effective_expiry_date ?? medication.expiry_date}
            {medication.days_until_expiry !== undefined && (
              <span className="med-days-badge">
                {medication.days_until_expiry < 0
                  ? `Quá hạn ${Math.abs(medication.days_until_expiry)} ngày`
                  : `Còn ${medication.days_until_expiry} ngày`}
              </span>
            )}
          </span>
        </div>
        {medication.manufacturer && (
          <div className="med-detail-row">
            <span className="med-detail-label">Nhà sản xuất</span>
            <span className="med-detail-value">{medication.manufacturer}</span>
          </div>
        )}
      </div>

      {/* ── Stock ── */}
      <div className="med-card-stock">
        <div className="med-stock-header">
          <span className="med-stock-label">Tồn kho</span>
          <span className={`med-stock-value ${isOutOfStock ? 'text-danger' : isLowStock ? 'text-warning' : 'text-success'}`}>
            {isOutOfStock
              ? '⛔ Hết thuốc'
              : isLowStock
              ? `⚠️ ${medication.stock_count} ${medication.unit}`
              : `${medication.stock_count} ${medication.unit}`}
          </span>
        </div>
        <div className="progress">
          <div
            className={`progress-bar ${isOutOfStock ? 'danger' : isLowStock ? 'warning' : 'success'}`}
            style={{ width: `${isOutOfStock ? 0 : stockPercent}%` }}
          />
        </div>
      </div>

      {/* ── Warning ── */}
      {medication.warning_message && (
        <div className={`med-card-warning ${isExpired ? 'alert-danger' : 'alert-warning'}`}>
          {medication.warning_message}
        </div>
      )}

      {/* ── Actions ── */}
      <div className="med-card-actions">
        <button
          className="btn btn-primary btn-sm"
          onClick={() => onDispense?.(medication)}
          disabled={isOutOfStock || isExpired}
          title={isExpired ? 'Thuốc đã hết hạn' : isOutOfStock ? 'Hết thuốc' : 'Lấy thuốc'}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12l7 7 7-7"/>
          </svg>
          Lấy thuốc
        </button>
        <button className="btn btn-outline btn-sm" onClick={() => onEdit?.(medication)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Sửa
        </button>
        <button className="btn btn-ghost btn-sm" onClick={() => onDelete?.(medication)} title="Xóa thuốc">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6M14 11v6"/>
            <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
          </svg>
        </button>
      </div>
    </div>
  );
}
