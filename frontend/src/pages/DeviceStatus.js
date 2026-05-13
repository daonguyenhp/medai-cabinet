import { useApp } from '../App';
import { useDevice } from '../hooks';
import EnvironmentMonitor from '../components/device/EnvironmentMonitor';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import '../styles/device.css';

function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export default function DeviceStatus() {
  const { user } = useApp();
  const deviceId = user.device_id;
  const { device, telemetry, history, loading, sending, wsConnected, isOnline, refetch, sendCommand, dispense } =
    useDevice(user.user_id, deviceId);

  const handleDispense = async (compartment) => {
    const qty = parseInt(window.prompt(`Số lượng cần lấy từ ngăn ${compartment}:`) ?? '0', 10);
    if (!qty || qty < 1) return;
    await dispense(compartment, qty);
  };

  if (!deviceId) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📡</div>
        <h3>Chưa có thiết bị</h3>
        <p>Tài khoản của bạn chưa được liên kết với thiết bị MedAI Cabinet nào.</p>
        <p className="text-muted text-sm mt-4">Liên hệ hỗ trợ để kết nối thiết bị ESP32 của bạn.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="loading-overlay"><div className="spinner" /><span>Đang tải...</span></div>;
  }

  return (
    <div className="device-page">
      {/* ── Device header ── */}
      <div className="device-header-card">
        <div className="device-header-left">
          <div className={`device-status-icon ${isOnline ? 'online' : 'offline'}`}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
          </div>
          <div>
            <h2 className="device-name">{device?.device_name ?? 'MedAI Cabinet'}</h2>
            <div className="device-id-text">ID: {deviceId}</div>
            <div className={`status-dot ${isOnline ? 'online' : 'offline'} mt-2`}>
              {isOnline ? 'Đang kết nối' : 'Ngoại tuyến'}
            </div>
          </div>
        </div>

        <div className="device-header-right">
          <div className="device-meta-grid">
            {[
              { label: 'Firmware', value: telemetry?.firmware_version ?? '--' },
              { label: 'Uptime',   value: telemetry?.uptime_seconds ? formatUptime(telemetry.uptime_seconds) : '--' },
              { label: 'WiFi',     value: telemetry?.wifi_rssi ? `${telemetry.wifi_rssi} dBm` : '--' },
              { label: 'Bộ nhớ',  value: telemetry?.free_heap ? `${Math.round(telemetry.free_heap / 1024)}KB` : '--' },
            ].map((item) => (
              <div key={item.label} className="device-meta-item">
                <span className="device-meta-label">{item.label}</span>
                <span className="device-meta-value">{item.value}</span>
              </div>
            ))}
          </div>
          <div className={`status-dot ${wsConnected ? 'online' : 'offline'} text-sm`}>
            {wsConnected ? 'WebSocket: Kết nối' : 'WebSocket: Ngắt'}
          </div>
        </div>
      </div>

      {/* ── Environment + Compartments ── */}
      <div className="device-grid">
        <div className="card">
          <div className="card-header">
            <div className="card-title">🌡️ Môi trường bảo quản</div>
            <button className="btn btn-ghost btn-sm" onClick={refetch}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
              Làm mới
            </button>
          </div>
          <div className="card-body">
            <EnvironmentMonitor telemetry={telemetry} isOnline={isOnline} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">🗄️ Điều khiển ngăn</div>
          </div>
          <div className="card-body">
            <div className="compartment-grid">
              {[1, 2, 3].map((comp) => {
                const compStatus = telemetry?.compartment_status?.find((c) => c.compartment_id === comp);
                const isOpen     = compStatus?.is_open ?? false;
                return (
                  <div key={comp} className={`compartment-control ${isOpen ? 'compartment-open' : ''}`}>
                    <div className="compartment-num">Ngăn {comp}</div>
                    <div className={`compartment-status-text ${isOpen ? 'text-warning' : 'text-success'}`}>
                      {isOpen ? '🔓 Đang mở' : '🔒 Đóng'}
                    </div>
                    <div className="compartment-btns">
                      <button className="btn btn-primary btn-sm" onClick={() => handleDispense(comp)} disabled={sending || !isOnline}>
                        Lấy thuốc
                      </button>
                      <button className="btn btn-outline btn-sm" onClick={() => sendCommand('unlock', { compartment: comp, duration_seconds: 30 })} disabled={sending || !isOnline}>
                        Mở
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ── Commands ── */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">⚙️ Lệnh thiết bị</div>
        </div>
        <div className="card-body">
          <div className="command-grid">
            {[
              { label: 'Yêu cầu trạng thái', icon: '📊', cmd: 'status_request', variant: '' },
              { label: 'Khóa tất cả ngăn',   icon: '🔒', cmd: 'lock',           variant: '' },
              { label: 'Test còi báo',        icon: '🔔', cmd: 'alert',          variant: 'command-btn-warning', payload: { alert_type: 'buzzer', message: 'Test' } },
              { label: 'Khởi động lại',       icon: '🔄', cmd: 'reboot',         variant: 'command-btn-danger',  confirm: 'Khởi động lại thiết bị?' },
            ].map((item) => (
              <button
                key={item.cmd}
                className={`command-btn ${item.variant}`}
                disabled={sending || !isOnline}
                onClick={() => {
                  if (item.confirm && !window.confirm(item.confirm)) return;
                  sendCommand(item.cmd, item.payload ?? {});
                }}
              >
                <span className="command-icon">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── 24h chart ── */}
      {history.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">📈 Lịch sử 24 giờ</div>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <Tooltip contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 13 }} />
                <Legend />
                <Line type="monotone" dataKey="temp"     stroke="var(--color-danger)"        strokeWidth={2} dot={false} name="Nhiệt độ (°C)" />
                <Line type="monotone" dataKey="humidity" stroke="var(--color-teal)"           strokeWidth={2} dot={false} name="Độ ẩm (%)" />
                <Line type="monotone" dataKey="battery"  stroke="var(--color-success-light)"  strokeWidth={2} dot={false} name="Pin (%)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
