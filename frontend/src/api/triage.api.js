import client from './client';

const BASE = '/api/v1/ai-triage';

export const triageApi = {
  quickCheck: (userId) =>
    client.get(`${BASE}/quick-check/${userId}`).then((r) => r.data),

  analyze: (userId, symptoms) =>
    client.post(`${BASE}/analyze`, { user_id: userId, symptoms }).then((r) => r.data),

  chat: (userId, message, conversationHistory) =>
    client
      .post(`${BASE}/chat`, { user_id: userId, message, conversation_history: conversationHistory })
      .then((r) => r.data),
};
