import { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    MarkerType,
    type Node,
    type Edge,
    type NodeMouseHandler,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Pencil, Trash2, X, Check } from 'lucide-react';
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
import { api, type StakeholderActor, type StakeholderDependency } from '@/services/api';
import { useSociaOntology } from '../hooks/useSociaOntology';

// ---------------------------------------------------------------------------
// Node-types
// ---------------------------------------------------------------------------

interface ActorNodeData {
    label: string;
    entityTypeLocal: string;
    roleLabel: string | null;
    selected?: boolean;
}

function ActorFlowNode({ data }: { data: ActorNodeData }) {
    return (
        <div className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg border bg-card text-card-foreground shadow-sm min-w-[130px] max-w-[200px] cursor-pointer transition-colors ${data.selected ? 'border-primary ring-1 ring-primary' : 'border-border'}`}>
            <span className="text-sm font-medium text-center leading-tight">{data.label}</span>
            {data.entityTypeLocal && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                    {data.entityTypeLocal}
                </span>
            )}
            {data.roleLabel && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                    {data.roleLabel}
                </span>
            )}
        </div>
    );
}

const NODE_TYPES = { actor: ActorFlowNode };

// ---------------------------------------------------------------------------
// Layout hulpfunctie (eenvoudige cirkelindeling)
// ---------------------------------------------------------------------------

function circleLayout(actors: StakeholderActor[]): { x: number; y: number }[] {
    const n = actors.length;
    if (n === 0) return [];
    const radius = Math.max(180, n * 50);
    return actors.map((_, i) => {
        const angle = (2 * Math.PI * i) / n - Math.PI / 2;
        return {
            x: 400 + radius * Math.cos(angle),
            y: 320 + radius * Math.sin(angle),
        };
    });
}

// ---------------------------------------------------------------------------
// Conversie helpers
// ---------------------------------------------------------------------------

function actorsToNodes(
    actors: StakeholderActor[],
    positions: { x: number; y: number }[],
    selectedUri: string | null,
): Node<ActorNodeData>[] {
    return actors.map((actor, i) => ({
        id: actor.uri,
        type: 'actor',
        position: positions[i] ?? { x: i * 200, y: 0 },
        data: {
            label: actor.label,
            entityTypeLocal: actor.entity_type_local,
            roleLabel: actor.role_label_nl ?? null,
            selected: actor.uri === selectedUri,
        },
    }));
}

function dependenciesToEdges(deps: StakeholderDependency[]): Edge[] {
    return deps.map((dep, i) => ({
        id: `dep-${i}`,
        source: dep.from_uri,
        target: dep.to_uri,
        label: dep.dependency_label_nl,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { strokeWidth: 1.5 },
        labelStyle: { fontSize: 11 },
    }));
}

// ---------------------------------------------------------------------------
// ActorDetailPanel
// ---------------------------------------------------------------------------

interface ActorDetailPanelProps {
    dsId: string;
    actor: StakeholderActor;
    onClose: () => void;
    onUpdated: () => void;
    onDeleted: () => void;
}

function ActorDetailPanel({ dsId, actor, onClose, onUpdated, onDeleted }: ActorDetailPanelProps) {
    const { ontology } = useSociaOntology();
    const [editing, setEditing] = useState(false);
    const [label, setLabel] = useState(actor.label);
    const [actorTypeUri, setActorTypeUri] = useState(actor.entity_type);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSave = async () => {
        setSaving(true);
        setError(null);
        try {
            await api.updateActor(dsId, actor.uri, {
                label: label.trim() || undefined,
                actor_type_uri: actorTypeUri || undefined,
            });
            setEditing(false);
            onUpdated();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Opslaan mislukt');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm(`Actor "${actor.label}" verwijderen? Dit kan niet ongedaan worden gemaakt.`)) return;
        setDeleting(true);
        setError(null);
        try {
            await api.deleteActor(dsId, actor.uri);
            onDeleted();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Verwijderen mislukt');
            setDeleting(false);
        }
    };

    return (
        <div className="absolute right-4 top-4 z-10 w-72 bg-card border border-border rounded-lg shadow-lg p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">Actor</span>
                <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground">
                    <X className="h-4 w-4" />
                </button>
            </div>

            {!editing ? (
                <>
                    <div className="space-y-1">
                        <p className="text-sm font-medium">{actor.label}</p>
                        <p className="text-xs text-muted-foreground">{actor.entity_type_local}</p>
                        {actor.role_label_nl && (
                            <p className="text-xs text-primary">{actor.role_label_nl}</p>
                        )}
                        <p className="text-xs text-muted-foreground truncate" title={actor.uri}>{actor.uri}</p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            className="flex-1 gap-1"
                            onClick={() => setEditing(true)}
                        >
                            <Pencil className="h-3.5 w-3.5" />
                            Bewerken
                        </Button>
                        <Button
                            variant="destructive"
                            size="sm"
                            className="gap-1"
                            onClick={handleDelete}
                            disabled={deleting}
                        >
                            <Trash2 className="h-3.5 w-3.5" />
                            {deleting ? '…' : 'Verwijder'}
                        </Button>
                    </div>
                </>
            ) : (
                <div className="space-y-3">
                    <div className="space-y-1.5">
                        <Label htmlFor="edit-label">Naam</Label>
                        <Input
                            id="edit-label"
                            value={label}
                            onChange={(e) => setLabel(e.target.value)}
                        />
                    </div>
                    <div className="space-y-1.5">
                        <Label htmlFor="edit-type">Type</Label>
                        {ontology?.actor_types && ontology.actor_types.length > 0 ? (
                            <Select value={actorTypeUri} onValueChange={setActorTypeUri}>
                                <SelectTrigger id="edit-type">
                                    <SelectValue placeholder="Kies een type" />
                                </SelectTrigger>
                                <SelectContent>
                                    {ontology.actor_types.map((t) => (
                                        <SelectItem key={t.uri} value={t.uri}>
                                            {t.label_nl || t.label_en || t.local_name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        ) : (
                            <Input
                                id="edit-type"
                                value={actorTypeUri}
                                onChange={(e) => setActorTypeUri(e.target.value)}
                                placeholder="URI van actortype"
                            />
                        )}
                    </div>
                    {error && <p className="text-xs text-destructive">{error}</p>}
                    <div className="flex gap-2 justify-end">
                        <Button type="button" variant="ghost" size="sm" onClick={() => setEditing(false)}>
                            Annuleren
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            className="gap-1"
                            onClick={handleSave}
                            disabled={saving || !label.trim()}
                        >
                            <Check className="h-3.5 w-3.5" />
                            {saving ? 'Opslaan…' : 'Opslaan'}
                        </Button>
                    </div>
                </div>
            )}

            {error && !editing && <p className="text-xs text-destructive">{error}</p>}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Hoofdcomponent
// ---------------------------------------------------------------------------

interface StakeholderMapProps {
    dsId: string;
}

export function StakeholderMap({ dsId }: StakeholderMapProps) {
    useSociaOntology(); // preload ontologie-cache
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actors, setActors] = useState<StakeholderActor[]>([]);
    const [selectedActor, setSelectedActor] = useState<StakeholderActor | null>(null);
    const [positions, setPositions] = useState<{ x: number; y: number }[]>([]);

    const [nodes, setNodes, onNodesChange] = useNodesState<ActorNodeData>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const map = await api.getStakeholderMap(dsId);
            const pos = circleLayout(map.actors);
            setActors(map.actors);
            setPositions(pos);
            setNodes(actorsToNodes(map.actors, pos, null));
            setEdges(dependenciesToEdges(map.dependencies));
            setSelectedActor(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Onbekende fout');
        } finally {
            setLoading(false);
        }
    }, [dsId, setNodes, setEdges]);

    useEffect(() => {
        load();
    }, [load]);

    // Update node selection highlight zonder reload
    useEffect(() => {
        setNodes(actorsToNodes(actors, positions, selectedActor?.uri ?? null));
    }, [selectedActor, actors, positions, setNodes]);

    const handleNodeClick: NodeMouseHandler = useCallback((_event, node) => {
        const actor = actors.find((a) => a.uri === node.id) ?? null;
        setSelectedActor((prev) => (prev?.uri === actor?.uri ? null : actor));
    }, [actors]);

    const nodeCount = nodes.length;
    const edgeCount = edges.length;

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
                Stakeholderkaart laden…
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-2">
                <p className="text-sm text-destructive">Fout bij laden: {error}</p>
                <button
                    type="button"
                    onClick={load}
                    className="text-sm underline text-muted-foreground hover:text-foreground"
                >
                    Opnieuw proberen
                </button>
            </div>
        );
    }

    if (nodeCount === 0) {
        return (
            <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
                Geen actoren gevonden in deze DesignSpace.
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center gap-4 px-4 py-2 border-b border-border text-xs text-muted-foreground">
                <span>{nodeCount} actor{nodeCount !== 1 ? 'en' : ''}</span>
                <span>{edgeCount} afhankelijkhe{edgeCount !== 1 ? 'den' : 'id'}</span>
                <span className="text-muted-foreground/60">Klik op een actor om te bewerken of verwijderen</span>
            </div>
            <div className="flex-1 min-h-0 relative">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={NODE_TYPES}
                    onNodeClick={handleNodeClick}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                >
                    <Background />
                    <Controls />
                </ReactFlow>
                {selectedActor && (
                    <ActorDetailPanel
                        dsId={dsId}
                        actor={selectedActor}
                        onClose={() => setSelectedActor(null)}
                        onUpdated={load}
                        onDeleted={load}
                    />
                )}
            </div>
        </div>
    );
}
