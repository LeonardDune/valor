import React, { useState } from 'react';
import { X } from 'lucide-react';
import { type FactorType } from '../../services/api';

interface FactorModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (name: string, type: FactorType, description: string) => void;
}

export const FactorModal: React.FC<FactorModalProps> = ({ isOpen, onClose, onSave }) => {
    const [name, setName] = useState('');
    const [type, setType] = useState<FactorType>('systeemelement');
    const [description, setDescription] = useState('');

    if (!isOpen) return null;

    const handleSave = () => {
        if (!name.trim()) return;
        onSave(name.trim(), type, description.trim());
        setName('');
        setDescription('');
        setType('systeemelement');
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                    <h3 className="font-bold text-slate-800">Nieuwe Factor Toevoegen</h3>
                    <button onClick={onClose} className="p-1 hover:bg-slate-200 rounded-lg text-slate-400 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Naam</label>
                        <input
                            autoFocus
                            type="text"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="Bijv. Energiebesparing"
                            className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm transition-all"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Rol (TU Delft)</label>
                        <select
                            value={type}
                            onChange={e => setType(e.target.value as FactorType)}
                            className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm transition-all bg-white"
                        >
                            <option value="middel">Middel (Means)</option>
                            <option value="extern">Externe Factor</option>
                            <option value="systeemelement">Systeemelement</option>
                            <option value="criterium">Criterium (Doel)</option>
                        </select>
                        <p className="mt-1.5 text-[10px] text-slate-400 leading-tight">
                            Selecteer de rol van deze factor binnen het systeemmodel volgens de TU Delft Systeemanalyse.
                        </p>
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Beschrijving (Optioneel)</label>
                        <textarea
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            rows={3}
                            placeholder="Wat houdt deze factor in?"
                            className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm transition-all resize-none"
                        />
                    </div>
                </div>

                <div className="p-4 border-t border-slate-100 bg-slate-50 flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-xl transition-colors"
                    >
                        Annuleren
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={!name.trim()}
                        className="flex-1 py-2.5 text-sm font-medium bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200 disabled:opacity-50 disabled:shadow-none"
                    >
                        Factor Aanmaken
                    </button>
                </div>
            </div>
        </div>
    );
};
