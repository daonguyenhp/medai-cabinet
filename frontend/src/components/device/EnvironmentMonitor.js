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
  if (!rssi) return { label: 'Không có', colorClass: 'text-muted' };
  return (
    WIFI_STRENGTH_LEVELS.find((l) => rssi >= l.threshold) ??
    WIFI_STRENGTH_LEVELS[WIFI_STRENGTH_LEVELS.length - 1]
  );
}

export default function EnvironmentMonitor({ telemetry, isOnline }) {
  const temp     = telemetry?.temperature;
  const humidity = telemetry?.humidity;
  const battery  = telemetry?.battery_level;
  const rssi     = telemetry?.wifi_rssi;

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

      {/* Quick stats */}
      <div className="env-stats">
        <div className="env-stat">
          <div className="env-stat-icon">🔋</div>
          <div>
            <div className="env-stat-label">Pin</div>
            <div className={`env-stat-value ${battery <= 20 ? 'text-danger' : battery <= 50 ? 'text-warning' : 'text-success'}`}>
              {battery != null ? `${battery}%` : '--'}
            </div>
          </div>
        </div>
        <div className="env-stat">
          <div className="env-stat-icon">📶</div>
          <div>
            <div className="env-stat-label">WiFi</div>
            <div className={`env-stat-value ${wifiInfo.colorClass}`}>{wifiInfo.label}</div>
          </div>
        </div>
        <div className="env-stat">
          <div className="env-stat-icon">🌡️</div>
          <div>
            <div className="env-stat-label">Bảo quản</div>
            <div className={`env-stat-value ${tempOk && humidityOk ? 'text-success' : 'text-warning'}`}>
              {tempOk && humidityOk ? 'Tốt' : 'Cần kiểm tra'}
            </div>
          </div>
        </div>
        <div className="env-stat">
          <div className="env-stat-icon">⚙️</div>
          <div>
            <div className="env-stat-label">Firmware</div>
            <div className="env-stat-value text-muted">{telemetry?.firmware_version ?? '--'}</div>
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
