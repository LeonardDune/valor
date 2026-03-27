import React, { useCallback, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    type Node,
    type Edge,
    type NodeMouseHandler,
    MarkerType,
    useNodesState,
    useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { api, type TesseraNode } from '@/services/api';
import { TesseraDetailPanel } from '@/components/deliberation/TesseraDetailPanel';

// Kleurcodering per polarity (CAUSA: valor:polarity op CausalClaim-Tessera)
// Conform VALOR-O 00h-causa.trig: ReinforcingPolarity (+) = supports, BalancingPolarity (-) = undermines
const RELATION_COLORS: Record<string, string> = {
    supports: '#22c55e',    // groen  — versterkende causaliteit (+)
    undermines: '#ef4444',  // rood   — dempende causaliteit (-)
    qualifies: '#f59e0b',   // amber  — nuancerende argue-relatie (IBIS overlay)
    presupposes: '#8b5cf6', // paars  — veronderstelde argue-relatie (IBIS overlay)
};

const STATUS_COLORS: Record<string, string> = {
    Proposed: '#71717a',
    Contested: '#f59e0b',
    Accepted: '#22c55e',
    Rejected: '#ef4444',
    Deprecated: '#a1a1aa',
};

const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;

function buildLayout(
    tesseraNodes: TesseraNode[],
): Map<string, { x: number; y: number }> {
    const positions = new Map<string, { x: number; y: number }>();
    const cols = Math.ceil(Math.sqrt(tesseraNodes.length));
    tesseraNodes.forEach((n, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        positions.set(n.id, {
            x: col * (NODE_WIDTH + 80),
            y: row * (NODE_HEIGHT + 60),
        });
    });
    return positions;
}

interface ArgumentationDiagramProps {
    dsId?: string;
}

export const ArgumentationDiagram: React.FC<ArgumentationDiagramProps> = ({ dsId: dsProp }) => {
    const { dsId: dsParam } = useParams<{ dsId: string }>();
    const dsId = dsProp ?? dsParam ?? '';

    // Factor-tesserae als fallback-nodes (inclusief factors zonder claims)
    const { data: allTesserae = [], isLoading: tesseraeLoading } = useQuery({
        queryKey: ['design-space-tesserae', dsId],
        queryFn: () => api.getDesignSpaceTesserae(dsId),
        enabled: !!dsId,
    });

    // CausalClaim-tesserae als edges tussen Factor-nodes (CAUSA-structuur)
    const { data: networkData, isLoading: networkLoading, isError } = useQuery({
        queryKey: ['argumentation-network', dsId],
        queryFn: () => api.getArgumentationNetwork(dsId),
        enabled: !!dsId,
    });

    const isLoading = tesseraeLoading || networkLoading;

    const POLARITY_LEGEND = [
        { key: 'supports', label: 'Versterkt (+)', color: RELATION_COLORS.supports },
        { key: 'undermines', label: 'Dempt (-)', color: RELATION_COLORS.undermines },
    ];

    // Combineer: alle tesserae als nodes, argue-relaties als edges
    const data = React.useMemo(() => {
        if (allTesserae.length === 0) return null;
        const connectedIds = new Set(networkData?.nodes.map(n => n.id) ?? []);
        const extraNodes = allTesserae.filter(t => !connectedIds.has(t.id));
        return {
            nodes: [...(networkData?.nodes ?? []), ...extraNodes],
            edges: networkData?.edges ?? [],
        };
    }, [allTesserae, networkData]);

    const [selectedTessera, setSelectedTessera] = useState<TesseraNode | null>(null);
    const [sheetOpen, setSheetOpen] = useState(false);

    const rfNodes = useMemo<Node[]>(() => {
        if (!data) return [];
        const positions = buildLayout(data.nodes);
        return data.nodes.map((n) => {
            const pos = positions.get(n.id) ?? { x: 0, y: 0 };
            const statusColor = STATUS_COLORS[n.epistemicStatus] ?? '#71717a';
            return {
                id: n.id,
                position: pos,
                type: 'default',
                data: {
                    label: (
                        <div className="flex flex-col gap-1 text-left p-1">
                            <p className="text-xs font-medium leading-tight line-clamp-3 text-foreground">
                                {n.claimContent}
                            </p>
                        </div>
                    ),
                    tessera: n,
                },
                style: {
                    width: NODE_WIDTH,
                    minHeight: NODE_HEIGHT,
                    borderRadius: 8,
                    border: `2px solid ${statusColor}`,
                    background: 'hsl(var(--background))',
                    padding: 8,
                    cursor: 'pointer',
                },
            };
        });
    }, [data]);

    const rfEdges = useMemo<Edge[]>(() => {
        if (!data) return [];
        return data.edges.map((e, i) => {
            const color = RELATION_COLORS[e.relationType] ?? '#94a3b8';
            return {
                id: `edge-${i}-${e.sourceId}-${e.targetId}`,
                source: e.sourceId,
                target: e.targetId,
                type: 'smoothstep',
                label: e.relationLabel,
                labelStyle: { fill: color, fontWeight: 500, fontSize: 11 },
                labelBgStyle: { fill: 'hsl(var(--background))', fillOpacity: 0.85 },
                style: { stroke: color, strokeWidth: 2 },
                markerEnd: {
                    type: MarkerType.ArrowClosed,
                    color,
                },
                data: { relationType: e.relationType },
            };
        });
    }, [data]);

    const [nodes, , onNodesChange] = useNodesState(rfNodes);
    const [edges, , onEdgesChange] = useEdgesState(rfEdges);

    const handleNodeClick: NodeMouseHandler = useCallback(
        (_event, node) => {
            const tessera = (node.data as { tessera: TesseraNode }).tessera;
            setSelectedTessera(tessera);
            setSheetOpen(true);
        },
        [],
    );

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64 gap-2 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm">Argumentatienetwerk laden...</span>
            </div>
        );
    }

    if (isError) {
        return (
            <Alert variant="destructive" className="m-6">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                    Het argumentatienetwerk kon niet worden geladen. Controleer de verbinding en probeer het opnieuw.
                </AlertDescription>
            </Alert>
        );
    }

    if (!data || data.nodes.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
                Nog geen tesserae gevonden in deze DesignSpace.
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full gap-0">
            {/* Legenda */}
            <div className="flex items-center gap-4 px-4 py-2 border-b bg-background flex-wrap">
                <span className="text-xs font-medium text-muted-foreground">Polariteit:</span>
                {POLARITY_LEGEND.map(({ key, label, color }) => (
                    <div key={key} className="flex items-center gap-1.5">
                        <span
                            className="inline-block w-3 rounded-full"
                            style={{ backgroundColor: color, height: 3 }}
                        />
                        <Badge
                            variant="outline"
                            className="text-xs px-1.5 py-0"
                            style={{ borderColor: color, color }}
                        >
                            {label}
                        </Badge>
                    </div>
                ))}
            </div>

            {/* React Flow canvas */}
            <div className="flex-1 relative">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onNodeClick={handleNodeClick}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                    minZoom={0.2}
                    maxZoom={2}
                    attributionPosition="bottom-right"
                >
                    <Background gap={16} size={1} />
                    <Controls showInteractive={false} />
                    <MiniMap
                        nodeColor={(n) => {
                            const tessera = (n.data as { tessera?: TesseraNode }).tessera;
                            return tessera ? (STATUS_COLORS[tessera.epistemicStatus] ?? '#71717a') : '#71717a';
                        }}
                        maskColor="hsl(var(--background) / 0.6)"
                    />
                </ReactFlow>
            </div>

            <TesseraDetailPanel
                tessera={selectedTessera}
                open={sheetOpen}
                onClose={() => setSheetOpen(false)}
            />
        </div>
    );
};
