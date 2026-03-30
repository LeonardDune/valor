import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useSociaOntology } from '../../hooks/useSociaOntology';

interface Actor {
    uri: string;
    label: string;
    actor_type_uri: string;
    role_uri?: string;
}

interface EditActorModalProps {
    open: boolean;
    actor: Actor | null;
    onClose: () => void;
    onSubmit: (data: { label: string; actor_type_uri: string; role_uri?: string }) => void;
}

export function EditActorModal({ open, actor, onClose, onSubmit }: EditActorModalProps) {
    const { ontology, loading } = useSociaOntology();
    const [label, setLabel] = useState('');
    const [actorTypeUri, setActorTypeUri] = useState('');
    const [roleUri, setRoleUri] = useState('');

    useEffect(() => {
        if (actor) {
            setLabel(actor.label);
            setActorTypeUri(actor.actor_type_uri);
            setRoleUri(actor.role_uri ?? '');
        }
    }, [actor]);

    function handleSubmit() {
        if (!label.trim() || !actorTypeUri) return;
        onSubmit({ label: label.trim(), actor_type_uri: actorTypeUri, role_uri: roleUri || undefined });
    }

    return (
        <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Actor bewerken</DialogTitle>
                </DialogHeader>

                <div className="space-y-4 py-2">
                    <div className="space-y-1">
                        <Label htmlFor="edit-actor-label">Naam</Label>
                        <Input
                            id="edit-actor-label"
                            value={label}
                            onChange={(e) => setLabel(e.target.value)}
                        />
                    </div>

                    <div className="space-y-1">
                        <Label htmlFor="edit-actor-type">Type</Label>
                        <Select value={actorTypeUri} onValueChange={setActorTypeUri} disabled={loading}>
                            <SelectTrigger id="edit-actor-type">
                                <SelectValue placeholder={loading ? 'Laden...' : 'Kies een type'} />
                            </SelectTrigger>
                            <SelectContent>
                                {ontology?.actor_types.map((t) => (
                                    <SelectItem key={t.uri} value={t.uri}>
                                        {t.label_nl}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-1">
                        <Label htmlFor="edit-actor-role">Rol (optioneel)</Label>
                        <Select value={roleUri} onValueChange={setRoleUri} disabled={loading}>
                            <SelectTrigger id="edit-actor-role">
                                <SelectValue placeholder={loading ? 'Laden...' : 'Kies een rol'} />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="">— geen rol —</SelectItem>
                                {ontology?.roles.map((r) => (
                                    <SelectItem key={r.uri} value={r.uri}>
                                        {r.label_nl}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Annuleren</Button>
                    <Button onClick={handleSubmit} disabled={!label.trim() || !actorTypeUri}>
                        Opslaan
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
