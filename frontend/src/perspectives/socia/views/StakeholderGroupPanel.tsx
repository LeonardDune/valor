import { useCallback, useEffect, useState } from 'react';
import { Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    api,
    type InterestLevel,
    type StakeholderGroup,
} from '@/services/api';

// ---------------------------------------------------------------------------
// Constanten
// ---------------------------------------------------------------------------

const INTEREST_OPTIONS: { value: InterestLevel; label: string }[] = [
    { value: 'High', label: 'Hoog' },
    { value: 'Medium', label: 'Middel' },
    { value: 'Low', label: 'Laag' },
];

const INTEREST_BADGE_CLASS: Record<InterestLevel, string> = {
    High: 'bg-destructive/15 text-destructive border-destructive/30',
    Medium: 'bg-yellow-500/15 text-yellow-700 border-yellow-500/30 dark:text-yellow-400',
    Low: 'bg-green-500/15 text-green-700 border-green-500/30 dark:text-green-400',
};

// ---------------------------------------------------------------------------
// Groepskaart
// ---------------------------------------------------------------------------

function GroupCard({ group }: { group: StakeholderGroup }) {
    const interestOpt = INTEREST_OPTIONS.find((o) => o.value === group.interest_level);

    return (
        <div className="border border-border rounded-lg p-3 space-y-1.5 bg-card">
            <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                    <Users className="h-4 w-4 shrink-0 text-primary" />
                    <span className="text-sm font-medium truncate">{group.label}</span>
                </div>
                <Badge
                    variant="outline"
                    className={`text-xs shrink-0 ${INTEREST_BADGE_CLASS[group.interest_level]}`}
                >
                    {interestOpt?.label ?? group.interest_level}
                </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
                Vertegenwoordigd:{' '}
                <span className={group.is_represented ? 'text-primary' : 'text-muted-foreground'}>
                    {group.is_represented ? 'Ja' : 'Nee'}
                </span>
            </p>
            {group.represented_by_uri && (
                <p className="text-xs text-muted-foreground truncate" title={group.represented_by_uri}>
                    {group.represented_by_uri}
                </p>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Aanmaakformulier
// ---------------------------------------------------------------------------

interface CreateFormProps {
    dsId: string;
    onCreated: () => void;
    onCancel: () => void;
}

function CreateStakeholderGroupForm({ dsId, onCreated, onCancel }: CreateFormProps) {
    const [label, setLabel] = useState('');
    const [interestLevel, setInterestLevel] = useState<InterestLevel>('Medium');
    const [representedByUri, setRepresentedByUri] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!label.trim()) return;
        setSubmitting(true);
        setError(null);
        try {
            await api.createStakeholderGroup(dsId, {
                label: label.trim(),
                interest_level: interestLevel,
                represented_by_uri: representedByUri.trim() || undefined,
            });
            onCreated();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Onbekende fout');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4 border border-border rounded-lg p-4 bg-muted/30">
            <p className="text-sm font-medium">Nieuwe StakeholderGroep</p>

            <div className="space-y-1.5">
                <Label htmlFor="sg-label">Naam</Label>
                <Input
                    id="sg-label"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    placeholder="Naam van de stakeholdergroep"
                    required
                />
            </div>

            <div className="space-y-1.5">
                <Label htmlFor="sg-interest">Interesseniveau</Label>
                <Select
                    value={interestLevel}
                    onValueChange={(v) => setInterestLevel(v as InterestLevel)}
                >
                    <SelectTrigger id="sg-interest">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        {INTEREST_OPTIONS.map((opt) => (
                            <SelectItem key={opt.value} value={opt.value}>
                                {opt.label}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <div className="space-y-1.5">
                <Label htmlFor="sg-represented">Vertegenwoordigd door (optioneel)</Label>
                <Input
                    id="sg-represented"
                    value={representedByUri}
                    onChange={(e) => setRepresentedByUri(e.target.value)}
                    placeholder="URI van IssueCommunity-lid"
                />
            </div>

            {error && <p className="text-xs text-destructive">{error}</p>}

            <div className="flex gap-2 justify-end">
                <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
                    Annuleren
                </Button>
                <Button type="submit" size="sm" disabled={submitting || !label.trim()}>
                    {submitting ? 'Opslaan\u2026' : 'Aanmaken'}
                </Button>
            </div>
        </form>
    );
}

// ---------------------------------------------------------------------------
// Hoofdcomponent
// ---------------------------------------------------------------------------

interface StakeholderGroupPanelProps {
    dsId: string;
}

export function StakeholderGroupPanel({ dsId }: StakeholderGroupPanelProps) {
    const [groups, setGroups] = useState<StakeholderGroup[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await api.getStakeholderGroups(dsId);
            setGroups(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Onbekende fout');
        } finally {
            setLoading(false);
        }
    }, [dsId]);

    useEffect(() => {
        load();
    }, [load]);

    const handleCreated = () => {
        setShowForm(false);
        load();
    };

    return (
        <div className="flex flex-col gap-4 p-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold">StakeholderGroepen</span>
                    {groups.length > 0 && (
                        <Badge variant="secondary" className="text-xs">
                            {groups.length}
                        </Badge>
                    )}
                </div>
                {!showForm && (
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowForm(true)}
                        className="gap-1"
                    >
                        <span className="text-base leading-none">+</span>
                        Nieuw
                    </Button>
                )}
            </div>

            {showForm && (
                <CreateStakeholderGroupForm
                    dsId={dsId}
                    onCreated={handleCreated}
                    onCancel={() => setShowForm(false)}
                />
            )}

            {loading && (
                <p className="text-xs text-muted-foreground">Laden\u2026</p>
            )}

            {error && (
                <div className="flex flex-col gap-1">
                    <p className="text-xs text-destructive">Fout: {error}</p>
                    <button
                        type="button"
                        onClick={load}
                        className="text-xs underline text-muted-foreground hover:text-foreground self-start"
                    >
                        Opnieuw proberen
                    </button>
                </div>
            )}

            {!loading && !error && groups.length === 0 && !showForm && (
                <p className="text-xs text-muted-foreground">
                    Nog geen StakeholderGroepen in deze DesignSpace.
                </p>
            )}

            {groups.map((group) => (
                <GroupCard key={group.group_uri} group={group} />
            ))}
        </div>
    );
}
