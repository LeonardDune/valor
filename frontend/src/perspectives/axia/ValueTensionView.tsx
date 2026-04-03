import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';
import type { ValueCanvasResponse, ValueTensionResponse, CreateValueTensionPayload } from '@/services/api';

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
}

export function ValueTensionView({ designSpaceId }: ValueTensionViewProps) {
    const [canvas, setCanvas] = useState<ValueCanvasResponse | null>(null);
    const [tensions, setTensions] = useState<TensionEdge[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Form state
    const [formOpen, setFormOpen] = useState(false);
    const [selectedA, setSelectedA] = useState('');
    const [selectedB, setSelectedB] = useState('');
    const [description, setDescription] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [formError, setFormError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const result = await api.getValueClaims(designSpaceId);
                if (!cancelled) setCanvas(result);
            } catch {
                if (!cancelled) setError('Kon waardeclaims niet laden.');
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => { cancelled = true; };
    }, [designSpaceId]);

    const valueTypes = canvas
        ? Object.entries(canvas.groups).map(([uri, claims]) => ({
              uri,
              label: claims[0]?.value_type_label ?? uri.split('#').pop() ?? uri,
          }))
        : [];

    const handleSubmit = async () => {
        if (!selectedA || !selectedB || !description.trim()) {
            setFormError('Vul alle velden in.');
            return;
        }
        if (selectedA === selectedB) {
            setFormError('Kies twee verschillende waardetypen.');
            return;
        }

        setSubmitting(true);
        setFormError(null);

        const payload: CreateValueTensionPayload = {
            value_type_a_uri: selectedA,
            value_type_b_uri: selectedB,
            description: description.trim(),
        };

        try {
            const result: ValueTensionResponse = await api.createValueTension(designSpaceId, payload);
            const labelA = valueTypes.find((v) => v.uri === result.value_type_a_uri)?.label ?? result.value_type_a_uri;
            const labelB = valueTypes.find((v) => v.uri === result.value_type_b_uri)?.label ?? result.value_type_b_uri;

            setTensions((prev) => [
                ...prev,
                {
                    id: result.tessera_id,
                    labelA,
                    labelB,
                    uriA: result.value_type_a_uri,
                    uriB: result.value_type_b_uri,
                    description: result.description,
                },
            ]);

            setFormOpen(false);
            setSelectedA('');
            setSelectedB('');
            setDescription('');
        } catch {
            setFormError('Opslaan mislukt. Probeer opnieuw.');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                Laden...
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

    return (
        <div className="flex flex-col h-full gap-4 p-4">
            <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold">Waardespanningen</h2>
                <Button size="sm" onClick={() => setFormOpen((v) => !v)}>
                    {formOpen ? 'Annuleren' : 'Spanning toevoegen'}
                </Button>
            </div>

            {formOpen && (
                <div className="rounded-md border border-border bg-card p-4 flex flex-col gap-3">
                    <div className="flex flex-col gap-1">
                        <label className="text-xs font-medium text-muted-foreground">Waardetype A</label>
                        <select
                            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                            value={selectedA}
                            onChange={(e) => setSelectedA(e.target.value)}
                        >
                            <option value="">— Kies waardetype —</option>
                            {valueTypes.map((v) => (
                                <option key={v.uri} value={v.uri}>{v.label}</option>
                            ))}
                        </select>
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="text-xs font-medium text-muted-foreground">Waardetype B</label>
                        <select
                            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                            value={selectedB}
                            onChange={(e) => setSelectedB(e.target.value)}
                        >
                            <option value="">— Kies waardetype —</option>
                            {valueTypes.map((v) => (
                                <option key={v.uri} value={v.uri}>{v.label}</option>
                            ))}
                        </select>
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="text-xs font-medium text-muted-foreground">Beschrijving</label>
                        <textarea
                            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm resize-none"
                            rows={3}
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Omschrijf de spanning tussen de twee waardetypen..."
                        />
                    </div>
                    {formError && (
                        <p className="text-xs text-destructive">{formError}</p>
                    )}
                    <Button size="sm" onClick={handleSubmit} disabled={submitting}>
                        {submitting ? 'Opslaan...' : 'Opslaan'}
                    </Button>
                </div>
            )}

            {tensions.length === 0 && !formOpen && (
                <p className="text-sm text-muted-foreground italic">
                    Nog geen waardespanningen gedefinieerd.
                </p>
            )}

            {tensions.length > 0 && (
                <TensionGraph valueTypes={valueTypes} tensions={tensions} />
            )}
        </div>
    );
}

interface ValueTypeNode {
    uri: string;
    label: string;
}

interface TensionGraphProps {
    valueTypes: ValueTypeNode[];
    tensions: TensionEdge[];
}

function TensionGraph({ valueTypes, tensions }: TensionGraphProps) {
    // Bepaal welke valueTypes betrokken zijn
    const involvedUris = new Set<string>();
    tensions.forEach((t) => {
        involvedUris.add(t.uriA);
        involvedUris.add(t.uriB);
    });
    const nodes = valueTypes.filter((v) => involvedUris.has(v.uri));

    // Positioneer nodes in een cirkel
    const cx = 250;
    const cy = 180;
    const r = 130;
    const positions: Record<string, { x: number; y: number }> = {};
    nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
        positions[node.uri] = {
            x: cx + r * Math.cos(angle),
            y: cy + r * Math.sin(angle),
        };
    });

    return (
        <div className="flex flex-col gap-3">
            <svg
                viewBox="0 0 500 360"
                className="w-full max-w-lg rounded-md border border-border bg-muted/30"
                aria-label="Waardespanningsdiagram"
            >
                {/* Edges */}
                {tensions.map((tension) => {
                    const posA = positions[tension.uriA];
                    const posB = positions[tension.uriB];
                    if (!posA || !posB) return null;
                    return (
                        <line
                            key={tension.id}
                            x1={posA.x}
                            y1={posA.y}
                            x2={posB.x}
                            y2={posB.y}
                            stroke="hsl(var(--destructive))"
                            strokeWidth={2}
                            strokeDasharray="6 3"
                            opacity={0.7}
                        />
                    );
                })}
                {/* Nodes */}
                {nodes.map((node) => {
                    const pos = positions[node.uri];
                    if (!pos) return null;
                    return (
                        <g key={node.uri}>
                            <circle cx={pos.x} cy={pos.y} r={28} fill="hsl(var(--card))" stroke="hsl(var(--border))" strokeWidth={1.5} />
                            <text
                                x={pos.x}
                                y={pos.y}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fontSize={9}
                                fill="hsl(var(--card-foreground))"
                                className="select-none"
                            >
                                {node.label.length > 12 ? node.label.slice(0, 11) + '…' : node.label}
                            </text>
                        </g>
                    );
                })}
            </svg>

            {/* Legende */}
            <div className="flex flex-col gap-1">
                {tensions.map((t) => (
                    <div key={t.id} className="flex items-start gap-2 text-sm">
                        <span className="mt-0.5 text-destructive font-bold">—</span>
                        <div>
                            <span className="font-medium">{t.labelA}</span>
                            <span className="text-muted-foreground mx-1">vs.</span>
                            <span className="font-medium">{t.labelB}</span>
                            <p className="text-xs text-muted-foreground">{t.description}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
