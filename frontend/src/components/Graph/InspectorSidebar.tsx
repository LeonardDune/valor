import React, { useState, useEffect } from 'react';
import { api, type FactorType } from '../../services/api';
import { ConfirmModal } from '../UI/ConfirmModal';
import { Trash2, Link as LinkIcon, Info, Type, Sliders, X } from 'lucide-react';

interface InspectorSidebarProps {
    selection: { type: 'node'; data: any } | { type: 'link'; data: any } | null;
    factors: any[];
    themeId: string;
    onRefresh: () => void;
    onClose: () => void;
}

export const InspectorSidebar: React.FC<InspectorSidebarProps> = ({ selection, factors, themeId, onRefresh, onClose }) => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [type, setType] = useState<FactorType>('systeemelement');
    const [statement, setStatement] = useState('');
    const [polarity, setPolarity] = useState('+');
    const [confidence, setConfidence] = useState(0.5);
    const [sourceId, setSourceId] = useState('');
    const [targetId, setTargetId] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

    // Sort factors alphabetically for the dropdowns
    const sortedFactors = [...factors].sort((a, b) => (a.name || '').localeCompare(b.name || ''));

    useEffect(() => {
        if (selection?.type === 'node') {
            setName(selection.data.name || '');
            setDescription(selection.data.description || '');
            setType(selection.data.type || 'systeemelement');
            setSourceId(''); // Clear sourceId to avoid confusion in node view

            // Reset relationship properties for the "Verbinding Leggen" form
            setStatement('');
            setPolarity('+');
            setConfidence(0.5);

            // Initialize targetId for the "Add Connection" dropdown if not already set or invalid
            const currentId = selection.data.dbId || selection.data.id;
            const firstOther = factors.find(f => (f.dbId || f.id) !== currentId);
            if (!targetId || !factors.find(f => f.id === targetId) || targetId === currentId) {
                setTargetId(firstOther?.id || '');
            }
        } else if (selection?.type === 'link') {
            // Map source/target objects to IDs for the dropdowns
            const linkData = selection.data as any;
            setStatement(linkData.statement || '');
            setPolarity(linkData.polarity || '+');
            setConfidence(linkData.confidence || 0.5);

            // Important: Use the dbId (UUID) from the node objects, or the source_id/target_id we added
            const sId = (typeof linkData.source === 'object' ? linkData.source.dbId : linkData.source_id);
            const tId = (typeof linkData.target === 'object' ? linkData.target.dbId : linkData.target_id);

            setSourceId(sId || '');
            setTargetId(tId || '');
        }
    }, [selection, factors]);

    const handleSave = async () => {
        if (!selection) return;
        setIsSaving(true);
        try {
            if (selection.type === 'node') {
                const factorId = selection.data.dbId || selection.data.id;
                await api.updateFactor(factorId, name, description, type);
            } else {
                await api.updateClaim(selection.data.id, {
                    statement,
                    polarity,
                    confidence,
                    source_id: sourceId,
                    target_id: targetId
                });
            }
            onRefresh();
        } catch (error) {
            console.error('Save failed', error);
        } finally {
            setIsSaving(false);
        }
    };

    const confirmDelete = async () => {
        if (!selection) return;
        setIsDeleteModalOpen(false);
        setIsSaving(true);
        try {
            if (selection.type === 'node') {
                const fid = selection.data.dbId || selection.data.id;
                await api.deleteFactor(fid);
            } else {
                await api.deleteClaim(selection.data.id);
            }
            onClose();
            onRefresh();
        } catch (error) {
            console.error('Delete failed', error);
        } finally {
            setIsSaving(false);
        }
    };

    if (!selection) return null;

    const isNode = selection.type === 'node';

    return (
        <div className="w-85 border-l border-slate-200 bg-white h-full flex flex-col shadow-2xl z-20 animate-slide-in-right overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 backdrop-blur-md">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${isNode ? 'bg-blue-50 text-blue-600' : 'bg-indigo-50 text-indigo-600'}`}>
                        {isNode ? <Type size={18} /> : <LinkIcon size={18} />}
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="font-bold text-slate-800 text-sm">
                                {isNode ? 'Factor' : 'Verbinding'}
                            </h3>
                            {!isNode && (
                                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold text-white shadow-sm ${polarity === '-' ? 'bg-red-500' : (polarity === '+' ? 'bg-emerald-500' : 'bg-slate-400')}`}>
                                    {polarity}
                                </span>
                            )}
                        </div>
                        <p className="text-[10px] text-slate-400 font-medium uppercase tracking-widest leading-none">
                            Inspector
                        </p>
                    </div>
                </div>
                <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-all">
                    <X size={20} />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
                {isNode ? (
                    <div className="space-y-5 animate-fade-in">
                        {/* Factor Identity */}
                        <div className="space-y-4">
                            <div>
                                <label className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                                    <Type size={12} /> Naam
                                </label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={e => setName(e.target.value)}
                                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-sm transition-all font-medium"
                                />
                            </div>
                            <div>
                                <label className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                                    <Sliders size={12} /> Rol (TU Delft)
                                </label>
                                <select
                                    value={type}
                                    onChange={e => setType(e.target.value as FactorType)}
                                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-sm cursor-pointer"
                                >
                                    <option value="middel">Middel (Means)</option>
                                    <option value="extern">Externe Factor</option>
                                    <option value="systeemelement">Systeemelement</option>
                                    <option value="criterium">Criterium (Doel)</option>
                                </select>
                            </div>
                            <div>
                                <label className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                                    <Info size={12} /> Beschrijving
                                </label>
                                <textarea
                                    value={description}
                                    onChange={e => setDescription(e.target.value)}
                                    rows={4}
                                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-sm resize-none"
                                    placeholder="Wat betekent deze factor?"
                                />
                            </div>
                        </div>

                        <div className="pt-4 border-t border-slate-100 space-y-4">
                            {factors.length > 1 && (
                                <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100 space-y-4">
                                    <label className="text-[10px] font-bold text-blue-400 uppercase tracking-widest block">Nieuwe Verbinding Leggen</label>

                                    <div className="space-y-2">
                                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">1. Doel factor</p>
                                        <select
                                            value={targetId}
                                            onChange={e => setTargetId(e.target.value)}
                                            className="w-full px-2 py-1.5 bg-white border border-blue-100 rounded-lg text-xs outline-none focus:ring-2 focus:ring-blue-500/20"
                                        >
                                            {sortedFactors
                                                .filter(f => (f.dbId || f.id) !== (selection.data.dbId || selection.data.id))
                                                .map(f => (
                                                    <option key={f.id} value={f.id}>{f.name}</option>
                                                ))
                                            }
                                        </select>
                                    </div>

                                    <div className="space-y-2">
                                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">2. Argumentatie</p>
                                        <textarea
                                            value={statement}
                                            onChange={e => setStatement(e.target.value)}
                                            rows={2}
                                            placeholder="Waarom is er een relatie?"
                                            className="w-full px-2 py-1.5 bg-white border border-blue-100 rounded-lg text-xs outline-none focus:ring-2 focus:ring-blue-500/20 resize-none"
                                        />
                                    </div>

                                    <div className="flex gap-3">
                                        <div className="flex-1 space-y-2">
                                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">3. Polarity</p>
                                            <select
                                                value={polarity}
                                                onChange={e => setPolarity(e.target.value)}
                                                className="w-full px-2 py-1.5 bg-white border border-blue-100 rounded-lg text-xs outline-none focus:ring-2 focus:ring-blue-500/20"
                                            >
                                                <option value="+">+</option>
                                                <option value="-">-</option>
                                                <option value="?">?</option>
                                            </select>
                                        </div>
                                        <div className="flex-1 space-y-2">
                                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">4. Zekerheid</p>
                                            <input
                                                type="number"
                                                min="0" max="1" step="0.1"
                                                value={confidence}
                                                onChange={e => setConfidence(parseFloat(e.target.value))}
                                                className="w-full px-2 py-1.5 bg-white border border-blue-100 rounded-lg text-xs outline-none focus:ring-2 focus:ring-blue-500/20"
                                            />
                                        </div>
                                    </div>

                                    <button
                                        onClick={async () => {
                                            setIsSaving(true);
                                            try {
                                                const sourceId = selection.data.dbId || selection.data.id;
                                                await api.createClaim({
                                                    theme_id: themeId,
                                                    statement: statement || 'Nieuwe verbinding',
                                                    source_id: sourceId,
                                                    target_id: targetId,
                                                    polarity,
                                                    confidence
                                                });
                                                onRefresh();
                                            } catch (e) {
                                                console.error('Failed to create claim', e);
                                            } finally {
                                                setIsSaving(false);
                                            }
                                        }}
                                        disabled={isSaving || !targetId}
                                        className="w-full py-2.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-all shadow-md flex items-center justify-center gap-2 group mt-2"
                                    >
                                        <LinkIcon size={14} className="group-hover:rotate-12 transition-transform" />
                                        Verbinding Leggen
                                    </button>
                                </div>
                            )}

                            <button
                                onClick={() => setIsDeleteModalOpen(true)}
                                className="w-full py-2.5 text-xs font-bold text-red-500 hover:bg-red-50 rounded-xl transition-all border border-dashed border-red-200 flex items-center justify-center gap-2 group"
                            >
                                <Trash2 size={14} className="group-hover:animate-bounce" />
                                Factor Verwijderen
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-5 animate-fade-in">
                        {/* Relationship Logic */}
                        <div className="space-y-4">
                            <div>
                                <label className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                                    <Info size={12} /> Argumentatie
                                </label>
                                <textarea
                                    value={statement}
                                    onChange={e => setStatement(e.target.value)}
                                    rows={3}
                                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm resize-none font-medium"
                                />
                            </div>
                            <div className="flex gap-3">
                                <div className="flex-1">
                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 block">Polariteit</label>
                                    <select
                                        value={polarity}
                                        onChange={e => setPolarity(e.target.value)}
                                        className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm"
                                    >
                                        <option value="+">Versterkend (+)</option>
                                        <option value="-">Remmend (-)</option>
                                        <option value="?">Onbekend (?)</option>
                                    </select>
                                </div>
                                <div className="flex-1">
                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 block">Zekerheid</label>
                                    <input
                                        type="number"
                                        min="0" max="1" step="0.1"
                                        value={confidence}
                                        onChange={e => setConfidence(parseFloat(e.target.value))}
                                        className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm"
                                    />
                                </div>
                            </div>

                            <div className="space-y-4 pt-2">
                                <div>
                                    <label className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                                        <LinkIcon size={12} /> Bron Factor
                                    </label>
                                    <select
                                        value={sourceId}
                                        onChange={e => setSourceId(e.target.value)}
                                        className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm"
                                    >
                                        {sortedFactors.map(f => (
                                            <option key={f.id} value={f.id}>{f.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                                        <LinkIcon size={12} /> Doel Factor
                                    </label>
                                    <select
                                        value={targetId}
                                        onChange={e => setTargetId(e.target.value)}
                                        className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm"
                                    >
                                        {sortedFactors.map(f => (
                                            <option key={f.id} value={f.id}>{f.name}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Danger Zone */}
                        <div className="pt-4 border-t border-slate-100">
                            <button
                                onClick={() => setIsDeleteModalOpen(true)}
                                className="w-full py-2.5 text-xs font-bold text-red-500 hover:bg-red-50 rounded-xl transition-all border border-dashed border-red-200 flex items-center justify-center gap-2 group"
                            >
                                <Trash2 size={14} className="group-hover:animate-bounce" />
                                Verbinding Verwijderen
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-slate-100 bg-slate-50/80 backdrop-blur-md flex gap-3">
                <button
                    onClick={onClose}
                    className="flex-1 py-3 text-xs font-bold text-slate-500 hover:bg-slate-200 rounded-xl transition-all uppercase tracking-wider"
                >
                    Sluiten
                </button>
                <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="flex-3 py-3 text-xs font-bold bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 disabled:opacity-50 uppercase tracking-wider"
                >
                    {isSaving ? 'Opslaan...' : 'Wijzigingen Opslaan'}
                </button>
            </div>

            {/* Custom Confirm Modal */}
            <ConfirmModal
                isOpen={isDeleteModalOpen}
                title={isNode ? 'Factor Verwijderen?' : 'Verbinding Verwijderen?'}
                message={isNode
                    ? `Weet je zeker dat je "${name}" wilt verwijderen? Alle bijbehorende verbindingen worden ook permanent verwijderd.`
                    : 'Weet je zeker dat je deze relatie tussen factoren wilt verwijderen?'}
                confirmLabel="Ja, Verwijderen"
                onConfirm={confirmDelete}
                onCancel={() => setIsDeleteModalOpen(false)}
                isDanger={true}
            />
        </div>
    );
};
