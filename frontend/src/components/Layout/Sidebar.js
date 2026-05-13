import React from 'react';
import { NavLink } from 'react-router-dom';
import { useApp } from '../../App';

const NAV_ITEMS = [
  {
    path: '/dashboard',
    label: 'Tổng Quan',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
  },
  {
    path: '/medications',
    label: 'Tủ Thuốc',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
      </svg>
    ),
  },
  {
    path: '/schedule',
    label: 'Lịch Uống Thuốc',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
        <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/>
      </svg>
    ),
  },
  {
    path: '/ai-triage',
    label: 'Tư Vấn AI',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 8v4l3 3"/>
        <path d="M18 2v4h4"/>
      </svg>
    ),
    badge: 'AI',
  },
  {
    path: '/alerts',
    label: 'Cảnh Báo',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
    ),
    alertKey: true,
  },
  {
    path: '/device',
    label: 'Thiết Bị',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
      </svg>
    ),
  },
];

export default function Sidebar() {
  const { user, alertCount } = useApp();

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
          </svg>
        </div>
        <div>
          <div className="sidebar-logo-title">MedAI Cabinet</div>
          <div className="sidebar-logo-sub">Tủ Thuốc Thông Minh</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="sidebar-nav-label">Menu chính</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar-nav-item ${isActive ? 'active' : ''}`
            }
          >
            <span className="sidebar-nav-icon">{item.icon}</span>
            <span className="sidebar-nav-text">{item.label}</span>
            {item.badge && (
              <span className="sidebar-badge sidebar-badge-ai">{item.badge}</span>
            )}
            {item.alertKey && alertCount > 0 && (
              <span className="sidebar-badge sidebar-badge-alert">{alertCount}</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User info */}
      <div className="sidebar-user">
        <div className="sidebar-user-avatar">
          {user?.name?.charAt(0) || 'U'}
        </div>
        <div className="sidebar-user-info">
          <div className="sidebar-user-name">{user?.name}</div>
          <div className="sidebar-user-role">
            {user?.age ? `${user.age} tuổi` : 'Bệnh nhân'}
          </div>
        </div>
      </div>

      <style>{`
        .sidebar {
          position: fixed;
          top: 0;
          left: 0;
          width: var(--sidebar-width);
          height: 100vh;
          background: var(--color-primary);
          display: flex;
          flex-direction: column;
          z-index: 100;
          overflow-y: auto;
          overflow-x: hidden;
        }

        .sidebar-logo {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-5) var(--space-5);
          border-bottom: 1px solid rgba(255,255,255,0.1);
          min-height: var(--header-height);
        }

        .sidebar-logo-icon {
          width: 44px;
          height: 44px;
          background: rgba(255,255,255,0.15);
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          flex-shrink: 0;
        }

        .sidebar-logo-title {
          font-family: 'Nunito', sans-serif;
          font-size: var(--font-size-md);
          font-weight: 800;
          color: white;
          line-height: 1.2;
        }

        .sidebar-logo-sub {
          font-size: var(--font-size-xs);
          color: rgba(255,255,255,0.6);
          font-weight: 500;
        }

        .sidebar-nav {
          flex: 1;
          padding: var(--space-5) var(--space-3);
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
        }

        .sidebar-nav-label {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: rgba(255,255,255,0.4);
          padding: 0 var(--space-3);
          margin-bottom: var(--space-2);
        }

        .sidebar-nav-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-3);
          border-radius: var(--radius-md);
          color: rgba(255,255,255,0.75);
          font-size: var(--font-size-base);
          font-weight: 500;
          text-decoration: none;
          transition: all var(--transition-fast);
          min-height: var(--touch-target);
          position: relative;
        }

        .sidebar-nav-item:hover {
          background: rgba(255,255,255,0.1);
          color: white;
          text-decoration: none;
        }

        .sidebar-nav-item.active {
          background: rgba(255,255,255,0.18);
          color: white;
          font-weight: 700;
          box-shadow: inset 3px 0 0 rgba(255,255,255,0.8);
        }

        .sidebar-nav-icon {
          flex-shrink: 0;
          display: flex;
          align-items: center;
        }

        .sidebar-nav-text { flex: 1; }

        .sidebar-badge {
          font-size: 11px;
          font-weight: 700;
          padding: 2px 7px;
          border-radius: var(--radius-full);
          line-height: 1.4;
        }

        .sidebar-badge-ai {
          background: var(--color-teal);
          color: white;
        }

        .sidebar-badge-alert {
          background: var(--color-danger);
          color: white;
          min-width: 20px;
          text-align: center;
        }

        .sidebar-user {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-4) var(--space-5);
          border-top: 1px solid rgba(255,255,255,0.1);
          margin-top: auto;
        }

        .sidebar-user-avatar {
          width: 40px;
          height: 40px;
          background: rgba(255,255,255,0.2);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: var(--font-size-lg);
          font-weight: 700;
          color: white;
          flex-shrink: 0;
        }

        .sidebar-user-name {
          font-size: var(--font-size-sm);
          font-weight: 600;
          color: white;
          line-height: 1.3;
        }

        .sidebar-user-role {
          font-size: var(--font-size-xs);
          color: rgba(255,255,255,0.55);
        }
      `}</style>
    </aside>
  );
}
