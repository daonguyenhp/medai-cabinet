import { useState, useRef, useEffect } from 'react';
import toast from 'react-hot-toast';
import { triageApi } from '../../api';
import { QUICK_SYMPTOMS, INITIAL_AI_MESSAGE } from '../../constants/triage.constants';
import ChatMessage from './ChatMessage';
import TriageResult from './TriageResult';
import '../../styles/triage.css';

export default function AITriageChat({ userId }) {
  const [symptoms, setSymptoms]       = useState('');
  const [messages, setMessages]       = useState([INITIAL_AI_MESSAGE]);
  const [triageResult, setTriageResult] = useState(null);
  const [loading, setLoading]         = useState(false);
  const [chatInput, setChatInput]     = useState('');
  const [showChat, setShowChat]       = useState(false);
  const messagesEndRef                = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleAnalyze = async () => {
    if (!symptoms.trim()) {
      toast.error('Vui lòng mô tả triệu chứng của bạn');
      return;
    }
    setLoading(true);
    setTriageResult(null);
    try {
      const result = await triageApi.analyze(userId, symptoms.trim());
      setTriageResult(result);
      setShowChat(true);
      setMessages((prev) => [
        ...prev,
        { role: 'user',      content: symptoms },
        { role: 'assistant', content: result.assessment ?? 'Đã phân tích xong. Xem kết quả bên dưới.' },
      ]);
    } catch {
      toast.error('Không thể kết nối AI. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const data    = await triageApi.chat(userId, userMsg, history);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
    } catch {
      toast.error('Lỗi kết nối AI');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-triage-chat">
      {/* ── Symptom input ── */}
      <div className="triage-input-section">
        <label className="form-label">Mô tả triệu chứng của bạn</label>
        <textarea
          className="form-control triage-textarea"
          placeholder="Ví dụ: Tôi bị đau đầu từ sáng, kèm theo chóng mặt và buồn nôn nhẹ..."
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          rows={4}
        />

        <div className="triage-quick-symptoms">
          <span className="triage-quick-label">Chọn nhanh:</span>
          <div className="triage-quick-grid">
            {QUICK_SYMPTOMS.map((s) => (
              <button
                key={s}
                className={`triage-quick-btn ${symptoms === s ? 'active' : ''}`}
                onClick={() => setSymptoms(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <button
          className="btn btn-primary btn-lg w-full"
          onClick={handleAnalyze}
          disabled={loading || !symptoms.trim()}
        >
          {loading ? (
            <><div className="spinner" style={{ width: 20, height: 20, borderWidth: 3 }} /> Đang phân tích...</>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 8v4l3 3"/><path d="M18 2v4h4"/>
              </svg>
              Phân tích với AI
            </>
          )}
        </button>
      </div>

      {/* ── Result ── */}
      {triageResult && <TriageResult result={triageResult} />}

      {/* ── Follow-up chat ── */}
      {showChat && (
        <div className="triage-chat-section">
          <div className="triage-chat-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Hỏi thêm AI
          </div>
          <div className="chat-messages">
            {messages.map((msg, i) => <ChatMessage key={i} message={msg} />)}
            {loading && (
              <div className="chat-message chat-ai">
                <div className="chat-avatar chat-avatar-ai">AI</div>
                <div className="chat-bubble chat-bubble-ai chat-typing">
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input-row">
            <input
              className="form-control"
              placeholder="Hỏi thêm về triệu chứng hoặc thuốc..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleChatSend()}
              disabled={loading}
            />
            <button
              className="btn btn-primary btn-icon"
              onClick={handleChatSend}
              disabled={loading || !chatInput.trim()}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
