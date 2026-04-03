import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
    api,
    type StakeholderClaimType,
    type StakeholderClaimResponse,
    type StakeholderActor,
} from '@/services/api';

// ---------------------------------------------------------------------------
// Claim-type metadata
// ---------------------------------------------------------------------------

const CLAIM_TYPE_OPTIONS: { value: StakeholderClaimType; label: string; description: string }[] = [
    {
        value: 'InterestClaim',
        label: 'Belang',
        description: 'Wat heeft de actor te winnen of verliezen?',
    },
    {
        value: 'GoalClaim',
        label: 'Doel',
        description: 'Wat wil de actor bereiken?',
    },
    {
        value: 'PowerClaim',
        label: 'Macht',
        description: 'Welke invloed of macht heeft de actor?',
    },
];

const STATUS_LABEL: Record<string, string> = {
    Proposed: 'Voorgesteld',
    Accepted: 'Geaccepteerd',
    Rejected: 'Verworpen',
};

// ---------------------------------------------------------------------------
// Subcomponent: ingediende claim
// ---------------------------------------------------------------------------

function ClaimItem({ claim }: { claim: StakeholderClaimResponse }) {
    const typeMeta = CLAIM_TYPE_OPTIONS.find((o) => o.value === claim.claim_type);
    const statusLabel = STATUS_LABEL[claim.epistemic_status] ?? claim.epistemic_status;

    return (
        <div className="rounded-md border border-border bg-card p-3 space-y-1">
            <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                    {typeMeta?.label ?? claim.claim_type}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                    {statusLabel}
                </Badge>
            </div>
            <p className="text-sm">{claim.claim_content}</p>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Hoofdcomponent
// ---------------------------------------------------------------------------

interface StakeholderClaimsPanelProps {
    dsId: string;
    actors: StakeholderActor[];
}

export function StakeholderClaimsPanel({ dsId, actors }: StakeholderClaimsPanelProps) {
    const [actorUri, setActorUri] = useState('');
    const [claimType, setClaimType] = useState<StakeholderClaimType | ''>('');
    const [content, setContent] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [submitted, setSubmitted] = useState<StakeholderClaimResponse[]>([]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!actorUri || !claimType || !content.trim()) return;

        setSubmitting(true);
        setError(null);
        try {
            const result = await api.createStakeholderClaim(dsId, {
                claim_type: claimType,
                claim_content: content.trim(),
                actor_uri: actorUri,
            });
            setSubmitted((prev) => [result, ...prev]);
            setContent('');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Onbekende fout');
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="flex flex-col gap-4 p-4">
            <h3 className="text-sm font-semibold">Stakeholderclaim toevoegen</h3>

            <form onSubmit={handleSubmit} className="space-y-3">
                {/* Actor selectie */}
                <div className="space-y-1">
                    <Label htmlFor="sc-actor">Actor</Label>
                    <Select value={actorUri} onValueChange={setActorUri}>
                        <SelectTrigger id="sc-actor">
                            <SelectValue placeholder="Kies een actor" />
                        </SelectTrigger>
                        <SelectContent>
                            {actors.map((a) => (
                                <SelectItem key={a.uri} value={a.uri}>
                                    {a.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                {/* Claim-type */}
                <div className="space-y-1">
                    <Label htmlFor="sc-type">Type claim</Label>
                    <Select
                        value={claimType}
                        onValueChange={(v) => setClaimType(v as StakeholderClaimType)}
                    >
                        <SelectTrigger id="sc-type">
                            <SelectValue placeholder="Kies een type" />
                        </SelectTrigger>
                        <SelectContent>
                            {CLAIM_TYPE_OPTIONS.map((o) => (
                                <SelectItem key={o.value} value={o.value}>
                                    <span>{o.label}</span>
                                    <span className="ml-2 text-xs text-muted-foreground">
                                        {o.description}
                                    </span>
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                {/* Inhoud */}
                <div className="space-y-1">
                    <Label htmlFor="sc-content">Inhoud</Label>
                    <Input
                        id="sc-content"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        placeholder="Beschrijf de claim…"
                    />
                </div>

                {error && (
                    <p className="text-xs text-destructive">{error}</p>
                )}

                <Button
                    type="submit"
                    disabled={!actorUri || !claimType || !content.trim() || submitting}
                    className="w-full"
                >
                    {submitting ? 'Opslaan…' : 'Claim opslaan'}
                </Button>
            </form>

            {/* Ingediende claims in deze sessie */}
            {submitted.length > 0 && (
                <div className="space-y-2">
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                        Zojuist toegevoegd
                    </p>
                    {submitted.map((c) => (
                        <ClaimItem key={c.tessera_id} claim={c} />
                    ))}
                </div>
            )}
        </div>
    );
}
