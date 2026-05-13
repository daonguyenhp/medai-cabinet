import React, { createContext, useContext, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Dashboard from './pages/Dashboard';
import Medications from './pages/Medications';
import Schedule from './pages/Schedule';
import AITriage from './pages/AITriage';
import Alerts from './pages/Alerts';
import DeviceStatus from './pages/DeviceStatus';

// ─── App Context ──────────────────────────────────────────────────────────────
export const AppContext = createContext(null);

export function useApp() {
  return useContext(AppContext);
}

// Demo user - replace with Cognito auth in production
const DEMO_USER = {
  user_id: 'demo-user-001',
  name: 'Nguyễn Văn An',
  age: 68,
  phone: '0901234567',
  caregiver_name: 'Nguyễn Thị Bình',
  caregiver_phone: '0907654321',
  device_id: 'medai-esp32-001',
  role: 'patient',
  language: 'vi',
};

// ─── App Component ────────────────────────────────────────────────────────────
export default function App() {
  const [user] = useState(DEMO_USER);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [alertCount, setAlertCount] = useState(0);

  const contextValue = {
    user,
    sidebarOpen,
    setSidebarOpen,
    alertCount,
    setAlertCount,
  };

  return (
    <AppContext.Provider value={contextValue}>
      <BrowserRouter>
        <div className="app-layout">
          <Sidebar />
          <div className="main-content">
            <Header />
            <main className="page-content">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/medications" element={<Medications />} />
                <Route path="/schedule" element={<Schedule />} />
                <Route path="/ai-triage" element={<AITriage />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/device" element={<DeviceStatus />} />
              </Routes>
            </main>
          </div>
        </div>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              fontFamily: 'var(--font-family)',
              fontSize: 'var(--font-size-base)',
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-lg)',
            },
            success: { iconTheme: { primary: '#2E7D32', secondary: '#fff' } },
            error:   { iconTheme: { primary: '#D32F2F', secondary: '#fff' } },
          }}
        />
      </BrowserRouter>
    </AppContext.Provider>
  );
}
