import { useState, useEffect, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';
import { devicesApi } from '../api';
import {
  DEMO_DEVICE,
  DEMO_TELEMETRY,
  DEMO_TELEMETRY_HISTORY,
} from '../constants/device.constants';

/**
 * Manages device state, telemetry, history, WebSocket, and commands.
 */
export function useDevice(userId, deviceId) {
  const [device, setDevice] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // ── REST polling ────────────────────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    if (!deviceId) { setLoading(false); return; }
    try {
      const [devices, tel, hist] = await Promise.all([
        devicesApi.list(userId),
        devicesApi.latestTelemetry(deviceId),
        devicesApi.telemetryHistory(deviceId, 24),
      ]);
      setDevice(devices[0] ?? null);
      setTelemetry(tel);
      setHistory(
        [...hist]
          .reverse()
          .map((t) => ({
            time: new Date(t.timestamp).toLocaleTimeString('vi-VN', {
              hour: '2-digit',
              minute: '2-digit',
            }),
            temp: t.temperature,
            humidity: t.humidity,
          })),
      );
    } catch {
      setDevice(DEMO_DEVICE);
      setTelemetry(DEMO_TELEMETRY);
      setHistory(DEMO_TELEMETRY_HISTORY);
    } finally {
      setLoading(false);
    }
  }, [userId, deviceId]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // ── WebSocket for real-time telemetry ───────────────────────────────────────
  useEffect(() => {
    if (!deviceId) return;
    const wsUrl = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/api/v1/devices/${deviceId}/ws`;
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onerror = () => setWsConnected(false);
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'telemetry') setTelemetry(msg.data);
        } catch { /* ignore malformed frames */ }
      };

      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30_000);

      return () => {
        clearInterval(ping);
        ws.close();
      };
    } catch { /* WebSocket unavailable in demo */ }
  }, [deviceId]);

  // ── Commands ────────────────────────────────────────────────────────────────
  const sendCommand = useCallback(async (commandType, payload = {}) => {
    setSending(true);
    try {
      await devicesApi.sendCommand(deviceId, commandType, payload);
      toast.success(`Đã gửi lệnh: ${commandType}`);
    } catch {
      toast.error('Không thể gửi lệnh đến thiết bị');
    } finally {
      setSending(false);
    }
  }, [deviceId]);

  const dispense = useCallback(async (compartment, quantity) => {
    setSending(true);
    try {
      await devicesApi.dispense(deviceId, compartment, quantity);
      toast.success(`Đang lấy ${quantity} viên từ ngăn ${compartment}`);
    } catch {
      toast.error('Không thể gửi lệnh lấy thuốc');
    } finally {
      setSending(false);
    }
  }, [deviceId]);

  return {
    device,
    telemetry,
    history,
    loading,
    sending,
    wsConnected,
    isOnline: device?.status === 'online',
    refetch: fetchData,
    sendCommand,
    dispense,
  };
}
