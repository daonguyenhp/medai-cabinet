import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { schedulesApi } from '../api';
import { DEMO_TODAY_SCHEDULE } from '../constants/schedule.constants';

/**
 * Manages schedules, today's doses, and dose history for a user.
 */
export function useSchedules(userId) {
  const [schedules, setSchedules] = useState([]);
  const [todaySchedule, setTodaySchedule] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [schedData, todayData, histData] = await Promise.all([
        schedulesApi.list(userId),
        schedulesApi.today(userId),
        schedulesApi.history(userId, 20),
      ]);
      setSchedules(schedData);
      setTodaySchedule(todayData);
      setHistory(histData);
    } catch {
      setTodaySchedule(DEMO_TODAY_SCHEDULE);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const create = useCallback(async (payload) => {
    await schedulesApi.create({ ...payload, user_id: userId });
    toast.success('Đã tạo lịch uống thuốc');
    await fetchAll();
  }, [userId, fetchAll]);

  const remove = useCallback(async (scheduleId) => {
    if (!window.confirm('Xóa lịch uống thuốc này?')) return;
    await schedulesApi.remove(scheduleId);
    toast.success('Đã xóa lịch');
    await fetchAll();
  }, [fetchAll]);

  const recordTaken = useCallback(async (dose) => {
    await schedulesApi.recordDose({
      user_id: userId,
      medication_id: dose.medication_id,
      schedule_id: dose.schedule_id,
      scheduled_time: dose.scheduled_datetime,
      taken_time: new Date().toISOString(),
      status: 'taken',
      dosage_count: dose.dosage_count,
    });
    toast.success(`✅ Đã uống ${dose.medication_name}`);
    await fetchAll();
  }, [userId, fetchAll]);

  const recordSkipped = useCallback(async (dose) => {
    await schedulesApi.recordDose({
      user_id: userId,
      medication_id: dose.medication_id,
      schedule_id: dose.schedule_id,
      scheduled_time: dose.scheduled_datetime,
      status: 'skipped',
      dosage_count: dose.dosage_count,
    });
    toast('Đã bỏ qua liều', { icon: '⏭️' });
    await fetchAll();
  }, [userId, fetchAll]);

  return {
    schedules,
    todaySchedule,
    history,
    loading,
    refetch: fetchAll,
    create,
    remove,
    recordTaken,
    recordSkipped,
  };
}
