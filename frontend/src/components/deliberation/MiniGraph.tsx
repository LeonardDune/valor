import React, { useMemo } from 'react';
import ReactFlow, {
    MarkerType,
    type Node,
    type Edge
} from 'reactflow';
import 'reactflow/dist/style.css';
import { type Claim, type Factor } from '@/services/api';
import { getGeometricHandles } from '@/perspectives/causa/layout/edgeUtils';
import CLDNode from '@/perspectives/causa/views/nodes/CLDNode';
import CLDEdge from '@/perspectives/causa/views/edges/CLDEdge';
import { cn } from '@/lib/utils';

interface MiniGraphProps {
    selectedClaim: Claim;
    allClaims: Claim[];
    factors?: Factor[];
    className?: string;
}

const nodeTypes = {
    cldNode: CLDNode
};

const edgeTypes = {
    cldEdge: CLDEdge
};

export const MiniGraph: React.FC<MiniGraphProps> = ({ selectedClaim, allClaims, factors = [], className }) => {
    const { nodes, edges } = useMemo(() => {
        const nodes: Node[] = [];
        const edges: Edge[] = [];

        if (!selectedClaim) return { nodes: [], edges: [] };

        // Factor lookup helper
        const factorMap = new Map<string, Factor>();
        factors.forEach(f => factorMap.set(f.id, f));

        // 1. Identify relevant claims
        const relevantClaims = allClaims.filter(c =>
            c.id === selectedClaim.id ||
            c.source_id === selectedClaim.source_id ||
            c.target_id === selectedClaim.target_id
        );

        // 2. Identify unique factor IDs
        const uniqueFactorIds = new Set<string>();
        relevantClaims.forEach(c => {
            if (c.source_id) uniqueFactorIds.add(c.source_id);
            if (c.target_id) uniqueFactorIds.add(c.target_id);
        });

        // 3. Create Nodes
        const factorIds = Array.from(uniqueFactorIds);
        const total = factorIds.length;

        factorIds.forEach((id, index) => {
            const factor = factorMap.get(id);
            const isSource = id === selectedClaim.source_id;
            const isTarget = id === selectedClaim.target_id;

            // Placement logic
            let x = 0;
            let y = 0;

            if (isSource) { x = -180; y = 0; }
            else if (isTarget) { x = 180; y = 0; }
            else {
                const angle = (index / total) * Math.PI * 2;
                x = Math.cos(angle) * 250;
                y = Math.sin(angle) * 150;
            }

            nodes.push({
                id,
                type: 'cldNode',
                position: { x, y },
                data: {
                    label: factor?.name || (isSource ? selectedClaim.source_node : selectedClaim.target_node) || 'Onbekend',
                    role: factor?.type || 'unknown',
                    type: factor?.type || 'unknown',
                    isSelected: isSource || isTarget,
                    isReadOnly: true,
                    threadCount: 0
                },
                draggable: false,
                selectable: false,
            });
        });

        // 4. Create Edges with geometric handle logic spiegelend aan CLDView.tsx
        relevantClaims.forEach(c => {
            const isSelected = c.id === selectedClaim.id;
            const sourceNode = nodes.find(n => n.id === c.source_id);
            const targetNode = nodes.find(n => n.id === c.target_id);

            const { sourceHandle, targetHandle } = getGeometricHandles(
                sourceNode?.position || { x: 0, y: 0 },
                targetNode?.position || { x: 0, y: 0 }
            );

            edges.push({
                id: c.id,
                type: 'cldEdge',
                source: c.source_id!,
                target: c.target_id!,
                sourceHandle,
                targetHandle,
                data: {
                    polarity: c.polarity === '+' ? 'positive' : 'negative',
                    statement: c.statement,
                    isSelected,
                    isReadOnly: true,
                    threadCount: 0
                },
                style: {
                    strokeWidth: isSelected ? 3 : 1,
                    opacity: isSelected ? 1 : 0.2,
                    stroke: c.polarity === '+' ? 'var(--color-causal-positive-line)' : 'var(--color-causal-negative-line)'
                },
                markerEnd: {
                    type: MarkerType.ArrowClosed,
                    width: isSelected ? 20 : 12,
                    height: isSelected ? 20 : 12,
                    color: c.polarity === '+' ? 'var(--color-causal-positive-marker)' : 'var(--color-causal-negative-marker)',
                },
            });
        });

        return { nodes, edges };
    }, [selectedClaim, allClaims, factors]);


    return (
        <div className={cn("h-64 w-full border rounded-xl bg-muted/5 overflow-hidden relative", className)}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                fitView
                fitViewOptions={{ padding: 0.1 }}
                draggable={true}
                panOnDrag={true}
                zoomOnScroll={true}
                zoomOnPinch={true}
                zoomOnDoubleClick={true}
                nodesDraggable={false}
                nodesConnectable={false}
                elementsSelectable={false}
                proOptions={{ hideAttribution: true }}
                minZoom={0.1}
                maxZoom={1}
                defaultViewport={{ x: 0, y: 0, zoom: 0.5 }}
            />
        </div>
    );
};
