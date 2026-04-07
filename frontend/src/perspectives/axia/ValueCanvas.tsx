import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
    Background,
    useNodesState,
    type Node,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { api } from '@/services/api';
import type { ValueClaimItem } from '@/services/api';

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------

const COL_WIDTH = 240;
const COL_GAP = 40;
const NODE_HEIGHT = 110;
const NODE_GAP = 16;
const START_X = 40;
const START_Y = 40;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function polarityBorderClass(uri?: string): string {
    if (!uri) return 'border-zinc-300 dark:border-zinc-600';
    if (uri.includes('Supporting')) return 'border-green-500';
    if (uri.includes('Opposing') || uri.includes('Conflicting')) return 'border-red-500';
    if (uri.includes('Neutral')) return 'border-zinc-400';
    return 'border-zinc-300 dark:border-zinc-600';
}

// ---------------------------------------------------------------------------
// Custom node
// ---------------------------------------------------------------------------

interface ValueClaimNodeData {
    claim: ValueClaimItem;
}

function ValueClaimNode({ data }: { data: ValueClaimNodeData }) {
    const { claim } = data;
    const borderClass = polarityBorderClass(claim.polarity_uri);

    return (
        <div className={`w-[220px] rounded-md border-2 ${borderClass} bg-card shadow-sm p-3`}>
            <p className="text-sm leading-snug text-card-foreground line-clamp-3">
                {claim.claim_content}
            </p>
            {claim.value_type_label && (
                <span className="mt-2 inline-block text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded-sm max-w-full truncate">
                    {claim.value_type_label}
                </span>
            )}
            {claim.epistemic_status && (
                <span className="ml-1 mt-2 inline-block text-xs text-muted-foreground italic">
                    {claim.epistemic_status}
                </span>
            )}
        </div>
    );
}

const NODE_TYPES = { valueClaim: ValueClaimNode };

// ---------------------------------------------------------------------------
// Auto-layout: column per value type
// ---------------------------------------------------------------------------

function buildNodes(claims: ValueClaimItem[]): Node[] {
    const grouped: Record<string, ValueClaimItem[]> = {};
    for (const claim of claims) {
        const key = claim.value_type_uri || '__ungrouped';
        (grouped[key] ??= []).push(claim);
    }

    const nodes: Node[] = [];
    let colIndex = 0;
    for (const group of Object.values(grouped)) {
        group.forEach((claim, rowIndex) => {
            const hasPosition = claim.canvas_x != null && claim.canvas_y != null;
            nodes.push({
                id: claim.tessera_id,
                type: 'valueClaim',
                position: {
                    x: hasPosition ? claim.canvas_x! : START_X + colIndex * (COL_WIDTH + COL_GAP),
                    y: hasPosition ? claim.canvas_y! : START_Y + rowIndex * (NODE_HEIGHT + NODE_GAP),
                },
                data: { claim },
                style: { width: 220 },
            });
        });
        colIndex++;
    }
    return nodes;
}

// ---------------------------------------------------------------------------
// Inner canvas — rendered only after claims are loaded
// ---------------------------------------------------------------------------

interface ValueCanvasFlowProps {
    claims: ValueClaimItem[];
    designSpaceId: string;
}

function ValueCanvasFlow({ claims, designSpaceId }: ValueCanvasFlowProps) {
    const initialNodes = useMemo(() => buildNodes(claims), [claims]);
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);

    useEffect(() => {
        setNodes(buildNodes(claims));
    }, [claims, setNodes]);

    const onNodeDragStop = useCallback(
        (_event: React.MouseEvent, node: Node) => {
            const claim = claims.find((c) => c.tessera_id === node.id);
            if (!claim) return;
            api.updateValueClaimPosition(
                designSpaceId,
                claim.tessera_uri,
                node.position.x,
                node.position.y,
            ).catch(() => {
                // Position persistence failure is non-critical
            });
        },
        [claims, designSpaceId],
    );

    return (
        <div className="h-full w-full">
            <ReactFlow
                nodes={nodes}
                edges={[]}
                onNodesChange={onNodesChange}
                onNodeDragStop={onNodeDragStop}
                nodeTypes={NODE_TYPES}
                fitView
                proOptions={{ hideAttribution: true }}
            >
                <Background />
            </ReactFlow>
        </div>
    );
}

// ---------------------------------------------------------------------------
// ValueCanvas
// ---------------------------------------------------------------------------

interface ValueCanvasProps {
    designSpaceId: string;
}

export function ValueCanvas({ designSpaceId }: ValueCanvasProps) {
    const [claims, setClaims] = useState<ValueClaimItem[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await api.getValueClaims(designSpaceId);
            const flat: ValueClaimItem[] = Object.values(result.groups).flat();
            setClaims(flat);
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

    if (!claims || claims.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm italic">
                Geen waardeclaims gevonden voor deze DesignSpace.
            </div>
        );
    }

    return <ValueCanvasFlow claims={claims} designSpaceId={designSpaceId} />;
}
