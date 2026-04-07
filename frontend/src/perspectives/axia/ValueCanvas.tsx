import { useCallback, useEffect, useRef } from 'react';
import ReactFlow, {
    Background,
    useNodesState,
    type Node,
    type ReactFlowInstance,
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

function polarityBorderClass(uri?: string | null): string {
    if (!uri) return 'border-zinc-300 dark:border-zinc-600';
    if (uri.includes('Supporting')) return 'border-green-500';
    if (uri.includes('Opposing') || uri.includes('Conflicting')) return 'border-red-500';
    if (uri.includes('Neutral')) return 'border-zinc-400';
    return 'border-zinc-300 dark:border-zinc-600';
}

// ---------------------------------------------------------------------------
// Custom node — defined at module level so reference is stable
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
        </div>
    );
}

// Stable module-level constant — prevents React Flow nodeTypes warning
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
// ValueCanvas
// ---------------------------------------------------------------------------

interface ValueCanvasProps {
    designSpaceId: string;
    refreshTrigger?: number;
}

export function ValueCanvas({ designSpaceId, refreshTrigger = 0 }: ValueCanvasProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState<ValueClaimNodeData>([]);
    const rfInstance = useRef<ReactFlowInstance | null>(null);

    const load = useCallback(async () => {
        try {
            const result = await api.getValueClaims(designSpaceId);
            const flat: ValueClaimItem[] = Object.values(result.groups).flat();
            setNodes(buildNodes(flat));
            // fitView na setNodes zodat alle nodes zichtbaar zijn
            setTimeout(() => rfInstance.current?.fitView({ padding: 0.1 }), 50);
        } catch {
            // keep canvas empty on error
        }
    }, [designSpaceId, setNodes]);

    useEffect(() => {
        load();
    // refreshTrigger intentionally included to reload when new claims are created
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [load, refreshTrigger]);

    const onNodeDragStop = useCallback(
        (_event: React.MouseEvent, node: Node) => {
            api.updateValueClaimPosition(
                designSpaceId,
                node.id,
                node.position.x,
                node.position.y,
            ).catch(() => {});
        },
        [designSpaceId],
    );

    return (
        <div className="h-full w-full">
            <ReactFlow
                nodes={nodes}
                edges={[]}
                onNodesChange={onNodesChange}
                onNodeDragStop={onNodeDragStop}
                onInit={(instance) => { rfInstance.current = instance; }}
                nodeTypes={NODE_TYPES}
                proOptions={{ hideAttribution: true }}
            >
                <Background />
            </ReactFlow>
        </div>
    );
}
