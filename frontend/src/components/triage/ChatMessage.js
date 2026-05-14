import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import '../../styles/triage.css';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`chat-message ${isUser ? 'chat-user' : 'chat-ai'}`}>
      {!isUser && (
        <div className="chat-avatar chat-avatar-ai">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 8v4l3 3"/><path d="M18 2v4h4"/>
          </svg>
        </div>
      )}
      <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-ai'}`}>
        {isUser ? (
          message.content
        ) : (
          <div className="chat-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content || ''}
            </ReactMarkdown>
          </div>
        )}
      </div>
      {isUser && <div className="chat-avatar chat-avatar-user">Bạn</div>}
    </div>
  );
}
