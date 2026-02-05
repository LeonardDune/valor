import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { toast } from "sonner";
import {
    Trash2,
    Type,
    Link as LinkIcon,
    Save
} from 'lucide-react';
import { api, type FactorType } from '../../../../services/api';

interface EditFactorDetailModalProps {
    selection: { type: 'node' | 'link'; data: any } | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onRefresh: () => void;
    factors: any[];
    themeId: string;
    readOnly?: boolean;
}

export const EditFactorDetailModal: React.FC<EditFactorDetailModalProps> = ({
    selection,
    open,
    onOpenChange,
    onRefresh,
    factors: _factors,
    themeId,
    readOnly = false
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
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

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
            setName(data.label || '');
            setDescription(data.description || '');
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

            let formPolarity = '+';
            if (data.polarity === 'negative') formPolarity = '-';
            if (data.polarity === 'ambiguous') formPolarity = '?';
            if (data.polarity === '+' || data.polarity === '-' || data.polarity === '?') formPolarity = data.polarity;

            setPolarity(formPolarity);
            setConfidence(data.certainty ?? data.confidence ?? 0.5);

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
            toast.success("Wijzigingen opgeslagen.");
            onRefresh();
            onOpenChange(false);
        } catch (err) {
            console.error(err);
            toast.error("Fout bij het opslaan van wijzigingen.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!selection) return;
        setIsSaving(true);
        try {
            if (selection.type === 'node') {
                await api.deleteFactor(selection.data.id);
            } else {
                await api.deleteClaim(selection.data.id);
            }
            toast.success("Item verwijderd.");
            onRefresh();
            onOpenChange(false);
        } catch (err) {
            console.error(err);
            toast.error("Fout bij het verwijderen van item.");
        } finally {
            setIsSaving(false);
            setIsDeleteDialogOpen(false);
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
            setNewTargetId('');
            onRefresh();
            toast.success("Verbinding aangemaakt!");
        } catch (e) {
            console.error('Failed to create claim', e);
            toast.error("Fout bij het maken van verbinding.");
        } finally {
            setIsCreatingLink(false);
        }
    };

    if (!selection) return null;

    const isNode = selection.type === 'node';
    const sortedFactors = [..._factors].sort((a, b) => (a.name || '').localeCompare(b.name || ''));

    return (
        <>
            <Dialog open={open} onOpenChange={onOpenChange}>
                <DialogContent className="sm:max-w-[425px] overflow-y-auto max-h-[90vh]">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            {isNode ? <Type size={16} className="text-blue-500" /> : <LinkIcon size={16} className="text-indigo-500" />}
                            {isNode
                                ? (readOnly ? 'Factor Details' : 'Factor Bewerken')
                                : (readOnly ? 'Verbinding Details' : 'Verbinding Bewerken')}
                        </DialogTitle>
                    </DialogHeader>

                    <div className="grid gap-4 py-4">
                        {isNode ? (
                            <>
                                <div className="grid gap-2">
                                    <Label htmlFor="name">Naam</Label>
                                    <Input id="name" value={name} onChange={e => setName(e.target.value)} disabled={readOnly} />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="role">Rol (TU Delft)</Label>
                                    <Select value={type} onValueChange={(val) => setType(val as FactorType)} disabled={readOnly}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Selecteer rol" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="middel">Middel (Means)</SelectItem>
                                            <SelectItem value="extern">Externe Factor</SelectItem>
                                            <SelectItem value="systeemelement">Systeemelement</SelectItem>
                                            <SelectItem value="criterium">Criterium (Doel)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="description">Beschrijving</Label>
                                    <Textarea id="description" value={description} onChange={e => setDescription(e.target.value)} disabled={readOnly} />
                                </div>

                                {(!readOnly && _factors.length > 1 && selection.data) && (
                                    <div className="border-t pt-4 mt-2">
                                        <Label className="mb-2 block text-blue-500">Nieuwe Verbinding</Label>
                                        <div className="space-y-3 bg-slate-50 p-3 rounded-md">
                                            <div className="grid gap-1">
                                                <Label className="text-xs">Doel Factor</Label>
                                                <Select value={newTargetId} onValueChange={setNewTargetId}>
                                                    <SelectTrigger className="h-8 text-xs">
                                                        <SelectValue placeholder="Kies factor..." />
                                                    </SelectTrigger>
                                                    <SelectContent className="max-h-[200px]">
                                                        {sortedFactors
                                                            .filter(f => (f.dbId || f.id) !== (selection.data.dbId || selection.data.id))
                                                            .map(f => (
                                                                <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>
                                                            ))
                                                        }
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="grid gap-1">
                                                <Label className="text-xs">Argumentatie</Label>
                                                <Textarea
                                                    value={newStatement}
                                                    onChange={e => setNewStatement(e.target.value)}
                                                    className="h-16 text-xs"
                                                    placeholder="Waarom?"
                                                />
                                            </div>
                                            <div className="flex gap-2">
                                                <div className="flex-1">
                                                    <Label className="text-xs">Polariteit</Label>
                                                    <Select value={newPolarity} onValueChange={setNewPolarity}>
                                                        <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="+">+</SelectItem>
                                                            <SelectItem value="-">-</SelectItem>
                                                            <SelectItem value="?">?</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                                <div className="flex-1">
                                                    <Label className="text-xs">Zekerheid</Label>
                                                    <Input
                                                        type="number" step="0.1" min="0" max="1"
                                                        value={newConfidence}
                                                        onChange={e => setNewConfidence(parseFloat(e.target.value))}
                                                        className="h-8 text-xs"
                                                    />
                                                </div>
                                            </div>
                                            <Button size="sm" onClick={handleCreateLink} disabled={!newTargetId || isCreatingLink} className="w-full">
                                                {isCreatingLink ? 'Bezig...' : <><LinkIcon size={12} className="mr-2" /> Toevoegen</>}
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <>
                                <div className="flex flex-col gap-4 bg-muted/50 p-3 rounded-md mb-4">
                                    <div className="grid gap-1">
                                        <Label className="text-xs text-muted-foreground uppercase tracking-wider">Van</Label>
                                        <div className="text-sm font-medium leading-relaxed break-words">
                                            {_factors.find(f => f.id === sourceId)?.name || sourceId}
                                        </div>
                                    </div>
                                    <div className="grid gap-1 border-t border-black/5 pt-2">
                                        <Label className="text-xs text-muted-foreground uppercase tracking-wider">Naar</Label>
                                        <div className="text-sm font-medium leading-relaxed break-words">
                                            {_factors.find(f => f.id === targetId)?.name || targetId}
                                        </div>
                                    </div>
                                </div>

                                <div className="grid gap-2">
                                    <Label htmlFor="statement">Claim</Label>
                                    <Textarea id="statement" value={statement} onChange={e => setStatement(e.target.value)} disabled={readOnly} />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="grid gap-2">
                                        <Label>Polariteit</Label>
                                        <Select value={polarity} onValueChange={setPolarity} disabled={readOnly}>
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="+">Versterkend (+)</SelectItem>
                                                <SelectItem value="-">Remmend (—)</SelectItem>
                                                <SelectItem value="?">Onbekend (?)</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="grid gap-2">
                                        <Label>Zekerheid</Label>
                                        <Input
                                            type="number" step="0.1" min="0" max="1"
                                            value={confidence}
                                            onChange={e => setConfidence(parseFloat(e.target.value))}
                                            disabled={readOnly}
                                        />
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    <DialogFooter className="flex justify-between sm:justify-between">
                        {readOnly ? (
                            <div className="flex justify-end w-full">
                                <Button variant="secondary" onClick={() => onOpenChange(false)}>
                                    Sluiten
                                </Button>
                            </div>
                        ) : (
                            <>
                                <Button variant="destructive" size="sm" onClick={() => setIsDeleteDialogOpen(true)} disabled={isSaving}>
                                    <Trash2 size={14} className="mr-2" /> Verwijderen
                                </Button>
                                <div className="flex gap-2">
                                    <DialogClose asChild>
                                        <Button variant="outline" size="sm">Annuleren</Button>
                                    </DialogClose>
                                    <Button size="sm" onClick={handleSave} disabled={isSaving}>
                                        <Save size={14} className="mr-2" /> {isSaving ? 'Opslaan...' : 'Opslaan'}
                                    </Button>
                                </div>
                            </>
                        )}
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <ConfirmModal
                isOpen={isDeleteDialogOpen}
                title="Verwijderen Bevestigen"
                message={`Weet je zeker dat je deze ${isNode ? 'factor' : 'verbinding'} wilt verwijderen? Dit kan niet ongedaan worden gemaakt.`}
                onConfirm={handleDelete}
                onCancel={() => setIsDeleteDialogOpen(false)}
            />
        </>
    );
};
