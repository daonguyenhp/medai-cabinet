import { useState } from 'react';
import '../../styles/modal.css';
import '../../styles/medications.css';

/**
 * Modal to confirm dispensing a medication from a compartment.
 */
export default function DispenseModal({ medication, onConfirm, onClose }) {
  const [qty, setQty] = useState(1);

  if (!medication) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Lấy thuốc</h3>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <p className="text-lg font-bold mb-4">{medication.name}</p>
          <div className="form-group">
            <label className="form-label">Số lượng cần lấy</label>
            <div className="qty-control">
              <button className="btn btn-outline btn-icon" onClick={() => setQty((q) => Math.max(1, q - 1))}>−</button>
              <span className="qty-value">{qty} {medication.unit}</span>
              <button className="btn btn-outline btn-icon" onClick={() => setQty((q) => Math.min(medication.stock_count, q + 1))}>+</button>
            </div>
          </div>
          <p className="text-muted text-sm">
            Tồn kho: {medication.stock_count} {medication.unit} → Còn lại: {medication.stock_count - qty} {medication.unit}
          </p>
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Hủy</button>
          <button className="btn btn-primary" onClick={() => onConfirm(qty)}>
            Xác nhận lấy thuốc
          </button>
        </div>
      </div>
    </div>
  );
}
