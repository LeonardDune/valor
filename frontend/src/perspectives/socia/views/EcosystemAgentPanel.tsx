import { useCallback, useEffect, useState } from 'react';
import { Building2, ChevronDown, ChevronUp, Plus } from 'lucide-react';
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
    type CommitmentDuration,
    type EcosystemAgent,
} from '@/services/api';

// ---------------------------------------------------------------------------
// Constanten
// ---------------------------------------------------------------------------

const COMMITMENT_OPTIONS: { value: CommitmentDuration; label: string }[] = [
    { value: 'Permanent', label: 'Permanent' },
    { value: 'ProjectBased', label: 'Projectgebonden' },
    { value: 'Experimental', label: 'Experimenteel' },
];

const CONDITION_BADGE_VARIANT: Record<EcosystemAgent['condition_status'], 'default' | 'secondary' | 'destructive'> = {
    Volledig: 'default',
    Gedeeltelijk: 'secondary',
    Onvolledig: 'destructive',
};

// ---------------------------------------------------------------------------
// Subcomponent: EcosystemAgent-kaart
// ---------------------------------------------------------------------------

function AgentCard({ agent }: { agent: EcosystemAgent }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="border border-border rounded-lg p-3 space-y-2 bg-card">
            <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                    <Building2 className="h-4 w-4 shrink-0 text-primary" />
                    <span className="text-sm font-medium truncate">{agent.label}</span>
                    <Badge
                        variant="outline"
                        className="text-xs shrink-0 border-primary/40 text-primary"
                    >
                        NEXUS
                    </Badge>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                    <Badge variant={CONDITION_BADGE_VARIANT[agent.condition_status]} className="text-xs">
                        {agent.condition_status}
                    </Badge>
                    <button
                        type="button"
                        onClick={() => setExpanded((v) => !v)}
                        className="text-muted-foreground hover:text-foreground"
                        aria-label={expanded ? 'Inklappen' : 'Uitklappen'}
                    >
                        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                </div>
            </div>

            {agent.commitment_duration && (
                <p className="text-xs text-muted-foreground">
                    Commitment:{' '}
                    {COMMITMENT_OPTIONS.find((o) => o.value === agent.commitment_duration)?.label ??
                        agent.commitment_duration}
                </p>
            )}

            {expanded && (
                <div className="pt-2 space-y-2 border-t border-border">
                    <div className="grid grid-cols-3 gap-1 text-xs">
                        <span
                            className={`px-2 py-1 rounded text-center ${agent.condition_layers.commitment ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}
                        >
                            Commitment
                        </span>
                        <span
                            className={`px-2 py-1 rounded text-center ${agent.condition_layers.architecture ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}
                        >
                            Architectuur
                        </span>
                        <span
                            className={`px-2 py-1 rounded text-center ${agent.condition_layers.disposition_config ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}
                        >
                            Dispositie
                        </span>
                    </div>
                    {agent.member_agent_uris.length > 0 && (
                        <div>
                            <p className="text-xs text-muted-foreground mb-1">
                                Leden ({agent.member_agent_uris.length}):
                            </p>
                            <ul className="space-y-0.5">
                                {agent.member_agent_uris.map((uri) => (
                                    <li key={uri} className="text-xs text-muted-foreground truncate">
                                        {uri.split(':').pop()}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
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

function CreateEcosystemAgentForm({ dsId, onCreated, onCancel }: CreateFormProps) {
    const [label, setLabel] = useState('');
    const [commitmentDuration, setCommitmentDuration] = useState<CommitmentDuration>('Permanent');
    const [memberInput, setMemberInput] = useState('');
    const [memberUris, setMemberUris] = useState<string[]>([]);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const addMember = () => {
        const trimmed = memberInput.trim();
        if (trimmed && !memberUris.includes(trimmed)) {
            setMemberUris((prev) => [...prev, trimmed]);
            setMemberInput('');
        }
    };

    const removeMember = (uri: string) => {
        setMemberUris((prev) => prev.filter((u) => u !== uri));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!label.trim()) return;
        setSubmitting(true);
        setError(null);
        try {
            await api.createEcosystemAgent(dsId, {
                label: label.trim(),
                commitment_duration: commitmentDuration,
                member_agent_uris: memberUris,
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
            <p className="text-sm font-medium">Nieuw EcosystemAgent</p>

            <div className="space-y-1.5">
                <Label htmlFor="ea-label">Naam</Label>
                <Input
                    id="ea-label"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    placeholder="Naam van het ecosysteem-netwerk"
                    required
                />
            </div>

            <div className="space-y-1.5">
                <Label htmlFor="ea-commitment">Commitment-duur</Label>
                <Select
                    value={commitmentDuration}
                    onValueChange={(v) => setCommitmentDuration(v as CommitmentDuration)}
                >
                    <SelectTrigger id="ea-commitment">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        {COMMITMENT_OPTIONS.map((opt) => (
                            <SelectItem key={opt.value} value={opt.value}>
                                {opt.label}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <div className="space-y-1.5">
                <Label>Leden (optioneel)</Label>
                <div className="flex gap-2">
                    <Input
                        value={memberInput}
                        onChange={(e) => setMemberInput(e.target.value)}
                        placeholder="urn:valor:entities:..."
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                addMember();
                            }
                        }}
                    />
                    <Button type="button" variant="outline" size="sm" onClick={addMember}>
                        Toevoegen
                    </Button>
                </div>
                {memberUris.length > 0 && (
                    <ul className="space-y-1 mt-1">
                        {memberUris.map((uri) => (
                            <li key={uri} className="flex items-center justify-between text-xs">
                                <span className="truncate text-muted-foreground">{uri}</span>
                                <button
                                    type="button"
                                    onClick={() => removeMember(uri)}
                                    className="text-destructive hover:underline ml-2 shrink-0"
                                >
                                    Verwijder
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {error && <p className="text-xs text-destructive">{error}</p>}

            <div className="flex gap-2 justify-end">
                <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
                    Annuleren
                </Button>
                <Button type="submit" size="sm" disabled={submitting || !label.trim()}>
                    {submitting ? 'Opslaan…' : 'Aanmaken'}
                </Button>
            </div>
        </form>
    );
}

// ---------------------------------------------------------------------------
// Hoofdcomponent
// ---------------------------------------------------------------------------

interface EcosystemAgentPanelProps {
    dsId: string;
}

export function EcosystemAgentPanel({ dsId }: EcosystemAgentPanelProps) {
    const [agents, setAgents] = useState<EcosystemAgent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await api.getEcosystemAgents(dsId);
            setAgents(data);
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
                    <Building2 className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold">EcosystemAgents</span>
                    {agents.length > 0 && (
                        <Badge variant="secondary" className="text-xs">
                            {agents.length}
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
                        <Plus className="h-3.5 w-3.5" />
                        Nieuw
                    </Button>
                )}
            </div>

            {showForm && (
                <CreateEcosystemAgentForm
                    dsId={dsId}
                    onCreated={handleCreated}
                    onCancel={() => setShowForm(false)}
                />
            )}

            {loading && (
                <p className="text-xs text-muted-foreground">Laden…</p>
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

            {!loading && !error && agents.length === 0 && !showForm && (
                <p className="text-xs text-muted-foreground">
                    Nog geen EcosystemAgents in deze DesignSpace.
                </p>
            )}

            {agents.map((agent) => (
                <AgentCard key={agent.agent_uri} agent={agent} />
            ))}
        </div>
    );
}
