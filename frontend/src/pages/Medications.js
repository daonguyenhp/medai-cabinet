import { useState } from 'react';
import toast from 'react-hot-toast';
import { useApp } from '../App';
import { useMedications } from '../hooks';
import MedicationCard from '../components/medications/MedicationCard';
import MedicationForm from '../components/medications/MedicationForm';
import DispenseModal from '../components/medications/DispenseModal';
import { EMPTY_MEDICATION_FORM } from '../constants/medication.constants';
import '../styles/medications.css';

const FILTERS = [
  { key: 'all',       label: 'Tất cả' },
  { key: 'expiring',  label: '⚠️ Sắp hết hạn' },
  { key: 'expired',   label: '⛔ Hết hạn' },
  { key: 'low_stock', label: '📦 Sắp hết' },
];

export default function Medications() {
  const { user } = useApp();
  const { medications, loading, create, update, remove, dispense } = useMedications(user.user_id);

  const [showForm, setShowForm]         = useState(false);
  const [editingMed, setEditingMed]     = useState(null);
  const [form, setForm]                 = useState(EMPTY_MEDICATION_FORM);
  const [saving, setSaving]             = useState(false);
  const [filter, setFilter]             = useState('all');
  const [search, setSearch]             = useState('');
  const [dispenseMed, setDispenseMed]   = useState(null);

  // ── Helpers ──────────────────────────────────────────────────────────────────
  const openAdd = () => {
    setEditingMed(null);
    setForm(EMPTY_MEDICATION_FORM);
    setShowForm(true);
  };

  const openEdit = (med) => {
    setEditingMed(med);
    setForm({
      name: med.name ?? '',
      generic_name: med.generic_name ?? '',
      medication_type: med.medication_type ?? 'pill',
      compartment: med.compartment ?? 1,
      stock_count: med.stock_count ?? 0,
      unit: med.unit ?? 'viên',
      dosage_strength: med.dosage_strength ?? '',
      manufacturer: med.manufacturer ?? '',
      expiry_date: med.expiry_date ?? '',
      opened_date: med.opened_date ?? '',
      post_opening_days: med.post_opening_days ?? '',
      storage_instructions: med.storage_instructions ?? '',
      notes: med.notes ?? '',
      low_stock_threshold: med.low_stock_threshold ?? 5,
    });
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.name || !form.expiry_date) {
      toast.error('Vui lòng điền tên thuốc và ngày hết hạn');
      return;
    }
    setSaving(true);
    try {
      // Sanitize: empty strings → null, numeric strings → numbers
      const payload = Object.fromEntries(
        Object.entries(form).map(([k, v]) => [k, v === '' ? null : v]),
      );
      ['post_opening_days', 'stock_count', 'compartment', 'low_stock_threshold'].forEach((k) => {
        if (payload[k] != null) payload[k] = parseInt(payload[k], 10);
      });

      if (editingMed) {
        await update(editingMed.medication_id, payload);
      } else {
        await create(payload);
      }
      setShowForm(false);
    } catch (err) {
      toast.error(err.userMessage ?? 'Lỗi lưu thuốc');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (med) => {
    await remove(med.medication_id, med.name);
  };

  const handleDispenseConfirm = async (qty) => {
    try {
      await dispense(dispenseMed.medication_id, qty);
      setDispenseMed(null);
    } catch (err) {
      toast.error(err.userMessage ?? 'Không thể lấy thuốc');
    }
  };

  // ── Filtering ─────────────────────────────────────────────────────────────
  const filtered = medications.filter((med) => {
    const matchSearch = !search || med.name.toLowerCase().includes(search.toLowerCase());
    const matchFilter =
      filter === 'all' ||
      (filter === 'expiring'  && ['warning', 'critical'].includes(med.expiry_status)) ||
      (filter === 'expired'   && med.expiry_status === 'expired') ||
      (filter === 'low_stock' && med.stock_count <= (med.low_stock_threshold ?? 5));
    return matchSearch && matchFilter;
  });

  const counts = {
    all:       medications.length,
    expiring:  medications.filter((m) => ['warning', 'critical'].includes(m.expiry_status)).length,
    expired:   medications.filter((m) => m.expiry_status === 'expired').length,
    low_stock: medications.filter((m) => m.stock_count <= (m.low_stock_threshold ?? 5)).length,
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div>
      {/* Toolbar */}
      <div className="meds-toolbar">
        <div className="meds-search">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            className="meds-search-input"
            placeholder="Tìm kiếm thuốc..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="meds-filters">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              className={`meds-filter-btn ${filter === f.key ? 'active' : ''}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
              {counts[f.key] > 0 && f.key !== 'all' && (
                <span className="meds-filter-count">{counts[f.key]}</span>
              )}
            </button>
          ))}
        </div>

        <button className="btn btn-primary" onClick={openAdd}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Thêm thuốc
        </button>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="loading-overlay"><div className="spinner" /><span>Đang tải...</span></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">💊</div>
          <h3>{search ? 'Không tìm thấy thuốc' : 'Tủ thuốc trống'}</h3>
          <p>{search ? `Không có thuốc nào khớp với "${search}"` : 'Thêm thuốc đầu tiên vào tủ của bạn.'}</p>
          {!search && <button className="btn btn-primary mt-4" onClick={openAdd}>Thêm thuốc đầu tiên</button>}
        </div>
      ) : (
        <div className="grid grid-3">
          {filtered.map((med) => (
            <MedicationCard
              key={med.medication_id}
              medication={med}
              onDispense={setDispenseMed}
              onEdit={openEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      {showForm && (
        <MedicationForm
          form={form}
          onChange={setForm}
          onSave={handleSave}
          onClose={() => setShowForm(false)}
          isEditing={!!editingMed}
          saving={saving}
        />
      )}

      {dispenseMed && (
        <DispenseModal
          medication={dispenseMed}
          onConfirm={handleDispenseConfirm}
          onClose={() => setDispenseMed(null)}
        />
      )}
    </div>
  );
}
