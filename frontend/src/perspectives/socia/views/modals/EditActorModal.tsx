import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useSociaOntology } from '../../hooks/useSociaOntology';
import { api } from '@/services/api';

interface ActorRoleEntry {
    entity_uri: string;
    entity_label?: string;
    entity_type_local?: string;
    role_uri: string;
    role_label_nl?: string;
}

interface EditActorModalProps {
    dsId: string;
    open: boolean;
    actor: ActorRoleEntry | null;
    onClose: () => void;
    onSubmit: (entityUri: string, roleUri?: string) => void;
}

export function EditActorModal({ dsId, open, actor, onClose, onSubmit }: EditActorModalProps) {
    const { ontology, loading: ontologyLoading } = useSociaOntology();
    const [roleUri, setRoleUri] = useState('');
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (actor) setRoleUri(actor.role_uri ?? '');
    }, [actor]);

    async function handleSave() {
        if (!actor) return;
        setSaving(true);
        try {
            if (roleUri && roleUri !== actor.role_uri) {
                await api.assignSociaRole(dsId, actor.entity_uri, roleUri);
            }
            onSubmit(actor.entity_uri, roleUri || undefined);
            onClose();
        } finally {
            setSaving(false);
        }
    }

    const displayName = actor?.entity_label ?? actor?.entity_uri.split(':').pop() ?? '';
    const typeLabel = actor?.entity_type_local ?? '';

    return (
        <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Actor bewerken</DialogTitle>
                </DialogHeader>

                <div className="space-y-4 py-2">
                    {/* Entity Registry profiel — read-only */}
                    <div className="rounded-md border border-border bg-muted/40 px-3 py-2 space-y-1">
                        <p className="text-xs text-muted-foreground">Registerprofiel (alleen-lezen)</p>
                        <p className="text-sm font-medium">{displayName}</p>
                        {typeLabel && (
                            <p className="text-xs text-muted-foreground">{typeLabel}</p>
                        )}
                        <p className="text-xs text-muted-foreground font-mono truncate">{actor?.entity_uri}</p>
                    </div>

                    {/* Rolassignatie — bewerkbaar */}
                    <div className="space-y-1">
                        <Label htmlFor="edit-role">Rol in deze werkruimte</Label>
                        <Select value={roleUri} onValueChange={setRoleUri} disabled={ontologyLoading}>
                            <SelectTrigger id="edit-role">
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
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Annuleren</Button>
                    <Button onClick={handleSave} disabled={saving || !actor}>
                        {saving ? 'Opslaan…' : 'Opslaan'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
