import '../../styles/device.css';
import { WIFI_STRENGTH_LEVELS } from '../../constants/device.constants';

function GaugeBar({ value, min, max, warningMin, warningMax, unit, label }) {
  const percent    = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const isWarning  = value < warningMin || value > warningMax;
  const isCritical = value < warningMin - 5 || value > warningMax + 5;

  return (
    <div className="env-gauge">
      <div className="env-gauge-header">
        <span className="env-gauge-label">{label}</span>
        <span className={`env-gauge-value ${isCritical ? 'text-danger' : isWarning ? 'text-warning' : 'text-success'}`}>
          {value != null ? `${value.toFixed(1)}${unit}` : '--'}
        </span>
      </div>
      <div className="progress">
        <div
          className={`progress-bar ${isCritical ? 'danger' : isWarning ? 'warning' : 'success'}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="env-gauge-range">
        <span>{min}{unit}</span>
        <span className="env-gauge-optimal">Tối ưu: {warningMin}–{warningMax}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}

function getWifiStrength(rssi) {
  if (rssi == null) return { label: 'Không có', colorClass: 'text-muted' };
  return (
    WIFI_STRENGTH_LEVELS.find((l) => rssi >= l.threshold) ??
    WIFI_STRENGTH_LEVELS[WIFI_STRENGTH_LEVELS.length - 1]
  );
}

function formatUptimeShort(seconds) {
  if (!seconds) return '--';
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}n ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export default function EnvironmentMonitor({ telemetry, isOnline }) {
  const temp     = telemetry?.temperature;
  const humidity = telemetry?.humidity;
  const rssi     = telemetry?.wifi_rssi;
  const ssid     = telemetry?.wifi_ssid;
  const ip       = telemetry?.wifi_ip;
  const uptime   = telemetry?.uptime_s ?? telemetry?.uptime_seconds;

  const tempOk     = temp     != null && temp     >= 15 && temp     <= 30;
  const humidityOk = humidity != null && humidity >= 30 && humidity <= 70;
  const wifiInfo   = getWifiStrength(rssi);

  return (
    <div className="env-monitor">
      {/* Status */}
      <div className="env-status-row">
        <div className={`status-dot ${isOnline ? 'online' : 'offline'}`}>
          {isOnline ? 'Thiết bị đang kết nối' : 'Thiết bị ngoại tuyến'}
        </div>
        {telemetry?.timestamp && (
          <span className="env-last-update text-muted text-sm">
            Cập nhật: {new Date(telemetry.timestamp).toLocaleTimeString('vi-VN')}
          </span>
        )}
      </div>

      {/* Gauges */}
      <div className="env-gauges">
        <GaugeBar value={temp}     min={0}  max={50}  warningMin={15} warningMax={30} unit="°C" label="Nhiệt độ" />
        <GaugeBar value={humidity} min={0}  max={100} warningMin={30} warningMax={70} unit="%"  label="Độ ẩm" />
      </div>

      {/* WiFi connection card — replaces the old battery tile */}
      <div className="env-wifi-card">
        <div className="env-wifi-icon" aria-hidden="true">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
            <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
            <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
            <line x1="12" y1="20" x2="12.01" y2="20"/>
          </svg>
        </div>
        <div className="env-wifi-body">
          <div className="env-wifi-row">
            <span className="env-wifi-label">Mạng WiFi</span>
            <span className={`env-wifi-strength ${wifiInfo.colorClass}`}>
              {wifiInfo.label}{rssi != null ? ` · ${rssi} dBm` : ''}
            </span>
          </div>
          <div className="env-wifi-ssid" title={ssid || ''}>
            {ssid ?? (isOnline ? 'Đang kết nối…' : 'Chưa kết nối')}
          </div>
          {ip && <div className="env-wifi-ip">IP: <code>{ip}</code></div>}
        </div>
      </div>

      {/* Compact secondary info — pharmacy-style row */}
      <div className="env-stats">
        <div className="env-stat">
          <div className="env-stat-icon" aria-hidden="true">🌡️</div>
          <div>
            <div className="env-stat-label">Bảo quản</div>
            <div className={`env-stat-value ${tempOk && humidityOk ? 'text-success' : 'text-warning'}`}>
              {temp == null && humidity == null ? '--' : tempOk && humidityOk ? 'Tốt' : 'Cần kiểm tra'}
            </div>
          </div>
        </div>
        <div className="env-stat">
          <div className="env-stat-icon" aria-hidden="true">⏱️</div>
          <div>
            <div className="env-stat-label">Thời gian hoạt động</div>
            <div className="env-stat-value">{formatUptimeShort(uptime)}</div>
          </div>
        </div>
        <div className="env-stat">
          <div className="env-stat-icon" aria-hidden="true">⚙️</div>
          <div>
            <div className="env-stat-label">Firmware</div>
            <div className="env-stat-value text-muted">{telemetry?.firmware_version ?? 'v1.1'}</div>
          </div>
        </div>
      </div>

      {/* Compartment status */}
      {telemetry?.compartment_status?.length > 0 && (
        <div className="env-compartments">
          <div className="env-section-title">Trạng thái ngăn</div>
          <div className="env-compartment-grid">
            {telemetry.compartment_status.map((comp) => (
              <div key={comp.compartment_id} className={`env-compartment ${comp.is_open ? 'env-compartment-open' : ''}`}>
                <div className="env-compartment-num">Ngăn {comp.compartment_id}</div>
                <div className={`env-compartment-status ${comp.is_open ? 'text-warning' : 'text-success'}`}>
                  {comp.is_open ? '🔓 Đang mở' : '🔒 Đóng'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
