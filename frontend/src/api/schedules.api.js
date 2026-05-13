import client from './client';

const BASE = '/api/v1/schedules';

export const schedulesApi = {
  list: (userId) =>
    client.get(`${BASE}/`, { params: { user_id: userId } }).then((r) => r.data),

  today: (userId) =>
    client.get(`${BASE}/today`, { params: { user_id: userId } }).then((r) => r.data),

  create: (payload) =>
    client.post(`${BASE}/`, payload).then((r) => r.data),

  remove: (scheduleId) =>
    client.delete(`${BASE}/${scheduleId}`).then((r) => r.data),

  recordDose: (payload) =>
    client.post(`${BASE}/dose-history`, payload).then((r) => r.data),

  history: (userId, limit = 20) =>
    client
      .get(`${BASE}/dose-history/list`, { params: { user_id: userId, limit } })
      .then((r) => r.data),
};
