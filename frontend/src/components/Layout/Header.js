import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useApp } from '../../App';
import axios from 'axios';

const PAGE_TITLES = {
  '/dashboard':   { title: 'Tổng Quan',        subtitle: 'Xem tình trạng tủ thuốc của bạn' },
  '/medications': { title: 'Tủ Thuốc',          subtitle: 'Quản lý danh sách thuốc' },
  '/schedule':    { title: 'Lịch Uống Thuốc',   subtitle: 'Theo dõi và đặt lịch uống thuốc' },
  '/ai-triage':   { title: 'Tư Vấn AI',         subtitle: 'Phân tích triệu chứng với trí tuệ nhân tạo' },
  '/alerts':      { title: 'Cảnh Báo',          subtitle: 'Thông báo và cảnh báo quan trọng' },
  '/device':      { title: 'Thiết Bị',          subtitle: 'Trạng thái tủ thuốc ESP32' },
};

export default function Header() {
  const { user, alertCount, setAlertCount } = useApp();
  const location = useLocation();
  const [currentTime, setCurrentTime] = useState(new Date());
  const pageInfo = PAGE_TITLES[location.pathname] || { title: 'MedAI Cabinet', subtitle: '' };

  // Update clock every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  // Poll alert count every 30 seconds
  useEffect(() => {
    const fetchAlertCount = async () => {
      try {
        const res = await axios.get(`/api/v1/alerts/unread-count?user_id=${user.user_id}`);
        setAlertCount(res.data.total || 0);
      } catch {
        // Silently fail
      }
    };
    fetchAlertCount();
    const interval = setInterval(fetchAlertCount, 30000);
    return () => clearInterval(interval);
  }, [user.user_id, setAlertCount]);

  const timeStr = currentTime.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  const dateStr = currentTime.toLocaleDateString('vi-VN', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  });

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="header-page-info">
          <h1 className="header-title">{pageInfo.title}</h1>
          <p className="header-subtitle">{pageInfo.subtitle}</p>
        </div>
      </div>

      <div className="header-right">
        {/* Date/Time */}
        <div className="header-datetime">
          <div className="header-time">{timeStr}</div>
          <div className="header-date">{dateStr}</div>
        </div>

        {/* Alert bell */}
        <Link to="/alerts" className="header-alert-btn" aria-label="Cảnh báo">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          {alertCount > 0 && (
            <span className="header-alert-badge">{alertCount > 99 ? '99+' : alertCount}</span>
          )}
        </Link>

        {/* User avatar */}
        <div className="header-user">
          <div className="header-user-avatar">{user?.name?.charAt(0) || 'U'}</div>
          <div className="header-user-info">
            <div className="header-user-name">{user?.name}</div>
            <div className="header-user-sub">Bệnh nhân</div>
          </div>
        </div>
      </div>

      <style>{`
        .app-header {
          position: fixed;
          top: 0;
          left: var(--sidebar-width);
          right: 0;
          height: var(--header-height);
          background: var(--color-surface);
          border-bottom: 1px solid var(--color-border-light);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 var(--space-6);
          z-index: 90;
          box-shadow: var(--shadow-sm);
        }

        .header-left { display: flex; align-items: center; gap: var(--space-4); }

        .header-title {
          font-size: var(--font-size-xl);
          font-weight: 800;
          color: var(--color-primary);
          line-height: 1.2;
        }

        .header-subtitle {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
          margin: 0;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: var(--space-5);
        }

        .header-datetime {
          text-align: right;
        }

        .header-time {
          font-size: var(--font-size-xl);
          font-weight: 700;
          color: var(--color-primary);
          line-height: 1.2;
          font-family: 'Nunito', sans-serif;
        }

        .header-date {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          text-transform: capitalize;
        }

        .header-alert-btn {
          position: relative;
          width: var(--touch-target);
          height: var(--touch-target);
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          background: var(--color-bg);
          border: 1px solid var(--color-border-light);
          transition: all var(--transition-fast);
          text-decoration: none;
        }

        .header-alert-btn:hover {
          background: var(--color-primary-50);
          color: var(--color-primary);
          text-decoration: none;
        }

        .header-alert-badge {
          position: absolute;
          top: 6px;
          right: 6px;
          min-width: 18px;
          height: 18px;
          background: var(--color-danger);
          color: white;
          font-size: 10px;
          font-weight: 700;
          border-radius: var(--radius-full);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0 4px;
          border: 2px solid white;
        }

        .header-user {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-2) var(--space-3);
          border-radius: var(--radius-md);
          border: 1px solid var(--color-border-light);
          background: var(--color-bg);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .header-user:hover { background: var(--color-primary-50); }

        .header-user-avatar {
          width: 36px;
          height: 36px;
          background: var(--color-primary);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: var(--font-size-md);
          font-weight: 700;
          color: white;
          flex-shrink: 0;
        }

        .header-user-name {
          font-size: var(--font-size-sm);
          font-weight: 600;
          color: var(--color-text-primary);
          line-height: 1.3;
        }

        .header-user-sub {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        @media (max-width: 768px) {
          .app-header { left: 0; padding: 0 var(--space-4); }
          .header-datetime { display: none; }
          .header-user-info { display: none; }
        }
      `}</style>
    </header>
  );
}
