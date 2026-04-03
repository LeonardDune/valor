import { useEffect, useState } from 'react';
import { ChevronRight, Plus, CheckCircle } from 'lucide-react';
import { api } from '@/services/api';
import type {
    ValueChainResponse,
    ValueChainTypeItem,
    ValueChainRequirementItem,
    CreateValueCriterionPayload,
    CreateValueBasedDesignRequirementPayload,
} from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface ValueChainProps {
    designSpaceId: string;
}

interface AddCriterionFormState {
    valueTypeUri: string;
    label: string;
    groundedInNormUri: string;
}

interface AddRequirementFormState {
    criterionUri: string;
    label: string;
}

export function ValueChain({ designSpaceId }: ValueChainProps) {
    const [data, setData] = useState<ValueChainResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [addCriterionFor, setAddCriterionFor] = useState<string | null>(null);
    const [addRequirementFor, setAddRequirementFor] = useState<string | null>(null);
    const [criterionForm, setCriterionForm] = useState<AddCriterionFormState>({
        valueTypeUri: '',
        label: '',
        groundedInNormUri: '',
    });
    const [requirementForm, setRequirementForm] = useState<AddRequirementFormState>({
        criterionUri: '',
        label: '',
    });
    const [submitting, setSubmitting] = useState(false);
    const [acceptingReq, setAcceptingReq] = useState<string | null>(null);

    async function load() {
        setLoading(true);
        setError(null);
        try {
            const result = await api.getValueChain(designSpaceId);
            setData(result);
        } catch {
            setError('Kon de waardeketen niet laden.');
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        load();
    }, [designSpaceId]);

    async function handleAddCriterion(e: React.FormEvent) {
        e.preventDefault();
        if (!criterionForm.label.trim() || !criterionForm.valueTypeUri) return;
        setSubmitting(true);
        try {
            const payload: CreateValueCriterionPayload = {
                label: criterionForm.label.trim(),
                value_type_uri: criterionForm.valueTypeUri,
                grounded_in_norm_uri: criterionForm.groundedInNormUri.trim() || undefined,
            };
            await api.createValueCriterion(designSpaceId, payload);
            setAddCriterionFor(null);
            setCriterionForm({ valueTypeUri: '', label: '', groundedInNormUri: '' });
            await load();
        } catch {
            setError('Aanmaken criterium mislukt.');
        } finally {
            setSubmitting(false);
        }
    }

    async function handleAcceptRequirement(reqUri: string) {
        setAcceptingReq(reqUri);
        try {
            await api.patchValueRequirementStatus(designSpaceId, reqUri, 'Accepted');
            await load();
        } catch {
            setError('Accepteren van de ontwerpeis mislukt.');
        } finally {
            setAcceptingReq(null);
        }
    }

    async function handleAddRequirement(e: React.FormEvent) {
        e.preventDefault();
        if (!requirementForm.label.trim() || !requirementForm.criterionUri) return;
        setSubmitting(true);
        try {
            const payload: CreateValueBasedDesignRequirementPayload = {
                label: requirementForm.label.trim(),
                criterion_uri: requirementForm.criterionUri,
            };
            await api.createValueBasedDesignRequirement(designSpaceId, payload);
            setAddRequirementFor(null);
            setRequirementForm({ criterionUri: '', label: '' });
            await load();
        } catch {
            setError('Aanmaken ontwerpeis mislukt.');
        } finally {
            setSubmitting(false);
        }
    }

    if (loading) {
        return <div className="text-sm text-muted-foreground p-4">Waardeketen laden...</div>;
    }

    if (error) {
        return <div className="text-sm text-destructive p-4">{error}</div>;
    }

    if (!data || data.chain.length === 0) {
        return (
            <div className="text-sm text-muted-foreground p-4">
                Geen waardecriteria gevonden. Voeg een waardecriterium toe om de keten te starten.
            </div>
        );
    }

    return (
        <div className="p-4 space-y-6">
            <h2 className="text-base font-semibold text-zinc-900">Waardeketen</h2>
            {data.chain.map((typeItem: ValueChainTypeItem) => (
                <div key={typeItem.value_type_uri} className="border border-border rounded-lg overflow-hidden">
                    {/* ValueType header */}
                    <div className="bg-zinc-100 px-4 py-2 flex items-center justify-between">
                        <span className="text-sm font-medium text-zinc-800">
                            {typeItem.value_type_label}
                        </span>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                                setAddCriterionFor(typeItem.value_type_uri);
                                setCriterionForm({
                                    valueTypeUri: typeItem.value_type_uri,
                                    label: '',
                                    groundedInNormUri: '',
                                });
                            }}
                        >
                            <Plus className="h-3.5 w-3.5 mr-1" />
                            Criterium
                        </Button>
                    </div>

                    {/* Inline form: criterium toevoegen */}
                    {addCriterionFor === typeItem.value_type_uri && (
                        <form onSubmit={handleAddCriterion} className="px-4 py-3 border-b border-border bg-zinc-50 space-y-2">
                            <div className="space-y-1">
                                <Label htmlFor="criterion-label" className="text-xs">Label criterium</Label>
                                <Input
                                    id="criterion-label"
                                    value={criterionForm.label}
                                    onChange={(e) => setCriterionForm(f => ({ ...f, label: e.target.value }))}
                                    placeholder="Bijv. Toegankelijkheid voor alle burgers"
                                    className="h-8 text-sm"
                                    autoFocus
                                />
                            </div>
                            <div className="space-y-1">
                                <Label htmlFor="criterion-norm" className="text-xs">Norm URI (optioneel)</Label>
                                <Input
                                    id="criterion-norm"
                                    value={criterionForm.groundedInNormUri}
                                    onChange={(e) => setCriterionForm(f => ({ ...f, groundedInNormUri: e.target.value }))}
                                    placeholder="https://..."
                                    className="h-8 text-sm"
                                />
                            </div>
                            <div className="flex gap-2">
                                <Button type="submit" size="sm" disabled={submitting || !criterionForm.label.trim()}>
                                    Opslaan
                                </Button>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setAddCriterionFor(null)}
                                >
                                    Annuleren
                                </Button>
                            </div>
                        </form>
                    )}

                    {/* Criteria + requirements */}
                    <div className="divide-y divide-border">
                        {typeItem.criteria.map(criterion => (
                            <div key={criterion.tessera_uri} className="px-4 py-3">
                                <div className="flex items-start gap-2">
                                    {/* Criterium kolom */}
                                    <div className="flex-1 min-w-0">
                                        <div className="text-xs font-medium text-zinc-500 uppercase tracking-wide mb-1">
                                            Criterium
                                        </div>
                                        <div className="text-sm text-zinc-800">{criterion.label}</div>
                                    </div>

                                    <ChevronRight className="h-4 w-4 text-zinc-400 mt-5 shrink-0" />

                                    {/* Ontwerpeisen kolom */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
                                                Ontwerpeisen
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="h-6 px-2 text-xs"
                                                onClick={() => {
                                                    setAddRequirementFor(criterion.tessera_uri);
                                                    setRequirementForm({
                                                        criterionUri: criterion.tessera_uri,
                                                        label: '',
                                                    });
                                                }}
                                            >
                                                <Plus className="h-3 w-3 mr-1" />
                                                Eis
                                            </Button>
                                        </div>

                                        {criterion.requirements.length === 0 ? (
                                            <div className="text-xs text-muted-foreground italic">
                                                Nog geen ontwerpeisen
                                            </div>
                                        ) : (
                                            <ul className="space-y-2">
                                                {criterion.requirements.map((req: ValueChainRequirementItem) => (
                                                    <li key={req.tessera_uri} className="text-sm text-zinc-700">
                                                        <div className="flex items-start gap-1">
                                                            <span className="text-zinc-400 mt-0.5 shrink-0">—</span>
                                                            <div className="flex-1 min-w-0">
                                                                <span>{req.label}</span>
                                                                <div className="flex items-center gap-2 mt-1 flex-wrap">
                                                                    {req.epistemic_status && (
                                                                        <span className={`inline-flex items-center text-xs px-1.5 py-0.5 rounded-full font-medium ${
                                                                            req.epistemic_status === 'Accepted'
                                                                                ? 'bg-green-100 text-green-700'
                                                                                : 'bg-zinc-100 text-zinc-600'
                                                                        }`}>
                                                                            {req.epistemic_status}
                                                                        </span>
                                                                    )}
                                                                    {req.capability_requirement_uri ? (
                                                                        <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                                                                            <CheckCircle className="h-3 w-3" />
                                                                            CapabilityRequirement voorgesteld
                                                                        </span>
                                                                    ) : req.epistemic_status !== 'Accepted' && (
                                                                        <Button
                                                                            variant="ghost"
                                                                            size="sm"
                                                                            className="h-5 px-1.5 text-xs text-zinc-500 hover:text-zinc-800"
                                                                            disabled={acceptingReq === req.tessera_uri}
                                                                            onClick={() => handleAcceptRequirement(req.tessera_uri)}
                                                                        >
                                                                            Accepteren
                                                                        </Button>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </li>
                                                ))}
                                            </ul>
                                        )}

                                        {/* Inline form: ontwerpeis toevoegen */}
                                        {addRequirementFor === criterion.tessera_uri && (
                                            <form onSubmit={handleAddRequirement} className="mt-2 space-y-2">
                                                <Input
                                                    value={requirementForm.label}
                                                    onChange={(e) => setRequirementForm(f => ({ ...f, label: e.target.value }))}
                                                    placeholder="Beschrijf de ontwerpeis..."
                                                    className="h-8 text-sm"
                                                    autoFocus
                                                />
                                                <div className="flex gap-2">
                                                    <Button
                                                        type="submit"
                                                        size="sm"
                                                        disabled={submitting || !requirementForm.label.trim()}
                                                    >
                                                        Opslaan
                                                    </Button>
                                                    <Button
                                                        type="button"
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => setAddRequirementFor(null)}
                                                    >
                                                        Annuleren
                                                    </Button>
                                                </div>
                                            </form>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}
