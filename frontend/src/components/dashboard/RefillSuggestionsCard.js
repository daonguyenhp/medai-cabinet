import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { triageApi } from '../../api';

/**
 * Smart shopping list powered by AI.
 * Pulls /api/v1/ai-triage/refill-suggestions/{userId} on mount.
 */
export default function RefillSuggestionsCard({ userId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await triageApi.refillSuggestions(userId);
      setData(res);
    } catch (err) {
      setError(err.userMessage ?? 'Không tải được gợi ý');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="card refill-card">
      <div className="card-header">
        <div className="card-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
          </svg>
          Gợi ý mua thêm thuốc <span className="badge badge-primary refill-ai-badge">AI</span>
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={load}
          disabled={loading}
          title="Làm mới"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
        </button>
      </div>

      <div className="card-body">
        {loading ? (
          <div className="refill-loading">
            <div className="spinner" />
            <span>AI đang phân tích tủ thuốc...</span>
          </div>
        ) : error ? (
          <div className="alert alert-danger">{error}</div>
        ) : !data?.needs_refill ? (
          <div className="refill-empty">
            <span style={{ fontSize: 32 }}>✅</span>
            <p>{data?.summary ?? 'Tủ thuốc đầy đủ — chưa cần mua thêm.'}</p>
          </div>
        ) : (
          <>
            <p className="refill-summary">{data.summary}</p>
            <ul className="refill-list">
              {data.candidates.map((c, i) => (
                <li key={i} className="refill-item">
                  <div className="refill-item-main">
                    <span className="refill-item-name">{c.name}</span>
                    <span className="refill-item-stock">
                      Còn {c.stock_count} {c.unit}
                      {c.expiry_status === 'expired' && (
                        <span className="badge badge-danger" style={{ marginLeft: 6 }}>Hết hạn</span>
                      )}
                      {c.expiry_status === 'critical' && (
                        <span className="badge badge-warning" style={{ marginLeft: 6 }}>
                          Sắp hết hạn ({c.days_until_expiry}d)
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="refill-item-meta">
                    {c.estimated_days_until_empty != null && (
                      <span>⏳ Hết trong ~{c.estimated_days_until_empty} ngày</span>
                    )}
                    {c.weekly_usage > 0 && (
                      <span>📊 ~{c.weekly_usage} {c.unit}/tuần</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
            <Link to="/medications" className="btn btn-outline btn-sm refill-link">
              Quản lý thuốc →
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
