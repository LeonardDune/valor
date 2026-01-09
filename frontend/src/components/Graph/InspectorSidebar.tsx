import React, { useState, useEffect } from 'react';
import { api, type Claim } from '../../services/api';


interface InspectorSidebarProps {
    selection: { type: 'node'; data: any } | { type: 'link'; data: Claim } | null;
    onRefresh: () => void;
    onClose: () => void;
}

export const InspectorSidebar: React.FC<InspectorSidebarProps> = ({ selection, onRefresh, onClose }) => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [statement, setStatement] = useState('');
    const [polarity, setPolarity] = useState('+');
    const [confidence, setConfidence] = useState(0.5);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (selection?.type === 'node') {
            setName(selection.data.id || ''); // In the graph, name is often the id
            setDescription(selection.data.description || '');
        } else if (selection?.type === 'link') {
            setStatement(selection.data.statement || '');
            setPolarity(selection.data.polarity || '+');
            setConfidence(selection.data.confidence || 0.5);
        }
    }, [selection]);

    const handleSave = async () => {
        if (!selection) return;
        setIsSaving(true);
        try {
            if (selection.type === 'node') {
                // Find existing ID for node if it's separate from name
                // For now assume selection.data.nodeId exists or similar
                const factorId = selection.data.nodeId || selection.data.id;
                await api.updateFactor(factorId, name, description);
            } else {
                await api.updateClaim(selection.data.id, {
                    statement,
                    polarity,
                    confidence
                });
            }
            onRefresh();
        } catch (error) {
            console.error('Save failed', error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async () => {
        if (selection?.type !== 'link') return;
        if (!window.confirm('Weet je zeker dat je deze verbinding wilt verwijderen?')) return;

        setIsSaving(true);
        try {
            await api.deleteClaim(selection.data.id);
            onClose();
            onRefresh();
        } catch (error) {
            console.error('Delete failed', error);
        } finally {
            setIsSaving(false);
        }
    };

    if (!selection) return null;

    return (
        <div className="w-80 border-l border-slate-200 bg-white h-full flex flex-col shadow-xl z-20 animate-slide-in-right">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                <h3 className="font-bold text-slate-800">
                    {selection.type === 'node' ? 'Factor Aanpassen' : 'Verbinding Aanpassen'}
                </h3>
                <button onClick={onClose} className="text-slate-400 hover:text-slate-600 font-bold">×</button>
            </div>

            <div className="p-6 space-y-6 flex-1 overflow-y-auto">
                {selection.type === 'node' ? (
                    <>
                        <div>
                            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Naam</label>
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Beschrijving</label>
                            <textarea
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                rows={4}
                                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                                placeholder="Wat betekent deze factor?"
                            />
                        </div>
                    </>
                ) : (
                    <>
                        <div>
                            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Argumentatie</label>
                            <textarea
                                value={statement}
                                onChange={e => setStatement(e.target.value)}
                                rows={3}
                                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                            />
                        </div>
                        <div className="flex gap-4">
                            <div className="flex-1">
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Polariteit</label>
                                <select
                                    value={polarity}
                                    onChange={e => setPolarity(e.target.value)}
                                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                                >
                                    <option value="+">Versterkend (+)</option>
                                    <option value="-">Remmend (-)</option>
                                    <option value="?">Onbekend (?)</option>
                                </select>
                            </div>
                            <div className="flex-1">
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Zekerheid</label>
                                <input
                                    type="number"
                                    min="0" max="1" step="0.1"
                                    value={confidence}
                                    onChange={e => setConfidence(parseFloat(e.target.value))}
                                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                                />
                            </div>
                        </div>

                        <div className="pt-4 border-t border-slate-100">
                            <button
                                onClick={handleDelete}
                                className="w-full py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100"
                            >
                                Verbinding Verwijderen
                            </button>
                        </div>
                    </>
                )}
            </div>

            <div className="p-4 border-t border-slate-100 bg-slate-50 flex gap-3">
                <button
                    onClick={onClose}
                    className="flex-1 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
                >
                    Annuleren
                </button>
                <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="flex-1 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50"
                >
                    {isSaving ? 'Opslaan...' : 'Opslaan'}
                </button>
            </div>
        </div>
    );
};
