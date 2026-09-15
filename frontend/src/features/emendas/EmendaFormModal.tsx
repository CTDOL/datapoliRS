'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, FileText, MapPin } from 'lucide-react';
import { FormDataEmenda, Emenda } from './useEmendas';
import { api } from '@/services/api';

interface MunicipioItem {
  cd_ibge_7: string;
  nm_municipio: string;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: FormDataEmenda) => Promise<boolean>;
  isSubmitting: boolean;
  initialData?: Emenda | null;
}

const EMPTY_FORM: FormDataEmenda = {
  cd_ibge_7: '',
  nr_emenda: '',
  ano_exercicio: new Date().getFullYear(),
  tp_emenda: 'Individual',
  ds_area: '',
  ds_objeto: '',
  vl_indicado: '0',
  vl_empenhado: '0',
  vl_pago: '0',
  tp_situacao: 'Indicada',
  ds_observacoes: '',
};

export function EmendaFormModal({ isOpen, onClose, onSubmit, isSubmitting, initialData }: ModalProps) {
  const [formData, setFormData] = useState<FormDataEmenda>(EMPTY_FORM);
  const [municipios, setMunicipios] = useState<MunicipioItem[]>([]);
  const [loadingMun, setLoadingMun] = useState(false);

  useEffect(() => {
    setTimeout(() => {
      if (initialData) {
        setFormData({
          cd_ibge_7: initialData.cd_ibge_7 || '',
          nr_emenda: initialData.nr_emenda || '',
          ano_exercicio: initialData.ano_exercicio,
          tp_emenda: initialData.tp_emenda || 'Individual',
          ds_area: initialData.ds_area || '',
          ds_objeto: initialData.ds_objeto,
          vl_indicado: initialData.vl_indicado,
          vl_empenhado: initialData.vl_empenhado,
          vl_pago: initialData.vl_pago,
          tp_situacao: initialData.tp_situacao,
          ds_observacoes: initialData.ds_observacoes || '',
        });
      } else {
        setFormData(EMPTY_FORM);
      }
    }, 0);
  }, [initialData, isOpen]);

  useEffect(() => {
    if (isOpen) {
      const fetchMuns = async () => {
        setLoadingMun(true);
        try {
          const res = await api.get('/api/v1/geo/municipios/lista');
          setMunicipios(res.data);
        } catch (err) {
          console.error(err);
        } finally {
          setLoadingMun(false);
        }
      };
      fetchMuns();
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await onSubmit({ ...formData, cd_ibge_7: formData.cd_ibge_7 || undefined });
    if (success) {
      setFormData(EMPTY_FORM);
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-zinc-950/80 backdrop-blur-sm z-40"
          />
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl bg-zinc-900 border border-zinc-700/50 rounded-3xl shadow-2xl z-50 overflow-hidden max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center sticky top-0 bg-zinc-900 z-10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
                  <FileText className="w-5 h-5 text-purple-400" />
                </div>
                <h2 className="text-xl font-bold text-white">{initialData ? 'Editar Emenda' : 'Nova Emenda'}</h2>
              </div>
              <button onClick={onClose} className="text-zinc-400 hover:text-white transition-colors">
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Objeto / Finalidade</label>
                <textarea
                  required
                  rows={2}
                  value={formData.ds_objeto}
                  onChange={(e) => setFormData({ ...formData, ds_objeto: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
                  placeholder="Ex: Pavimentação de ruas no bairro Centro"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Número da Emenda</label>
                  <input
                    type="text"
                    value={formData.nr_emenda || ''}
                    onChange={(e) => setFormData({ ...formData, nr_emenda: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                    placeholder="Ex: 12345678"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Ano de Exercício</label>
                  <input
                    type="number"
                    required
                    value={formData.ano_exercicio}
                    onChange={(e) => setFormData({ ...formData, ano_exercicio: Number(e.target.value) })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Tipo de Emenda</label>
                  <select
                    value={formData.tp_emenda || ''}
                    onChange={(e) => setFormData({ ...formData, tp_emenda: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50"
                  >
                    <option value="Individual">Individual</option>
                    <option value="Bancada">Bancada</option>
                    <option value="Comissão">Comissão</option>
                    <option value="Relator">Relator</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5 flex items-center gap-1"><MapPin className="w-3 h-3" /> Município Beneficiário</label>
                  <select
                    value={formData.cd_ibge_7 || ''}
                    onChange={(e) => setFormData({ ...formData, cd_ibge_7: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50"
                    disabled={loadingMun}
                  >
                    <option value="">Não especificado</option>
                    {municipios.map((m) => (
                      <option key={m.cd_ibge_7} value={m.cd_ibge_7}>{m.nm_municipio}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Área Temática</label>
                <input
                  type="text"
                  value={formData.ds_area || ''}
                  onChange={(e) => setFormData({ ...formData, ds_area: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                  placeholder="Ex: Saúde, Educação, Infraestrutura..."
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Valor Indicado (R$)</label>
                  <input
                    type="number" step="0.01" min="0"
                    value={formData.vl_indicado}
                    onChange={(e) => setFormData({ ...formData, vl_indicado: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Empenhado (R$)</label>
                  <input
                    type="number" step="0.01" min="0"
                    value={formData.vl_empenhado}
                    onChange={(e) => setFormData({ ...formData, vl_empenhado: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Pago (R$)</label>
                  <input
                    type="number" step="0.01" min="0"
                    value={formData.vl_pago}
                    onChange={(e) => setFormData({ ...formData, vl_pago: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Situação</label>
                <select
                  value={formData.tp_situacao}
                  onChange={(e) => setFormData({ ...formData, tp_situacao: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50"
                >
                  <option value="Indicada">Indicada</option>
                  <option value="Empenhada">Empenhada</option>
                  <option value="Paga">Paga</option>
                  <option value="Cancelada">Cancelada</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Observações</label>
                <textarea
                  rows={2}
                  value={formData.ds_observacoes || ''}
                  onChange={(e) => setFormData({ ...formData, ds_observacoes: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button type="button" onClick={onClose} className="flex-1 px-4 py-3 rounded-xl border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors">Cancelar</button>
                <button type="submit" disabled={isSubmitting} className="flex-1 bg-purple-600 hover:bg-purple-500 text-white px-4 py-3 rounded-xl font-medium shadow-lg flex justify-center disabled:opacity-70">
                  {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Salvar'}
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
