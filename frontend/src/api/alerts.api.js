import client from './client';

const BASE = '/api/v1/alerts';

export const alertsApi = {
  list: (userId, resolved) => {
    const params = { user_id: userId };
    if (resolved !== undefined) params.resolved = resolved;
    return client.get(`${BASE}/`, { params }).then((r) => r.data);
  },

  unreadCount: (userId) =>
    client.get(`${BASE}/unread-count`, { params: { user_id: userId } }).then((r) => r.data),

  resolve: (alertId) =>
    client.put(`${BASE}/${alertId}/resolve`).then((r) => r.data),

  resolveAll: (userId) =>
    client.put(`${BASE}/resolve-all`, null, { params: { user_id: userId } }).then((r) => r.data),

  checkMedications: (userId) =>
    client.post(`${BASE}/check-medications`, null, { params: { user_id: userId } }).then((r) => r.data),
};
