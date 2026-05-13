import client from './client';

const BASE = '/api/v1/dashboard';

export const dashboardApi = {
  summary: (userId) =>
    client.get(`${BASE}/summary`, { params: { user_id: userId } }).then((r) => r.data),

  adherence: (userId, days = 7) =>
    client.get(`${BASE}/adherence`, { params: { user_id: userId, days } }).then((r) => r.data),
};
