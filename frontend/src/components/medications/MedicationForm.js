import { MEDICATION_TYPES } from '../../constants/medication.constants';
import '../../styles/modal.css';

/**
 * Add / Edit medication modal form.
 * Controlled by parent via `form` + `onChange`.
 */
export default function MedicationForm({ form, onChange, onSave, onClose, isEditing, saving }) {
  const set = (field, value) => onChange({ ...form, [field]: value });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">{isEditing ? 'Cập nhật thuốc' : 'Thêm thuốc mới'}</h3>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="grid grid-2">
            <div className="form-group">
              <label className="form-label">Tên thuốc *</label>
              <input className="form-control" value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Paracetamol 500mg" />
            </div>
            <div className="form-group">
              <label className="form-label">Tên hoạt chất</label>
              <input className="form-control" value={form.generic_name} onChange={(e) => set('generic_name', e.target.value)} placeholder="Acetaminophen" />
            </div>
            <div className="form-group">
              <label className="form-label">Loại thuốc *</label>
              <select className="form-control" value={form.medication_type} onChange={(e) => set('medication_type', e.target.value)}>
                {MEDICATION_TYPES.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Ngăn chứa (1–3) *</label>
              <select className="form-control" value={form.compartment} onChange={(e) => set('compartment', e.target.value)}>
                <option value={1}>Ngăn 1</option>
                <option value={2}>Ngăn 2</option>
                <option value={3}>Ngăn 3</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Số lượng tồn kho *</label>
              <input type="number" className="form-control" value={form.stock_count} onChange={(e) => set('stock_count', e.target.value)} min={0} />
            </div>
            <div className="form-group">
              <label className="form-label">Đơn vị</label>
              <input className="form-control" value={form.unit} onChange={(e) => set('unit', e.target.value)} placeholder="viên, ml, ống..." />
            </div>
            <div className="form-group">
              <label className="form-label">Hàm lượng</label>
              <input className="form-control" value={form.dosage_strength} onChange={(e) => set('dosage_strength', e.target.value)} placeholder="500mg, 10ml..." />
            </div>
            <div className="form-group">
              <label className="form-label">Nhà sản xuất</label>
              <input className="form-control" value={form.manufacturer} onChange={(e) => set('manufacturer', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Ngày hết hạn *</label>
              <input type="date" className="form-control" value={form.expiry_date} onChange={(e) => set('expiry_date', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Ngày mở hộp</label>
              <input type="date" className="form-control" value={form.opened_date} onChange={(e) => set('opened_date', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Hạn dùng sau khi mở (ngày)</label>
              <input type="number" className="form-control" value={form.post_opening_days} onChange={(e) => set('post_opening_days', e.target.value)} placeholder="28" min={1} />
            </div>
            <div className="form-group">
              <label className="form-label">Ngưỡng cảnh báo hết thuốc</label>
              <input type="number" className="form-control" value={form.low_stock_threshold} onChange={(e) => set('low_stock_threshold', e.target.value)} min={1} />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Hướng dẫn bảo quản</label>
            <input className="form-control" value={form.storage_instructions} onChange={(e) => set('storage_instructions', e.target.value)} placeholder="Bảo quản nơi khô ráo, tránh ánh sáng..." />
          </div>
          <div className="form-group">
            <label className="form-label">Ghi chú</label>
            <textarea className="form-control" value={form.notes} onChange={(e) => set('notes', e.target.value)} rows={2} />
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Hủy</button>
          <button className="btn btn-primary" onClick={onSave} disabled={saving}>
            {saving ? 'Đang lưu...' : isEditing ? 'Cập nhật' : 'Thêm thuốc'}
          </button>
        </div>
      </div>
    </div>
  );
}
