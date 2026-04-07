import { useEffect, useState } from 'react';
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
    type StakeholderClaimResponse,
    type StakeholderActor,
    type SociaOntologyEntry,
} from '@/services/api';

const STATUS_LABEL: Record<string, string> = {
    Proposed: 'Voorgesteld',
    Accepted: 'Geaccepteerd',
    Rejected: 'Verworpen',
};

function ClaimItem({ claim, claimTypes }: { claim: StakeholderClaimResponse; claimTypes: SociaOntologyEntry[] }) {
    const typeMeta = claimTypes.find((t) => t.uri === claim.claim_type_uri);
    const statusLabel = STATUS_LABEL[claim.epistemic_status] ?? claim.epistemic_status;

    return (
        <div className="rounded-md border border-border bg-card p-3 space-y-1">
            <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                    {typeMeta?.label_nl ?? typeMeta?.label_en ?? claim.claim_type_uri.split('#').pop()}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                    {statusLabel}
                </Badge>
            </div>
            <p className="text-sm">{claim.claim_content}</p>
        </div>
    );
}

interface StakeholderClaimsPanelProps {
    dsId: string;
    actors: StakeholderActor[];
}

export function StakeholderClaimsPanel({ dsId, actors }: StakeholderClaimsPanelProps) {
    const [actorUri, setActorUri] = useState('');
    const [claimTypeUri, setClaimTypeUri] = useState('');
    const [content, setContent] = useState('');
    const [claimTypes, setClaimTypes] = useState<SociaOntologyEntry[]>([]);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [submitted, setSubmitted] = useState<StakeholderClaimResponse[]>([]);

    useEffect(() => {
        api.getSociaOntology().then((ont) => {
            setClaimTypes(ont.claim_types);
            if (ont.claim_types.length > 0 && !claimTypeUri) {
                setClaimTypeUri(ont.claim_types[0].uri);
            }
        }).catch(() => {/* ontologie niet beschikbaar */});
    }, []);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!actorUri || !claimTypeUri || !content.trim()) return;

        setSubmitting(true);
        setError(null);
        try {
            const result = await api.createStakeholderClaim(dsId, {
                claim_type_uri: claimTypeUri,
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

                <div className="space-y-1">
                    <Label htmlFor="sc-type">Type claim</Label>
                    <Select value={claimTypeUri} onValueChange={setClaimTypeUri}>
                        <SelectTrigger id="sc-type">
                            <SelectValue placeholder="Kies een type" />
                        </SelectTrigger>
                        <SelectContent>
                            {claimTypes.map((t) => (
                                <SelectItem key={t.uri} value={t.uri}>
                                    {t.label_nl || t.label_en || t.local_name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

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
                    disabled={!actorUri || !claimTypeUri || !content.trim() || submitting}
                    className="w-full"
                >
                    {submitting ? 'Opslaan…' : 'Claim opslaan'}
                </Button>
            </form>

            {submitted.length > 0 && (
                <div className="space-y-2">
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                        Zojuist toegevoegd
                    </p>
                    {submitted.map((c) => (
                        <ClaimItem key={c.tessera_id} claim={c} claimTypes={claimTypes} />
                    ))}
                </div>
            )}
        </div>
    );
}
