import { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    MarkerType,
    type Node,
    type Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { api, type StakeholderActor, type StakeholderDependency } from '@/services/api';
import { useSociaOntology } from '../hooks/useSociaOntology';

// ---------------------------------------------------------------------------
// Node-types
// ---------------------------------------------------------------------------

interface ActorNodeData {
    label: string;
    entityTypeLocal: string;
    roleLabel: string | null;
}

function ActorFlowNode({ data }: { data: ActorNodeData }) {
    return (
        <div className="flex flex-col items-center gap-1 px-3 py-2 rounded-lg border border-border bg-card text-card-foreground shadow-sm min-w-[130px] max-w-[200px]">
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
): Node<ActorNodeData>[] {
    return actors.map((actor, i) => ({
        id: actor.uri,
        type: 'actor',
        position: positions[i] ?? { x: i * 200, y: 0 },
        data: {
            label: actor.label,
            entityTypeLocal: actor.entity_type_local,
            roleLabel: actor.role_label_nl ?? null,
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
// Hoofdcomponent
// ---------------------------------------------------------------------------

interface StakeholderMapProps {
    dsId: string;
}

export function StakeholderMap({ dsId }: StakeholderMapProps) {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    useSociaOntology(); // preload ontologie-cache voor labels in de toekomst

    const [nodes, setNodes, onNodesChange] = useNodesState<ActorNodeData>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const map = await api.getStakeholderMap(dsId);
            const positions = circleLayout(map.actors);
            setNodes(actorsToNodes(map.actors, positions));
            setEdges(dependenciesToEdges(map.dependencies));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Onbekende fout');
        } finally {
            setLoading(false);
        }
    }, [dsId, setNodes, setEdges]);

    useEffect(() => {
        load();
    }, [load]);

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
            </div>
            <div className="flex-1 min-h-0">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={NODE_TYPES}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                >
                    <Background />
                    <Controls />
                </ReactFlow>
            </div>
        </div>
    );
}
