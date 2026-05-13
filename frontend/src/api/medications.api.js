import client from './client';

const BASE = '/api/v1/medications';

export const medicationsApi = {
  list: (userId) =>
    client.get(`${BASE}/`, { params: { user_id: userId } }).then((r) => r.data),

  create: (payload) =>
    client.post(`${BASE}/`, payload).then((r) => r.data),

  update: (medicationId, payload) =>
    client.put(`${BASE}/${medicationId}`, payload).then((r) => r.data),

  remove: (medicationId) =>
    client.delete(`${BASE}/${medicationId}`).then((r) => r.data),

  dispense: (medicationId, quantity) =>
    client
      .post(`${BASE}/${medicationId}/dispense`, { medication_id: medicationId, quantity })
      .then((r) => r.data),
};
