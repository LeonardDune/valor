import { useCallback, useEffect, useRef, type MutableRefObject } from 'react';
import ReactFlow, {
    Background,
    useNodesState,
    useNodesInitialized,
    useReactFlow,
    type Node,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { api } from '@/services/api';
import type { ValueClaimItem } from '@/services/api';

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------

const NODE_WIDTH = 220;
const COL_GAP = 60;
const NODE_HEIGHT = 110;
const NODE_GAP = 20;
const GROUP_HEADER_H = 32;
const START_X = 60;
const START_Y = 60;

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
// AutoFitView — binnenin <ReactFlow> zodat RF hooks werken
// ---------------------------------------------------------------------------

function AutoFitView({ shouldFitRef }: { shouldFitRef: MutableRefObject<boolean> }) {
    const { fitView } = useReactFlow();
    const nodesInitialized = useNodesInitialized();

    useEffect(() => {
        if (!nodesInitialized || !shouldFitRef.current) return;
        shouldFitRef.current = false;
        fitView({ padding: 0.2, duration: 400 });
    }, [nodesInitialized, fitView, shouldFitRef]);

    return null;
}

// ---------------------------------------------------------------------------
// Auto-layout: column per value type
// ---------------------------------------------------------------------------

function buildNodes(claims: ValueClaimItem[]): Node[] {
    // Groepeer per ValueType — geordend zodat named types voor ungrouped komen
    const named: Record<string, ValueClaimItem[]> = {};
    const ungrouped: ValueClaimItem[] = [];

    for (const claim of claims) {
        if (claim.value_type_uri) {
            (named[claim.value_type_uri] ??= []).push(claim);
        } else {
            ungrouped.push(claim);
        }
    }

    // Sorteer groepen op label voor stabiele volgorde
    const groups = Object.values(named).sort((a, b) => {
        const la = a[0]?.value_type_label ?? '';
        const lb = b[0]?.value_type_label ?? '';
        return la.localeCompare(lb, 'nl');
    });
    if (ungrouped.length > 0) groups.push(ungrouped);

    const nodes: Node[] = [];
    const colStep = NODE_WIDTH + COL_GAP;

    groups.forEach((group, colIndex) => {
        const x = START_X + colIndex * colStep;
        group.forEach((claim, rowIndex) => {
            nodes.push({
                id: claim.tessera_id,
                type: 'valueClaim',
                // Altijd auto-layout — geslagen stored positions veroorzaken verstrooide canvas
                position: {
                    x,
                    y: START_Y + GROUP_HEADER_H + rowIndex * (NODE_HEIGHT + NODE_GAP),
                },
                data: { claim },
                style: { width: NODE_WIDTH },
            });
        });
    });
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
    const shouldFitRef = useRef(false);

    const load = useCallback(async () => {
        try {
            const result = await api.getValueClaims(designSpaceId);
            const flat: ValueClaimItem[] = Object.values(result.groups).flat();
            shouldFitRef.current = true;
            setNodes(buildNodes(flat));
        } catch {
            // keep canvas empty on error
        }
    }, [designSpaceId, setNodes]);

    useEffect(() => {
        load();
    // refreshTrigger intentionally included to reload when new claims are created
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [load, refreshTrigger]);

    return (
        <div className="h-full w-full">
            <ReactFlow
                nodes={nodes}
                edges={[]}
                onNodesChange={onNodesChange}
                nodeTypes={NODE_TYPES}
                proOptions={{ hideAttribution: true }}
            >
                <Background />
                <AutoFitView shouldFitRef={shouldFitRef} />
            </ReactFlow>
        </div>
    );
}
