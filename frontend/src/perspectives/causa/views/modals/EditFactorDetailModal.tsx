import React, { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
// import * as Select from '@radix-ui/react-select'; // Unused, using native select for MVP complexity
import {
    X,
    Trash2,
    Type,
    Link as LinkIcon,
    ChevronDown,
    Save
} from 'lucide-react';
import { api, type FactorType } from '../../../../services/api';

// Reusing FactorModal styles since I haven't set up a global theme yet
// But using Radix primitives for accessibility and portal behavior

interface EditFactorDetailModalProps {
    // We pass the RAW node/link data here
    selection: { type: 'node' | 'link'; data: any } | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onRefresh: () => void;
    factors: any[]; // Needed to link to others
    themeId: string;
}

export const EditFactorDetailModal: React.FC<EditFactorDetailModalProps> = ({
    selection,
    open,
    onOpenChange,
    onRefresh,
    factors: _factors,
    themeId
}) => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [type, setType] = useState<FactorType>('systeemelement');

    // Relationship fields
    const [statement, setStatement] = useState('');
    const [polarity, setPolarity] = useState('+');
    const [confidence, setConfidence] = useState(0.5);
    const [sourceId, setSourceId] = useState('');
    const [targetId, setTargetId] = useState('');

    const [isSaving, setIsSaving] = useState(false);

    // Helpers for New Connection Logic
    const [newTargetId, setNewTargetId] = useState('');
    const [newStatement, setNewStatement] = useState('');
    const [newPolarity, setNewPolarity] = useState('+');
    const [newConfidence, setNewConfidence] = useState(0.5);
    const [isCreatingLink, setIsCreatingLink] = useState(false);

    // Sync state when selection changes
    useEffect(() => {
        if (!selection || !open) return;

        if (selection.type === 'node') {
            const data = selection.data;
            // If data is just { id, label, type }, we might need to find full object in `factors`
            // But if we passed full object in data, we are good.
            // Let's assume data has the fields we mapped.
            setName(data.label || '');
            setDescription(data.description || '');
            // Map internal 'system'/'factor' type back to role if possible, or use role field
            // The CLDView passes `role` now.
            setType((data.role || 'systeemelement') as FactorType);

            // Connection Form Reset
            setTargetId('');
            setStatement('');
            setPolarity('+');
            setConfidence(0.5);
        } else {
            // Link
            const data = selection.data;
            setStatement(data.statement || '');
            setPolarity(data.polarity || '+');
            setConfidence(data.confidence || 0.5);
            setSourceId(data.source_id || data.source || '');
            setTargetId(data.target_id || data.target || '');
        }
    }, [selection, open]);

    const handleSave = async () => {
        if (!selection) return;
        setIsSaving(true);
        try {
            if (selection.type === 'node') {
                await api.updateFactor(selection.data.id, name, description, type, themeId);
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
            onOpenChange(false);
        } catch (err) {
            console.error(err);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!selection) return;
        if (!confirm("Weet je zeker dat je dit wilt verwijderen?")) return;

        setIsSaving(true);
        try {
            if (selection.type === 'node') {
                await api.deleteFactor(selection.data.id);
            } else {
                await api.deleteClaim(selection.data.id);
            }
            onRefresh();
            onOpenChange(false);
        } catch (err) {
            console.error(err);
        } finally {
            setIsSaving(false);
        }
    };

    const handleCreateLink = async () => {
        if (!selection || !newTargetId) return;
        setIsCreatingLink(true);
        try {
            const sourceId = selection.data.id;
            await api.createClaim({
                theme_id: themeId,
                statement: newStatement || 'Nieuwe verbinding',
                source_id: sourceId,
                target_id: newTargetId,
                polarity: newPolarity,
                confidence: newConfidence
            });
            setNewStatement('');
            onRefresh(); // Refresh to show new link
            alert("Verbinding aangemaakt!");
        } catch (e) {
            console.error('Failed to create claim', e);
        } finally {
            setIsCreatingLink(false);
        }
    };

    if (!selection) return null;

    const isNode = selection.type === 'node';
    const sortedFactors = [..._factors].sort((a, b) => (a.name || '').localeCompare(b.name || ''));

    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 animate-in fade-in" />
                <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-white rounded-2xl shadow-2xl z-50 animate-in zoom-in-95 duration-200 focus:outline-none flex flex-col max-h-[90vh]">

                    {/* Header */}
                    <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/80">
                        <Dialog.Title className="text-sm font-bold text-slate-800 flex items-center gap-2">
                            {isNode ? <Type size={16} className="text-blue-500" /> : <LinkIcon size={16} className="text-indigo-500" />}
                            {isNode ? 'Factor Bewerken' : 'Verbinding Bewerken'}
                        </Dialog.Title>
                        <Dialog.Close className="p-1 hover:bg-slate-200 rounded-full transition-colors text-slate-400">
                            <X size={18} />
                        </Dialog.Close>
                    </div>

                    {/* Body */}
                    <div className="p-6 overflow-y-auto space-y-5">
                        {isNode ? (
                            <>
                                {/* Factor Name */}
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Naam</label>
                                    <input
                                        className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-bold focus:ring-2 focus:ring-blue-500 outline-none"
                                        value={name}
                                        onChange={e => setName(e.target.value)}
                                    />
                                </div>

                                {/* Factor Type (Role) */}
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Rol (TU Delft)</label>
                                    <div className="relative">
                                        <select
                                            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm appearance-none bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                                            value={type}
                                            onChange={e => setType(e.target.value as FactorType)}
                                        >
                                            <option value="middel">Middel (Means)</option>
                                            <option value="extern">Externe Factor</option>
                                            <option value="systeemelement">Systeemelement</option>
                                            <option value="criterium">Criterium (Doel)</option>
                                        </select>
                                        <ChevronDown size={14} className="absolute right-3 top-3 text-slate-400 pointer-events-none" />
                                    </div>
                                </div>

                                {/* Description */}
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Beschrijving</label>
                                    <textarea
                                        className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                                        rows={4}
                                        value={description}
                                        onChange={e => setDescription(e.target.value)}
                                        placeholder="Beschrijf de factor..."
                                    />
                                </div>

                                {/* NEW CONNECTION SECTION */}
                                {(_factors.length > 1 && selection.data) && ( // Ensure selection.data exists before accessing it
                                    <div className="pt-4 mt-4 border-t border-slate-100">
                                        <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100 space-y-4">
                                            <label className="text-[10px] font-bold text-blue-400 uppercase tracking-widest block flex items-center gap-2">
                                                <LinkIcon size={12} />
                                                Nieuwe Verbinding Leggen
                                            </label>

                                            <div className="space-y-2">
                                                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">1. Doel factor</p>
                                                <select
                                                    value={newTargetId}
                                                    onChange={e => setNewTargetId(e.target.value)}
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
                                                    value={newStatement}
                                                    onChange={e => setNewStatement(e.target.value)}
                                                    rows={2}
                                                    placeholder="Waarom is er een relatie?"
                                                    className="w-full px-2 py-1.5 bg-white border border-blue-100 rounded-lg text-xs outline-none focus:ring-2 focus:ring-blue-500/20 resize-none"
                                                />
                                            </div>

                                            <div className="flex gap-3">
                                                <div className="flex-1 space-y-2">
                                                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">3. Polarity</p>
                                                    <select
                                                        value={newPolarity}
                                                        onChange={e => setNewPolarity(e.target.value)}
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
                                                        value={newConfidence}
                                                        onChange={e => setNewConfidence(parseFloat(e.target.value))}
                                                        className="w-full px-2 py-1.5 bg-white border border-blue-100 rounded-lg text-xs outline-none focus:ring-2 focus:ring-blue-500/20"
                                                    />
                                                </div>
                                            </div>

                                            <button
                                                onClick={handleCreateLink}
                                                disabled={isCreatingLink || !newTargetId}
                                                className="w-full py-2.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-all shadow-md flex items-center justify-center gap-2 group mt-2 disabled:opacity-50"
                                            >
                                                <LinkIcon size={14} className="group-hover:rotate-12 transition-transform" />
                                                Verbinding Toevoegen
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <>
                                {/* Link Statement */}
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Argumentatie</label>
                                    <textarea
                                        className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none resize-none font-medium text-slate-700"
                                        rows={3}
                                        value={statement}
                                        onChange={e => setStatement(e.target.value)}
                                    />
                                </div>

                                <div className="flex gap-4">
                                    <div className="flex-1">
                                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Polariteit</label>
                                        <div className="relative">
                                            <select
                                                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm appearance-none bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                                                value={polarity}
                                                onChange={e => setPolarity(e.target.value)}
                                            >
                                                <option value="+">Versterkend (+)</option>
                                                <option value="-">Remmend (—)</option>
                                                <option value="?">Onbekend (?)</option>
                                            </select>
                                            <ChevronDown size={14} className="absolute right-3 top-3 text-slate-400 pointer-events-none" />
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Zekerheid (0-1)</label>
                                        <input
                                            type="number" step="0.1" min="0" max="1"
                                            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                            value={confidence}
                                            onChange={e => setConfidence(parseFloat(e.target.value))}
                                        />
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-between gap-3">
                        <button
                            onClick={handleDelete}
                            className="px-4 py-2 text-xs font-bold text-red-500 hover:bg-red-50 rounded-lg border border-transparent hover:border-red-100 transition-all flex items-center gap-2"
                        >
                            <Trash2 size={14} />
                            Verwijderen
                        </button>
                        <div className="flex gap-2">
                            <Dialog.Close className="px-4 py-2 text-xs font-bold text-slate-500 hover:bg-slate-200 rounded-lg transition-all">
                                Annuleren
                            </Dialog.Close>
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="px-6 py-2 text-xs font-bold bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all flex items-center gap-2 disabled:opacity-50"
                            >
                                <Save size={14} />
                                {isSaving ? 'Opslaan...' : 'Opslaan'}
                            </button>
                        </div>
                    </div>

                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
};
