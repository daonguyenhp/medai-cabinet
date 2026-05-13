import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { alertsApi } from '../api';
import { DEMO_ALERTS } from '../constants/alert.constants';

/**
 * Manages alerts list, resolution, and unread count for a user.
 */
export function useAlerts(userId, filter = 'unresolved') {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const resolvedParam =
    filter === 'resolved' ? true : filter === 'unresolved' ? false : undefined;

  const fetch = useCallback(async () => {
    try {
      const data = await alertsApi.list(userId, resolvedParam);
      setAlerts(data);
    } catch {
      setAlerts(DEMO_ALERTS);
    } finally {
      setLoading(false);
    }
  }, [userId, resolvedParam]);

  useEffect(() => { fetch(); }, [fetch]);

  const resolve = useCallback(async (alertId) => {
    await alertsApi.resolve(alertId);
    toast.success('Đã xử lý cảnh báo');
    await fetch();
  }, [fetch]);

  const resolveAll = useCallback(async () => {
    if (!window.confirm('Xử lý tất cả cảnh báo chưa giải quyết?')) return;
    const result = await alertsApi.resolveAll(userId);
    toast.success(`Đã xử lý ${result.resolved_count} cảnh báo`);
    await fetch();
  }, [userId, fetch]);

  const checkMedications = useCallback(async () => {
    const result = await alertsApi.checkMedications(userId);
    toast.success(
      `Đã kiểm tra ${result.medications_checked} thuốc, tạo ${result.alerts_created} cảnh báo mới`,
    );
    await fetch();
  }, [userId, fetch]);

  return { alerts, loading, refetch: fetch, resolve, resolveAll, checkMedications };
}
