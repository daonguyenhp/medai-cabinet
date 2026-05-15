import { useState } from 'react';
import toast from 'react-hot-toast';
import { alertsApi } from '../../api';

export default function CaregiverSubscribeCard() {
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [pending, setPending] = useState(null); // last successfully subscribed email

  const isValidEmail = (s) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValidEmail(email)) {
      toast.error('Email không hợp lệ');
      return;
    }
    setSubmitting(true);
    try {
      const res = await alertsApi.subscribeCaregiver(email);
      toast.success('Đã gửi email xác nhận');
      setPending({ email, ...res });
      setEmail('');
    } catch (err) {
      toast.error(err.userMessage ?? 'Không gửi được. Thử lại sau.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card caregiver-card">
      <div className="card-header">
        <div className="card-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
          Người chăm sóc nhận thông báo
        </div>
      </div>
      <div className="card-body">
        <p className="text-muted" style={{ marginBottom: 12 }}>
          Đăng ký email người chăm sóc để nhận cảnh báo tự động khi bệnh nhân
          <strong> bỏ lỡ liều thuốc</strong> hoặc tủ thuốc gặp sự cố.
        </p>

        <form onSubmit={handleSubmit} className="caregiver-form">
          <input
            type="email"
            className="form-control"
            placeholder="caregiver@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={submitting}
            required
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || !email.trim()}
          >
            {submitting ? (
              <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Đang gửi...</>
            ) : (
              'Đăng ký'
            )}
          </button>
        </form>

        {pending && (
          <div className="alert alert-info caregiver-pending">
            <strong>📧 Đã gửi email xác nhận tới {pending.email}</strong>
            <p style={{ margin: '4px 0 0' }}>
              Vui lòng mở hộp thư và click <em>"Confirm subscription"</em> để bắt đầu nhận thông báo.
              Nếu không thấy, kiểm tra hộp thư <strong>Spam / Junk</strong>.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
