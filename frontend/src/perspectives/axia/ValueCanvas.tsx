import { useCallback, useEffect, useState } from 'react';
import { Pencil, Trash2, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/services/api';
import type { ValueCanvasResponse, ValueClaimItem } from '@/services/api';

interface ValueCanvasProps {
    designSpaceId: string;
}

export function ValueCanvas({ designSpaceId }: ValueCanvasProps) {
    const [data, setData] = useState<ValueCanvasResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await api.getValueClaims(designSpaceId);
            setData(result);
        } catch {
            setError('Kon waardeclaims niet laden.');
        } finally {
            setLoading(false);
        }
    }, [designSpaceId]);

    useEffect(() => {
        load();
    }, [load]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                Waardeclaims laden...
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full text-destructive text-sm">
                {error}
            </div>
        );
    }

    if (!data || Object.keys(data.groups).length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm italic">
                Geen waardeclaims gevonden voor deze DesignSpace.
            </div>
        );
    }

    const groups = Object.entries(data.groups);

    return (
        <div className="h-full w-full overflow-x-auto">
            <div className="flex gap-4 p-4 min-h-full">
                {groups.map(([valueTypeUri, claims]) => (
                    <ValueTypeColumn
                        key={valueTypeUri}
                        designSpaceId={designSpaceId}
                        valueTypeUri={valueTypeUri}
                        valueTypeLabel={claims[0]?.value_type_label ?? valueTypeUri}
                        claims={claims}
                        onChanged={load}
                    />
                ))}
            </div>
        </div>
    );
}

interface ValueTypeColumnProps {
    designSpaceId: string;
    valueTypeUri: string;
    valueTypeLabel: string;
    claims: ValueClaimItem[];
    onChanged: () => void;
}

function ValueTypeColumn({ designSpaceId, valueTypeLabel, claims, onChanged }: ValueTypeColumnProps) {
    return (
        <div className="flex flex-col gap-2 min-w-[220px] max-w-[280px]">
            <div className="rounded-md bg-zinc-100 dark:bg-zinc-800 px-3 py-2">
                <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-200 truncate" title={valueTypeLabel}>
                    {valueTypeLabel}
                </h3>
                <span className="text-xs text-muted-foreground">{claims.length} claim{claims.length !== 1 ? 's' : ''}</span>
            </div>
            <div className="flex flex-col gap-2">
                {claims.map((claim) => (
                    <ValueClaimCard
                        key={claim.tessera_id}
                        claim={claim}
                        designSpaceId={designSpaceId}
                        onChanged={onChanged}
                    />
                ))}
            </div>
        </div>
    );
}

interface ValueClaimCardProps {
    claim: ValueClaimItem;
    designSpaceId: string;
    onChanged: () => void;
}

function ValueClaimCard({ claim, designSpaceId, onChanged }: ValueClaimCardProps) {
    const [editing, setEditing] = useState(false);
    const [content, setContent] = useState(claim.claim_content);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSave = async () => {
        if (!content.trim()) return;
        setSaving(true);
        setError(null);
        try {
            await api.updateValueClaim(designSpaceId, claim.tessera_uri, { claim_content: content.trim() });
            setEditing(false);
            onChanged();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Opslaan mislukt');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm('Waardeclaim verwijderen?')) return;
        setDeleting(true);
        setError(null);
        try {
            await api.deleteValueClaim(designSpaceId, claim.tessera_uri);
            onChanged();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Verwijderen mislukt');
            setDeleting(false);
        }
    };

    const handleCancel = () => {
        setContent(claim.claim_content);
        setEditing(false);
        setError(null);
    };

    return (
        <div className="group rounded-md border border-border bg-card p-3 shadow-sm">
            {editing ? (
                <div className="space-y-2">
                    <Input
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        className="text-sm"
                        autoFocus
                    />
                    {error && <p className="text-xs text-destructive">{error}</p>}
                    <div className="flex gap-1 justify-end">
                        <Button type="button" variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={handleCancel}>
                            <X className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={handleSave}
                            disabled={saving || !content.trim()}
                        >
                            <Check className="h-3.5 w-3.5" />
                        </Button>
                    </div>
                </div>
            ) : (
                <>
                    <p className="text-sm text-card-foreground leading-snug">{claim.claim_content}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                        Door {claim.claimed_by} &middot; {new Date(claim.claimed_at).toLocaleDateString('nl-NL')}
                    </p>
                    <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity justify-end">
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
                            onClick={() => setEditing(true)}
                        >
                            <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                            onClick={handleDelete}
                            disabled={deleting}
                        >
                            <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                    </div>
                    {error && <p className="text-xs text-destructive mt-1">{error}</p>}
                </>
            )}
        </div>
    );
}
