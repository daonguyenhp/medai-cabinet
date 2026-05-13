import { useState, useEffect, useCallback } from 'react';
import { dashboardApi, devicesApi } from '../api';
import { schedulesApi } from '../api';
import { DEMO_DASHBOARD } from '../constants/device.constants';
import { DEMO_TODAY_SCHEDULE } from '../constants/schedule.constants';

/**
 * Aggregates dashboard summary, today's schedule, and telemetry history.
 */
export function useDashboard(userId) {
  const [dashboard, setDashboard] = useState(null);
  const [todaySchedule, setTodaySchedule] = useState([]);
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const [dash, today] = await Promise.all([
        dashboardApi.summary(userId),
        schedulesApi.today(userId),
      ]);
      setDashboard(dash);
      setTodaySchedule(today);

      if (dash?.device?.device_id) {
        try {
          const hist = await devicesApi.telemetryHistory(dash.device.device_id, 6);
          setTelemetryHistory(
            hist.map((t) => ({
              time: new Date(t.timestamp).toLocaleTimeString('vi-VN', {
                hour: '2-digit',
                minute: '2-digit',
              }),
              temp: t.temperature,
              humidity: t.humidity,
            })),
          );
        } catch { /* telemetry optional */ }
      }
    } catch {
      setDashboard(DEMO_DASHBOARD);
      setTodaySchedule(DEMO_TODAY_SCHEDULE);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, 30_000);
    return () => clearInterval(interval);
  }, [fetch]);

  return { dashboard, todaySchedule, telemetryHistory, loading, refetch: fetch };
}
