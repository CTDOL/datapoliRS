'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, UserPlus, MapPin, Phone, Camera, Search } from 'lucide-react';
import { FormDataLideranca, Lideranca } from './useLiderancas';
import { api } from '@/services/api';

interface MunicipioItem {
  cd_ibge_7: string;
  nm_municipio: string;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Cria/atualiza a liderança e retorna o id_lideranca em caso de sucesso, ou null em caso de falha. */
  onSubmit: (data: FormDataLideranca) => Promise<string | null>;
  onUploadFoto: (id: string, arquivo: File) => Promise<boolean>;
  isSubmitting: boolean;
  initialData?: Lideranca | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const EMPTY_FORM: FormDataLideranca = {
  nm_completo: '',
  nr_telefone: '',
  tp_influencia: 'Comunitária',
  municipios: [],
};

export function LiderancaFormModal({ isOpen, onClose, onSubmit, onUploadFoto, isSubmitting, initialData }: ModalProps) {
  const [formData, setFormData] = useState<FormDataLideranca>(EMPTY_FORM);
  const [buscaMunicipio, setBuscaMunicipio] = useState('');
  const [fotoArquivo, setFotoArquivo] = useState<File | null>(null);
  const [fotoPreview, setFotoPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setTimeout(() => {
      if (initialData) {
        setFormData({
          nm_completo: initialData.nm_completo || '',
          nr_telefone: initialData.nr_telefone || '',
          tp_influencia: initialData.tp_influencia || 'Comunitária',
          municipios: initialData.municipios?.map((m) => m.cd_ibge_7) || [],
        });
        setFotoPreview(initialData.ds_foto_url ? `${API_BASE_URL}${initialData.ds_foto_url}` : null);
      } else {
        setFormData(EMPTY_FORM);
        setFotoPreview(null);
      }
      setFotoArquivo(null);
      setBuscaMunicipio('');
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

  const toggleMunicipio = (cdIbge7: string) => {
    setFormData((prev) => ({
      ...prev,
      municipios: prev.municipios.includes(cdIbge7)
        ? prev.municipios.filter((c) => c !== cdIbge7)
        : [...prev.municipios, cdIbge7],
    }));
  };

  const nomeDoMunicipio = (cdIbge7: string) => municipios.find((m) => m.cd_ibge_7 === cdIbge7)?.nm_municipio || cdIbge7;

  const municipiosFiltrados = municipios.filter((m) =>
    m.nm_municipio.toLowerCase().includes(buscaMunicipio.trim().toLowerCase())
  );

  const handleFotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const arquivo = e.target.files?.[0];
    if (!arquivo) return;
    setFotoArquivo(arquivo);
    setFotoPreview(URL.createObjectURL(arquivo));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = await onSubmit(formData);
    if (!id) return; // onSubmit já loga o erro; mantém o modal aberto para o usuário corrigir

    if (fotoArquivo) {
      await onUploadFoto(id, fotoArquivo);
    }
    onClose();
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
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-zinc-900 border border-zinc-700/50 rounded-3xl shadow-2xl z-50 overflow-hidden max-h-[90vh] flex flex-col"
          >
        <div className="p-6 border-b border-zinc-800 flex justify-between items-center shrink-0">
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

        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto">
          {/* Foto */}
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-20 h-20 rounded-2xl bg-zinc-950 border-2 border-dashed border-zinc-700 hover:border-purple-500/50 flex items-center justify-center overflow-hidden shrink-0 transition-colors"
            >
              {fotoPreview ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={fotoPreview} alt="Prévia da foto" className="w-full h-full object-cover" />
              ) : (
                <Camera className="w-6 h-6 text-zinc-500" />
              )}
            </button>
            <div>
              <p className="text-sm font-semibold text-zinc-300">Foto</p>
              <p className="text-xs text-zinc-500">JPEG, PNG ou WebP · até 5MB</p>
            </div>
            <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleFotoChange} className="hidden" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Nome Completo</label>
            <input type="text" required value={formData.nm_completo} onChange={(e) => setFormData({...formData, nm_completo: e.target.value})} className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50" placeholder="Ex: João da Silva"/>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5 flex items-center gap-1"><Phone className="w-3 h-3"/> Telefone</label>
            <input type="text" required value={formData.nr_telefone} onChange={(e) => setFormData({...formData, nr_telefone: e.target.value})} className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50" placeholder="(51) 99999-9999"/>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5 flex items-center gap-1">
              <MapPin className="w-3 h-3"/> Municípios de Atuação ({formData.municipios.length} selecionado{formData.municipios.length === 1 ? '' : 's'})
            </label>

            {formData.municipios.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-2">
                {formData.municipios.map((cd) => (
                  <span key={cd} className="inline-flex items-center gap-1 bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-full px-2.5 py-1 text-xs">
                    {nomeDoMunicipio(cd)}
                    <button type="button" onClick={() => toggleMunicipio(cd)} className="hover:text-white">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            <div className="relative mb-1.5">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-500" />
              <input
                type="text"
                value={buscaMunicipio}
                onChange={(e) => setBuscaMunicipio(e.target.value)}
                placeholder="Buscar município..."
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-8 pr-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
            <div className="max-h-40 overflow-y-auto bg-zinc-950 border border-zinc-800 rounded-xl divide-y divide-zinc-800/50">
              {loadingMun ? (
                <p className="px-4 py-3 text-xs text-zinc-500">Carregando municípios...</p>
              ) : municipiosFiltrados.length === 0 ? (
                <p className="px-4 py-3 text-xs text-zinc-500">Nenhum município encontrado.</p>
              ) : (
                municipiosFiltrados.map((m) => (
                  <label key={m.cd_ibge_7} className="flex items-center gap-2 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.municipios.includes(m.cd_ibge_7)}
                      onChange={() => toggleMunicipio(m.cd_ibge_7)}
                      className="accent-purple-500"
                    />
                    {m.nm_municipio}
                  </label>
                ))
              )}
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
            <button
              type="submit"
              disabled={isSubmitting || formData.municipios.length === 0}
              title={formData.municipios.length === 0 ? 'Selecione pelo menos um município' : undefined}
              className="flex-1 bg-purple-600 hover:bg-purple-500 text-white px-4 py-3 rounded-xl font-medium shadow-lg flex justify-center disabled:opacity-70"
            >
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
