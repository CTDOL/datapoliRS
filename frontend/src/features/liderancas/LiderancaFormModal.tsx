'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, UserPlus, MapPin, Phone } from 'lucide-react';
import { FormDataLideranca, Lideranca } from './useLiderancas';
import { api } from '@/services/api';

interface MunicipioItem {
  cd_ibge_7: string;
  nm_municipio: string;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: FormDataLideranca) => Promise<boolean>;
  isSubmitting: boolean;
  initialData?: Lideranca | null;
}

export function LiderancaFormModal({ isOpen, onClose, onSubmit, isSubmitting, initialData }: ModalProps) {
  const [formData, setFormData] = useState<FormDataLideranca>({
    nm_completo: '',
    nr_telefone: '',
    cd_ibge_7: '4314902',
    tp_influencia: 'Comunitária',
  });
  
  useEffect(() => {
    setTimeout(() => {
      if (initialData) {
        setFormData({
          nm_completo: initialData.nm_completo || '',
          nr_telefone: initialData.nr_telefone || '',
          cd_ibge_7: initialData.cd_ibge_7 || '4314902',
          tp_influencia: initialData.tp_influencia || 'Comunitária',
        });
      } else {
        setFormData({ nm_completo: '', nr_telefone: '', cd_ibge_7: '4314902', tp_influencia: 'Comunitária' });
      }
    }, 0);
  }, [initialData, isOpen]);
  
  const [municipios, setMunicipios] = useState<MunicipioItem[]>([]);
  const [loadingMun, setLoadingMun] = useState(false);

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
    const success = await onSubmit(formData);
    if (success) {
      setFormData({ nm_completo: '', nr_telefone: '', cd_ibge_7: '4314902', tp_influencia: 'Comunitária' });
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
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-zinc-900 border border-zinc-700/50 rounded-3xl shadow-2xl z-50 overflow-hidden"
          >
        <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
              <UserPlus className="w-5 h-5 text-purple-400" />
            </div>
            <h2 className="text-xl font-bold text-white">{initialData ? 'Editar Liderança' : 'Nova Liderança'}</h2>
          </div>
          <button onClick={onClose} className="text-zinc-400 hover:text-white transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Nome Completo</label>
            <input type="text" required value={formData.nm_completo} onChange={(e) => setFormData({...formData, nm_completo: e.target.value})} className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50" placeholder="Ex: João da Silva"/>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5 flex items-center gap-1"><Phone className="w-3 h-3"/> Telefone</label>
              <input type="text" required value={formData.nr_telefone} onChange={(e) => setFormData({...formData, nr_telefone: e.target.value})} className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50" placeholder="(51) 99999-9999"/>
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5 flex items-center gap-1"><MapPin className="w-3 h-3"/> Município de Atuação</label>
              <select 
                value={formData.cd_ibge_7} 
                onChange={(e) => setFormData({...formData, cd_ibge_7: e.target.value})} 
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50"
                disabled={loadingMun}
              >
                {loadingMun ? (
                  <option value="">Carregando...</option>
                ) : (
                  municipios.map(m => (
                    <option key={m.cd_ibge_7} value={m.cd_ibge_7}>{m.nm_municipio}</option>
                  ))
                )}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Tipo de Influência</label>
            <select value={formData.tp_influencia} onChange={(e) => setFormData({...formData, tp_influencia: e.target.value})} className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50">
              <option value="Comunitária">Comunitária</option>
              <option value="Religiosa">Religiosa</option>
              <option value="Empresarial">Empresarial</option>
              <option value="Política">Política</option>
            </select>
          </div>
          <div className="pt-4 flex gap-3">
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
