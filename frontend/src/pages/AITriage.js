import { useState, useEffect } from 'react';
import { useApp } from '../App';
import { triageApi } from '../api';
import AITriageChat from '../components/triage/AITriageChat';
import { DEMO_QUICK_CHECK } from '../constants/triage.constants';
import '../styles/dashboard.css'; /* triage-layout, triage-info-banner */
import '../styles/triage.css';

export default function AITriage() {
  const { user } = useApp();
  const [quickCheck, setQuickCheck] = useState(null);

  useEffect(() => {
    triageApi.quickCheck(user.user_id)
      .then(setQuickCheck)
      .catch(() => setQuickCheck(DEMO_QUICK_CHECK));
  }, [user.user_id]);

  return (
    <div className="ai-triage-page">
      {/* Info banner */}
      <div className="triage-info-banner">
        <div className="triage-info-icon">🤖</div>
        <div>
          <h3 className="triage-info-title">Trợ lý Y tế AI — Powered by Claude</h3>
          <p className="triage-info-desc">
            Mô tả triệu chứng của bạn và AI sẽ đề xuất thuốc phù hợp từ tủ thuốc của bạn.
            Ưu tiên sử dụng thuốc sắp hết hạn để tránh lãng phí.
          </p>
        </div>
        <div className="triage-info-disclaimer">⚕️ Chỉ là tư vấn sơ bộ</div>
      </div>

      <div className="triage-layout">
        {/* Main chat */}
        <div className="card triage-main">
          <div className="card-header">
            <div className="card-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              Tư vấn triệu chứng
            </div>
          </div>
          <div className="card-body">
            <AITriageChat userId={user.user_id} />
          </div>
        </div>

        {/* Sidebar */}
        <div className="triage-sidebar">
          <QuickCheckCard quickCheck={quickCheck} />
          <EmergencyCard />
          <TipsCard />
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function QuickCheckCard({ quickCheck }) {
  if (!quickCheck) return null;
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Cần chú ý
        </div>
      </div>
      <div className="card-body">
        {quickCheck.needs_attention === 0 ? (
          <div className="triage-all-ok">
            <span className="triage-ok-icon">✅</span>
            <p>Tủ thuốc của bạn đang ổn!</p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {quickCheck.expired?.length > 0 && (
              <div>
                <div className="triage-check-title text-danger">⛔ Đã hết hạn ({quickCheck.expired.length})</div>
                {quickCheck.expired.map((m, i) => (
                  <div key={i} className="triage-check-item triage-check-expired">
                    <span className="font-semibold">{m.name}</span>
                    <span className="text-sm text-danger">Quá {m.days_overdue} ngày</span>
                  </div>
                ))}
              </div>
            )}
            {quickCheck.near_expiry?.length > 0 && (
              <div>
                <div className="triage-check-title text-warning">⚠️ Sắp hết hạn ({quickCheck.near_expiry.length})</div>
                {quickCheck.near_expiry.map((m, i) => (
                  <div key={i} className="triage-check-item triage-check-warning">
                    <span className="font-semibold">{m.name}</span>
                    <span className="text-sm">Còn {m.days_remaining} ngày</span>
                  </div>
                ))}
              </div>
            )}
            {quickCheck.low_stock?.length > 0 && (
              <div>
                <div className="triage-check-title">📦 Sắp hết thuốc ({quickCheck.low_stock.length})</div>
                {quickCheck.low_stock.map((m, i) => (
                  <div key={i} className="triage-check-item">
                    <span className="font-semibold">{m.name}</span>
                    <span className="text-sm text-muted">Còn {m.remaining} {m.unit}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function EmergencyCard() {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">🚨 Khẩn cấp</div>
      </div>
      <div className="card-body">
        <div className="emergency-contacts">
          <a href="tel:115" className="emergency-btn emergency-btn-red">
            <span className="emergency-icon">🚑</span>
            <div>
              <div className="emergency-name">Cấp cứu</div>
              <div className="emergency-number">115</div>
            </div>
          </a>
          <a href="tel:1800599920" className="emergency-btn emergency-btn-blue">
            <span className="emergency-icon">☎️</span>
            <div>
              <div className="emergency-name">Đường dây nóng y tế</div>
              <div className="emergency-number">1800 599 920</div>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}

function TipsCard() {
  const tips = [
    'Mô tả triệu chứng càng chi tiết càng tốt',
    'Cho biết thời gian xuất hiện triệu chứng',
    'Đề cập các bệnh nền nếu có',
    'AI ưu tiên thuốc sắp hết hạn để tránh lãng phí',
    'Luôn tham khảo bác sĩ cho triệu chứng nghiêm trọng',
  ];
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">💡 Lưu ý khi dùng AI</div>
      </div>
      <div className="card-body">
        <ul className="triage-tips">
          {tips.map((tip, i) => <li key={i}>{tip}</li>)}
        </ul>
      </div>
    </div>
  );
}
