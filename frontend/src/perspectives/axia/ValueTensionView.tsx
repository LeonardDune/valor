import { useCallback, useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { api } from '@/services/api';
import type { ValueTensionResponse } from '@/services/api';
import { useAxiaSchema } from './hooks/useAxiaSchema';

interface ValueTensionViewProps {
    designSpaceId: string;
}

interface TensionEdge {
    id: string;
    labelA: string;
    labelB: string;
    uriA: string;
    uriB: string;
    description: string;
    tensionContext?: string | null;
}

// ---------------------------------------------------------------------------
// CreateValueTensionModal
// ---------------------------------------------------------------------------

interface CreateValueTensionModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    designSpaceId: string;
    onCreated: (edge: TensionEdge) => void;
}

function CreateValueTensionModal({ open, onOpenChange, designSpaceId, onCreated }: CreateValueTensionModalProps) {
    const { schema } = useAxiaSchema();
    const [selectedA, setSelectedA] = useState('');
    const [selectedB, setSelectedB] = useState('');
    const [description, setDescription] = useState('');
    const [tensionContext, setTensionContext] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleClose = () => {
        setSelectedA('');
        setSelectedB('');
        setDescription('');
        setTensionContext('');
        setError(null);
        onOpenChange(false);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedA || !selectedB || !description.trim()) {
            setError('Vul alle verplichte velden in.');
            return;
        }
        if (selectedA === selectedB) {
            setError('Kies twee verschillende waardetypen.');
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            const result: ValueTensionResponse = await api.createValueTension(designSpaceId, {
                value_type_a_uri: selectedA,
                value_type_b_uri: selectedB,
                description: description.trim(),
                tension_context: tensionContext.trim() || undefined,
            });

            const labelA = schema?.value_types.find((v) => v.uri === result.value_type_a_uri)?.label_nl ?? result.value_type_a_uri.split('#').pop() ?? result.value_type_a_uri;
            const labelB = schema?.value_types.find((v) => v.uri === result.value_type_b_uri)?.label_nl ?? result.value_type_b_uri.split('#').pop() ?? result.value_type_b_uri;

            onCreated({
                id: result.tessera_id,
                labelA,
                labelB,
                uriA: result.value_type_a_uri,
                uriB: result.value_type_b_uri,
                description: result.description,
                tensionContext: result.tension_context,
            });

            // Transitieve spanningsdetectie
            const isTransitive = await api.checkTransitiveTension(designSpaceId, selectedA, selectedB);
            if (isTransitive) {
                toast.info(`Transitieve spanning gedetecteerd: er bestaat al een indirecte verbinding tussen ${labelA} en ${labelB} via een derde waardetype.`);
            }

            handleClose();
        } catch {
            setError('Opslaan mislukt. Probeer opnieuw.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const valueTypes = schema?.value_types ?? [];

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[440px]">
                <DialogHeader>
                    <DialogTitle>Nieuwe Waardespanning</DialogTitle>
                    <DialogDescription>
                        Definieer een spanning tussen twee waardetypen.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label>Waardetype A</Label>
                        <Select value={selectedA} onValueChange={setSelectedA}>
                            <SelectTrigger>
                                <SelectValue placeholder="Kies waardetype A" />
                            </SelectTrigger>
                            <SelectContent>
                                {valueTypes.map((v) => (
                                    <SelectItem key={v.uri} value={v.uri}>
                                        {v.label_nl || v.label_en}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid gap-2">
                        <Label>Waardetype B</Label>
                        <Select value={selectedB} onValueChange={setSelectedB}>
                            <SelectTrigger>
                                <SelectValue placeholder="Kies waardetype B" />
                            </SelectTrigger>
                            <SelectContent>
                                {valueTypes.map((v) => (
                                    <SelectItem key={v.uri} value={v.uri}>
                                        {v.label_nl || v.label_en}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="vt-desc">Omschrijving</Label>
                        <Textarea
                            id="vt-desc"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                            placeholder="Omschrijf de spanning tussen de twee waardetypen..."
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="vt-ctx">Context <span className="text-muted-foreground text-xs">(optioneel)</span></Label>
                        <Textarea
                            id="vt-ctx"
                            value={tensionContext}
                            onChange={(e) => setTensionContext(e.target.value)}
                            rows={2}
                            placeholder="In welke situatie of context speelt deze spanning?"
                        />
                    </div>
                    {error && <p className="text-xs text-destructive">{error}</p>}
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
                            Annuleren
                        </Button>
                        <Button type="submit" disabled={!selectedA || !selectedB || !description.trim() || isSubmitting}>
                            {isSubmitting ? 'Opslaan...' : 'Aanmaken'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// ---------------------------------------------------------------------------
// TensionGraph — SVG met dubbele pijlen
// ---------------------------------------------------------------------------

interface ValueTypeNode { uri: string; label: string; }
interface TensionGraphProps { valueTypes: ValueTypeNode[]; tensions: TensionEdge[]; }

function TensionGraph({ valueTypes, tensions }: TensionGraphProps) {
    const involvedUris = new Set<string>();
    tensions.forEach((t) => { involvedUris.add(t.uriA); involvedUris.add(t.uriB); });
    const nodes = valueTypes.filter((v) => involvedUris.has(v.uri));

    const cx = 250, cy = 180, r = 130;
    const positions: Record<string, { x: number; y: number }> = {};
    nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
        positions[node.uri] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
    });

    return (
        <div className="flex flex-col gap-3">
            <svg viewBox="0 0 500 360" className="w-full max-w-lg rounded-md border border-border bg-muted/30" aria-label="Waardespanningsdiagram">
                <defs>
                    <marker id="arrow-start" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto-start-reverse">
                        <path d="M 0 0 L 6 3 L 0 6 z" fill="hsl(var(--destructive))" opacity="0.7" />
                    </marker>
                    <marker id="arrow-end" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
                        <path d="M 0 0 L 6 3 L 0 6 z" fill="hsl(var(--destructive))" opacity="0.7" />
                    </marker>
                </defs>
                {tensions.map((tension) => {
                    const posA = positions[tension.uriA];
                    const posB = positions[tension.uriB];
                    if (!posA || !posB) return null;
                    return (
                        <line
                            key={tension.id}
                            x1={posA.x} y1={posA.y}
                            x2={posB.x} y2={posB.y}
                            stroke="hsl(var(--destructive))"
                            strokeWidth={2}
                            strokeDasharray="6 3"
                            opacity={0.7}
                            markerStart="url(#arrow-start)"
                            markerEnd="url(#arrow-end)"
                        />
                    );
                })}
                {nodes.map((node) => {
                    const pos = positions[node.uri];
                    if (!pos) return null;
                    return (
                        <g key={node.uri}>
                            <circle cx={pos.x} cy={pos.y} r={28} fill="hsl(var(--card))" stroke="hsl(var(--border))" strokeWidth={1.5} />
                            <text x={pos.x} y={pos.y} textAnchor="middle" dominantBaseline="middle" fontSize={9} fill="hsl(var(--card-foreground))" className="select-none">
                                {node.label.length > 12 ? node.label.slice(0, 11) + '…' : node.label}
                            </text>
                        </g>
                    );
                })}
            </svg>
            <div className="flex flex-col gap-1">
                {tensions.map((t) => (
                    <div key={t.id} className="flex items-start gap-2 text-sm">
                        <span className="mt-0.5 text-destructive font-bold">⟺</span>
                        <div>
                            <span className="font-medium">{t.labelA}</span>
                            <span className="text-muted-foreground mx-1">vs.</span>
                            <span className="font-medium">{t.labelB}</span>
                            <p className="text-xs text-muted-foreground">{t.description}</p>
                            {t.tensionContext && (
                                <p className="text-xs text-muted-foreground italic">Context: {t.tensionContext}</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// ValueTensionView
// ---------------------------------------------------------------------------

export function ValueTensionView({ designSpaceId }: ValueTensionViewProps) {
    const { schema } = useAxiaSchema();
    const [tensions, setTensions] = useState<TensionEdge[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const result = await api.getValueTensions(designSpaceId);
            const valueTypesMap = Object.fromEntries(
                (schema?.value_types ?? []).map((v) => [v.uri, v.label_nl || v.label_en])
            );
            setTensions(result.tensions.map((t) => ({
                id: t.tessera_id,
                labelA: valueTypesMap[t.value_type_a_uri] ?? t.value_type_a_uri.split('#').pop() ?? t.value_type_a_uri,
                labelB: valueTypesMap[t.value_type_b_uri] ?? t.value_type_b_uri.split('#').pop() ?? t.value_type_b_uri,
                uriA: t.value_type_a_uri,
                uriB: t.value_type_b_uri,
                description: t.description,
                tensionContext: t.tension_context,
            })));
        } catch {
            // keep empty on error
        } finally {
            setLoading(false);
        }
    }, [designSpaceId, schema]);

    useEffect(() => {
        load();
    }, [load]);

    const valueTypes = (schema?.value_types ?? []).map((v) => ({
        uri: v.uri,
        label: v.label_nl || v.label_en,
    }));

    const handleCreated = (edge: TensionEdge) => {
        setTensions((prev) => [...prev, edge]);
    };

    if (loading) {
        return <div className="flex items-center justify-center h-full text-muted-foreground text-sm">Laden...</div>;
    }

    return (
        <div className="flex flex-col h-full gap-4 p-4">
            <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold">Waardespanningen</h2>
                <Button size="sm" onClick={() => setIsModalOpen(true)}>
                    <Plus className="h-4 w-4 mr-1" />
                    Spanning toevoegen
                </Button>
            </div>

            {tensions.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">
                    Nog geen waardespanningen gedefinieerd.
                </p>
            ) : (
                <TensionGraph valueTypes={valueTypes} tensions={tensions} />
            )}

            <CreateValueTensionModal
                open={isModalOpen}
                onOpenChange={setIsModalOpen}
                designSpaceId={designSpaceId}
                onCreated={handleCreated}
            />
        </div>
    );
}
