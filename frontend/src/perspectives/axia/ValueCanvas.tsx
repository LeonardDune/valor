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
const COL_GAP = 80;
const NODE_HEIGHT = 120;
const NODE_GAP = 16;
const GROUP_HEADER_H = 32;
const START_X = 60;
const START_Y = 60;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const HEX_W = 220;
const HEX_H = 120;
// Platte hexagoon (punt links/rechts)
const HEX_CLIP = 'polygon(8% 0%, 92% 0%, 100% 50%, 92% 100%, 8% 100%, 0% 50%)';

function polarityColors(uri?: string | null): { bg: string; text: string; label: string } {
    if (!uri) return { bg: '#e2e8f0', text: '#475569', label: '#94a3b8' };
    if (uri.includes('Supporting')) return { bg: '#dcfce7', text: '#15803d', label: '#16a34a' };
    if (uri.includes('Undermining') || uri.includes('Opposing') || uri.includes('Conflicting'))
        return { bg: '#fee2e2', text: '#b91c1c', label: '#dc2626' };
    if (uri.includes('Ambiguous') || uri.includes('Neutral'))
        return { bg: '#fef9c3', text: '#854d0e', label: '#ca8a04' };
    return { bg: '#e2e8f0', text: '#475569', label: '#94a3b8' };
}

// ---------------------------------------------------------------------------
// Custom node — hexagonale vorm, module-niveau voor stabiele referentie
// ---------------------------------------------------------------------------

interface ValueClaimNodeData {
    claim: ValueClaimItem;
}

function ValueClaimNode({ data }: { data: ValueClaimNodeData }) {
    const { claim } = data;
    const colors = polarityColors(claim.polarity_uri);

    return (
        <div
            style={{
                width: HEX_W,
                height: HEX_H,
                clipPath: HEX_CLIP,
                backgroundColor: colors.bg,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '12px 32px',
                boxSizing: 'border-box',
                cursor: 'pointer',
            }}
        >
            <p
                style={{
                    fontSize: 11,
                    lineHeight: 1.4,
                    color: colors.text,
                    textAlign: 'center',
                    margin: 0,
                    overflow: 'hidden',
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    fontWeight: 500,
                }}
            >
                {claim.claim_content}
            </p>
            {claim.value_type_label && (
                <span
                    style={{
                        marginTop: 4,
                        fontSize: 9,
                        color: colors.label,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        maxWidth: '80%',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                    }}
                >
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
                style: { width: HEX_W, height: HEX_H },
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
    onEdit?: (claim: ValueClaimItem) => void;
}

export function ValueCanvas({ designSpaceId, refreshTrigger = 0, onEdit }: ValueCanvasProps) {
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

    // Dubbelklik opent edit modal — exact zoals CAUSA (onNodeDoubleClick → onEdit)
    const handleNodeDoubleClick = useCallback(
        (_: React.MouseEvent, node: { data: ValueClaimNodeData }) => {
            onEdit?.(node.data.claim);
        },
        [onEdit],
    );

    return (
        <div className="h-full w-full">
            <ReactFlow
                nodes={nodes}
                edges={[]}
                onNodesChange={onNodesChange}
                onNodeDoubleClick={handleNodeDoubleClick}
                nodeTypes={NODE_TYPES}
                proOptions={{ hideAttribution: true }}
            >
                <Background />
                <AutoFitView shouldFitRef={shouldFitRef} />
            </ReactFlow>
        </div>
    );
}
