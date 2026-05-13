import client from './client';

const BASE = '/api/v1/devices';

export const devicesApi = {
  list: (userId) =>
    client.get(`${BASE}/`, { params: { user_id: userId } }).then((r) => r.data),

  latestTelemetry: (deviceId) =>
    client.get(`${BASE}/${deviceId}/telemetry`).then((r) => r.data),

  telemetryHistory: (deviceId, hours = 24) =>
    client.get(`${BASE}/${deviceId}/telemetry/history`, { params: { hours } }).then((r) => r.data),

  sendCommand: (deviceId, commandType, payload = {}) =>
    client
      .post(`${BASE}/${deviceId}/command`, { device_id: deviceId, command_type: commandType, payload })
      .then((r) => r.data),

  dispense: (deviceId, compartment, quantity, medicationId = 'manual') =>
    client
      .post(`${BASE}/${deviceId}/dispense`, { compartment, quantity, medication_id: medicationId })
      .then((r) => r.data),
};
