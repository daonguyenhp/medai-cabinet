import '../../styles/triage.css';
import { SEVERITY_DISPLAY } from '../../constants/triage.constants';

export default function TriageResult({ result }) {
  if (!result) return null;

  const sev = SEVERITY_DISPLAY[result.severity] ?? SEVERITY_DISPLAY.unknown;

  return (
    <div className="triage-result">
      {/* Header */}
      <div className="triage-result-header">
        <div className="triage-result-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
          </svg>
          Kết quả phân tích AI
        </div>
        <span className={`badge ${sev.badgeClass}`}>{sev.icon} Mức độ: {sev.label}</span>
      </div>

      {/* Assessment */}
      <div className="triage-assessment">{result.assessment}</div>

      {/* Recommendations */}
      {result.recommendations?.length > 0 && (
        <div className="triage-section">
          <div className="triage-section-title">💊 Thuốc đề xuất từ tủ của bạn</div>
          {result.recommendations.map((rec, i) => (
            <div key={i} className={`triage-rec ${rec.near_expiry ? 'triage-rec-expiry' : ''}`}>
              <div className="triage-rec-header">
                <span className="triage-rec-name">{rec.medication_name}</span>
                <div className="triage-rec-badges">
                  <span className="badge badge-primary">Ưu tiên {rec.priority}</span>
                  {rec.near_expiry && <span className="badge badge-warning">⚠️ Dùng trước</span>}
                </div>
              </div>
              <div className="triage-rec-detail">
                <span>📋 {rec.reason}</span>
                {rec.dosage && <span>💊 Liều: {rec.dosage}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Warnings */}
      {result.warnings?.length > 0 && (
        <div className="triage-section">
          <div className="triage-section-title">⚠️ Lưu ý quan trọng</div>
          {result.warnings.map((w, i) => (
            <div key={i} className="alert alert-warning">{w}</div>
          ))}
        </div>
      )}

      {/* See doctor */}
      {result.see_doctor && (
        <div className="alert alert-danger triage-doctor-alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <div>
            <strong>Cần gặp bác sĩ</strong>
            {result.see_doctor_reason && (
              <p style={{ margin: '4px 0 0' }}>{result.see_doctor_reason}</p>
            )}
          </div>
        </div>
      )}

      {/* General advice */}
      {result.general_advice && (
        <div className="triage-advice">
          <div className="triage-section-title">💡 Lời khuyên chung</div>
          <p>{result.general_advice}</p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="triage-disclaimer">
        ⚕️ <em>Đây chỉ là tư vấn sơ bộ từ AI, không thay thế ý kiến bác sĩ. Trong trường hợp khẩn cấp, gọi 115.</em>
      </div>
    </div>
  );
}
