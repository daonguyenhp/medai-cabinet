import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { medicationsApi } from '../api';
import { DEMO_MEDICATIONS } from '../constants/medication.constants';

/**
 * Manages the full medication list for a user.
 * Provides CRUD operations and handles demo fallback.
 */
export function useMedications(userId) {
  const [medications, setMedications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    try {
      const data = await medicationsApi.list(userId);
      setMedications(data);
      setError(null);
    } catch {
      setMedications(DEMO_MEDICATIONS);
      setError('demo');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => { fetch(); }, [fetch]);

  const create = useCallback(async (payload) => {
    const data = await medicationsApi.create({ ...payload, user_id: userId });
    toast.success('Đã thêm thuốc mới');
    await fetch();
    return data;
  }, [userId, fetch]);

  const update = useCallback(async (medicationId, payload) => {
    const data = await medicationsApi.update(medicationId, { ...payload, user_id: userId });
    toast.success('Đã cập nhật thuốc');
    await fetch();
    return data;
  }, [userId, fetch]);

  const remove = useCallback(async (medicationId, name) => {
    if (!window.confirm(`Xóa thuốc "${name}"?`)) return false;
    await medicationsApi.remove(medicationId);
    toast.success('Đã xóa thuốc');
    await fetch();
    return true;
  }, [fetch]);

  const dispense = useCallback(async (medicationId, quantity) => {
    const data = await medicationsApi.dispense(medicationId, quantity);
    toast.success(data.message || 'Đã gửi lệnh lấy thuốc');
    await fetch();
    return data;
  }, [fetch]);

  return { medications, loading, error, refetch: fetch, create, update, remove, dispense };
}
