import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useSociaOntology } from '../../hooks/useSociaOntology';
import { api, type EntityRegistryEntry } from '@/services/api';

type Step = 'search' | 'create-new';

interface CreateActorModalProps {
    dsId: string;
    open: boolean;
    onClose: () => void;
    onSubmit: (entityUri: string, roleUri?: string) => void;
}

export function CreateActorModal({ dsId, open, onClose, onSubmit }: CreateActorModalProps) {
    const { ontology, loading: ontologyLoading } = useSociaOntology();

    const [step, setStep] = useState<Step>('search');
    const [query, setQuery] = useState('');
    const [searchResults, setSearchResults] = useState<EntityRegistryEntry[]>([]);
    const [searching, setSearching] = useState(false);
    const [selectedUri, setSelectedUri] = useState('');
    const [roleUri, setRoleUri] = useState('');

    // Nieuwe actor aanmaken
    const [newLabel, setNewLabel] = useState('');
    const [newTypeUri, setNewTypeUri] = useState('');
    const [creating, setCreating] = useState(false);

    async function handleSearch() {
        if (!query.trim()) return;
        setSearching(true);
        try {
            const results = await api.searchEntities(query.trim());
            setSearchResults(results);
        } finally {
            setSearching(false);
        }
    }

    async function handleSelectExisting() {
        if (!selectedUri) return;
        if (roleUri) {
            await api.assignSociaRole(dsId, selectedUri, roleUri);
        }
        onSubmit(selectedUri, roleUri || undefined);
        handleClose();
    }

    async function handleCreateNew() {
        if (!newLabel.trim() || !newTypeUri) return;
        setCreating(true);
        try {
            const typeLocalName = newTypeUri.split('#').pop() ?? 'PhysicalAgent';
            const entry = await api.createEntity({ entity_type: typeLocalName, label: newLabel.trim() });
            if (roleUri) {
                await api.assignSociaRole(dsId, entry.uri, roleUri);
            }
            onSubmit(entry.uri, roleUri || undefined);
            handleClose();
        } finally {
            setCreating(false);
        }
    }

    function handleClose() {
        setStep('search');
        setQuery('');
        setSearchResults([]);
        setSelectedUri('');
        setRoleUri('');
        setNewLabel('');
        setNewTypeUri('');
        onClose();
    }

    return (
        <Dialog open={open} onOpenChange={(o) => { if (!o) handleClose(); }}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Actor toevoegen</DialogTitle>
                </DialogHeader>

                {step === 'search' && (
                    <div className="space-y-4 py-2">
                        <div className="space-y-1">
                            <Label>Zoek in register</Label>
                            <div className="flex gap-2">
                                <Input
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                    placeholder="Naam van persoon, organisatie…"
                                />
                                <Button variant="outline" onClick={handleSearch} disabled={searching}>
                                    {searching ? 'Zoeken…' : 'Zoeken'}
                                </Button>
                            </div>
                        </div>

                        {searchResults.length > 0 && (
                            <div className="space-y-1">
                                <Label>Resultaten</Label>
                                <div className="border rounded-md divide-y max-h-48 overflow-y-auto">
                                    {searchResults.map((entry) => (
                                        <button
                                            key={entry.uri}
                                            type="button"
                                            onClick={() => setSelectedUri(entry.uri)}
                                            className={`w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors ${selectedUri === entry.uri ? 'bg-muted font-medium' : ''}`}
                                        >
                                            <span>{entry.label ?? entry.uri.split(':').pop()}</span>
                                            {entry.entity_type_local && (
                                                <span className="ml-2 text-xs text-muted-foreground">{entry.entity_type_local}</span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {searchResults.length === 0 && query && !searching && (
                            <p className="text-sm text-muted-foreground">
                                Geen resultaten. Je kunt een nieuwe externe actor aanmaken.
                            </p>
                        )}

                        <div className="space-y-1">
                            <Label htmlFor="role-select">Rol (optioneel)</Label>
                            <Select value={roleUri} onValueChange={setRoleUri} disabled={ontologyLoading}>
                                <SelectTrigger id="role-select">
                                    <SelectValue placeholder={ontologyLoading ? 'Laden…' : 'Kies een rol'} />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="">— geen rol —</SelectItem>
                                    {ontology?.roles.map((r) => (
                                        <SelectItem key={r.uri} value={r.uri}>{r.label_nl}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <DialogFooter className="flex-col sm:flex-row gap-2">
                            <Button variant="outline" onClick={() => setStep('create-new')} className="sm:mr-auto">
                                Nieuwe externe actor
                            </Button>
                            <Button variant="outline" onClick={handleClose}>Annuleren</Button>
                            <Button onClick={handleSelectExisting} disabled={!selectedUri}>
                                Toevoegen
                            </Button>
                        </DialogFooter>
                    </div>
                )}

                {step === 'create-new' && (
                    <div className="space-y-4 py-2">
                        <div className="space-y-1">
                            <Label htmlFor="new-label">Naam</Label>
                            <Input
                                id="new-label"
                                value={newLabel}
                                onChange={(e) => setNewLabel(e.target.value)}
                                placeholder="Naam van de actor"
                            />
                        </div>

                        <div className="space-y-1">
                            <Label htmlFor="new-type">Type</Label>
                            <Select value={newTypeUri} onValueChange={setNewTypeUri} disabled={ontologyLoading}>
                                <SelectTrigger id="new-type">
                                    <SelectValue placeholder={ontologyLoading ? 'Laden…' : 'Kies een type'} />
                                </SelectTrigger>
                                <SelectContent>
                                    {ontology?.actor_types.map((t) => (
                                        <SelectItem key={t.uri} value={t.uri}>{t.label_nl}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-1">
                            <Label htmlFor="new-role">Rol (optioneel)</Label>
                            <Select value={roleUri} onValueChange={setRoleUri} disabled={ontologyLoading}>
                                <SelectTrigger id="new-role">
                                    <SelectValue placeholder={ontologyLoading ? 'Laden…' : 'Kies een rol'} />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="">— geen rol —</SelectItem>
                                    {ontology?.roles.map((r) => (
                                        <SelectItem key={r.uri} value={r.uri}>{r.label_nl}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <DialogFooter>
                            <Button variant="outline" onClick={() => setStep('search')}>Terug</Button>
                            <Button onClick={handleCreateNew} disabled={!newLabel.trim() || !newTypeUri || creating}>
                                {creating ? 'Aanmaken…' : 'Aanmaken'}
                            </Button>
                        </DialogFooter>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
