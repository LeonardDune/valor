import React, { useEffect, useMemo, useState, useCallback } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    type Node,
    type Edge,
    ConnectionMode,
    useNodesState,
    useEdgesState,
    ReactFlowProvider,
    useReactFlow,
    useNodesInitialized,
    addEdge,
    type Connection,
    type OnConnect,
    MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import type { Factor, Claim } from '../../services/api';
import { api } from '../../services/api';
import FactorNode from './FactorNode';
import { SystemScopeNode } from './SystemScopeNode';
import { useForceLayout } from '../../hooks/useForceLayout';

interface LayoutControllerProps {
    nodes: Node[];
    edges: Edge[];
    mode: 'force' | 'system';
    scope: { scopeW: number; scopeH: number };
    layoutEpoch: number;
    onInit: (exposed: { simulation: any, d3Nodes: any[] }) => void;
}

const LayoutController: React.FC<LayoutControllerProps> = ({ nodes, edges, mode, scope, layoutEpoch, onInit }) => {
    const { fitView } = useReactFlow();
    const nodesInitialized = useNodesInitialized();
    const { simulation, d3Nodes } = useForceLayout(nodes, edges, mode, scope, layoutEpoch);

    // Expose simulation to parent
    useEffect(() => {
        if (simulation && d3Nodes) {
            onInit({ simulation, d3Nodes });
        }
    }, [simulation, d3Nodes, onInit]);

    // Unified Auto-Fit Logic
    useEffect(() => {
        // Only fit if nodes are actually ready/measured
        if (!nodesInitialized || nodes.length === 0) return;

        // Force Mode: D3 simulation running/init needs time to expand/cluster.
        // System Mode: Static placement, almost immediate.
        const delay = mode === 'force' ? 2000 : 50;

        const t = setTimeout(() => {
            fitView();
        }, delay);

        return () => clearTimeout(t);
    }, [mode, nodesInitialized, fitView, layoutEpoch]);

    return null;
};

interface ReactFlowCanvasProps {
    factors: Factor[];
    claims: Claim[];
    selection: any;
    onSelect?: (selection: any) => void;
    themeId: string;
    onRefresh?: () => void;
}

const nodeTypes = {
    factor: FactorNode,
    systemScope: SystemScopeNode
};

export const ReactFlowCanvas: React.FC<ReactFlowCanvasProps> = ({
    factors,
    claims,
    selection,
    onSelect,
    themeId,
    onRefresh
}) => {
    const [layoutMode, setLayoutMode] = useState<'force' | 'system'>('force');
    const selectedId = selection?.data?.id;

    // Internal state for React Flow
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // [ADVISOR - SOLUTION A] Parallel Worlds Cache
    const layoutCache = React.useRef<Record<string, Record<string, { x: number, y: number }>>>({});

    // [ADVISOR - EPOCH] Explicit versioning for Layout Runs
    const [layoutEpoch, setLayoutEpoch] = useState(0);

    // [US-4] Interactive Connections
    const onConnect: OnConnect = useCallback(async (params: Connection) => {
        if (!params.source || !params.target) return;

        // 1. Optimistic UI Update
        const tempId = `temp-${Date.now()}`;
        const newEdge: Edge = {
            id: tempId,
            source: params.source,
            target: params.target,
            type: 'default',
            label: '+', // [US-4b] Default polarity
            data: {
                statement: 'New Relation',
                polarity: '+',
                confidence: 0.5,
                source_id: params.source,
                target_id: params.target
            },
            markerEnd: { type: MarkerType.ArrowClosed },
            style: { strokeWidth: 2, stroke: '#94a3b8' },
            labelStyle: { fill: '#1e293b', fontWeight: 700, fontSize: 12 },
            labelBgStyle: { fill: '#f1f5f9', rx: 10, ry: 10, stroke: '#cbd5e1', strokeWidth: 1 },
            labelBgPadding: [8, 4],
        };
        setEdges((eds) => addEdge(newEdge, eds));

        try {
            // 2. API Call
            const createdClaim = await api.createClaim({
                theme_id: themeId,
                source_id: params.source,
                target_id: params.target,
                statement: 'New Relation', // Default
                confidence: 0.5
            });

            // 3. Confirm Update (Replace temp ID with real ID)
            setEdges((eds) => eds.map(e =>
                e.id === tempId ? {
                    ...e,
                    id: createdClaim.id,
                    label: createdClaim.polarity || '+',
                    data: createdClaim, // Sync full data from API
                    animated: true
                } : e
            ));

            // 4. Notify Parent to Refresh Data
            if (onRefresh) onRefresh();

        } catch (err) {
            console.error("Failed to create link:", err);
            // 5. Revert on Failure
            setEdges((eds) => eds.filter(e => e.id !== tempId));
        }
    }, [setEdges, themeId, onRefresh]);

    // Robust Switch Handler
    const switchLayout = (newMode: 'force' | 'system') => {
        if (newMode === layoutMode) return;

        // 1. SAVE: Persist current positions to the old mode's cache
        const currentPositions: Record<string, { x: number, y: number }> = {};
        nodes.forEach(n => {
            currentPositions[n.id] = { ...n.position };
        });
        layoutCache.current[layoutMode] = currentPositions;

        // 2. RESTORE or RESET: Determine start positions for the new mode
        if (newMode === 'force') {
            setNodes(prev => prev.map(n => ({
                ...n,
                position: {
                    x: (Math.random() - 0.5) * 500,
                    y: (Math.random() - 0.5) * 500
                }
            })));
        } else {
            const cached = layoutCache.current['system'];
            if (cached) {
                setNodes(prev => prev.map(n => ({
                    ...n,
                    position: cached[n.id] || n.position
                })));
            }
        }

        // 3. EXECUTE SWITCH
        setLayoutMode(newMode);

        // 4. BUMP EPOCH (Hard Reset Signal)
        setLayoutEpoch(e => e + 1);
    };

    // 2b. Dynamic System Layout Calculations
    const systemScope = useMemo(() => {
        const middelen = factors.filter(f => f.type === 'middel');
        const externen = factors.filter(f => f.type === 'extern');
        const criteria = factors.filter(f => f.type === 'criterium');

        const MIN_W = 1000;
        const MIN_H = 700;
        const ITEM_SPACING = 180;
        const neededW = Math.max(MIN_W, externen.length * ITEM_SPACING);
        const neededH = Math.max(MIN_H, Math.max(middelen.length, criteria.length) * ITEM_SPACING);

        const targetAspect = 1.6;
        let finalW = neededW;
        let finalH = neededW / targetAspect;

        if (finalH < neededH) {
            finalH = neededH;
            finalW = finalH * targetAspect;
        }
        return { scopeW: Math.max(MIN_W, finalW), scopeH: Math.max(MIN_H, finalH) };
    }, [factors]);

    // Sync Factors -> Nodes (and Scope Box)
    useEffect(() => {
        // We only init default nodes once, but the hook handles position updates.
        // If switching layout, we might want to let the hook handle the transition.
        const factorNodes: Node[] = factors.map((f) => ({
            id: f.id,
            position: { x: (Math.random() - 0.5) * 500, y: (Math.random() - 0.5) * 500 },
            data: { label: f.name, ...f },
            type: 'factor',
            zIndex: 10
        }));

        const finalNodes = [...factorNodes];

        if (layoutMode === 'system') {
            finalNodes.push({
                id: 'system-scope-border',
                type: 'systemScope',
                position: { x: 4, y: 0 }, // Nudge Right to align visually
                data: { width: systemScope.scopeW, height: systemScope.scopeH },
                style: { width: systemScope.scopeW, height: systemScope.scopeH }, // Required for nodeOrigin to work before measurement
                draggable: false,
                selectable: false,
                zIndex: -1
            });
        }

        setNodes((prev) => {
            const existingIds = new Set(prev.map(n => n.id));

            // If checking for existing, we must filter out scope node to avoid duplications issues if we didn't handle it
            // Actually, we should just Replace/Update the scope node if it exists.

            const newFactors = finalNodes.filter(n => n.type === 'factor' && !existingIds.has(n.id));
            const otherNodes = prev.filter(n => n.type === 'factor'); // Keep existing factors

            // Re-construct with Scope Node always fresh
            const scopeNode = finalNodes.find(n => n.type === 'systemScope');

            let result = [...otherNodes, ...newFactors];
            if (scopeNode) result.push(scopeNode);

            return result;
        });
    }, [factors, layoutMode, systemScope, setNodes]);

    // Sync Claims -> Edges
    useEffect(() => {
        const newEdges: Edge[] = claims
            .filter(c => c.source_id && c.target_id)
            .map((c) => {
                const isSelected = selectedId === c.id;
                const polarity = c.polarity || '+';
                const badgeColor = isSelected ? '#3b82f6' : (polarity === '-' ? '#ef4444' : '#10b981');

                // [US-6] Find nodes to determine absolute best handles among 8 options
                const sourceNode = nodes.find(n => n.id === c.source_id);
                const targetNode = nodes.find(n => n.id === c.target_id);

                let sourceHandle = 'source-right';
                let targetHandle = 'target-left';

                if (sourceNode && targetNode) {
                    const dx = targetNode.position.x - sourceNode.position.x;
                    const dy = targetNode.position.y - sourceNode.position.y;

                    if (Math.abs(dy) > Math.abs(dx) * 1.2) {
                        // Primarily vertical
                        if (dy > 0) {
                            sourceHandle = 'source-bottom';
                            targetHandle = 'target-top';
                        } else {
                            sourceHandle = 'source-top';
                            targetHandle = 'target-bottom';
                        }
                    } else {
                        // Primarily horizontal
                        if (dx > 0) {
                            sourceHandle = 'source-right';
                            targetHandle = 'target-left';
                        } else {
                            sourceHandle = 'source-left';
                            targetHandle = 'target-right';
                        }
                    }
                }

                return {
                    id: c.id,
                    source: c.source_id!,
                    target: c.target_id!,
                    sourceHandle,
                    targetHandle,
                    label: polarity === '-' ? '—' : polarity,
                    data: c,
                    type: 'default',
                    animated: true,
                    markerEnd: { type: MarkerType.ArrowClosed },
                    style: {
                        strokeWidth: isSelected ? 3 : 2,
                        stroke: isSelected ? '#3b82f6' : '#94a3b8'
                    },
                    labelStyle: { fill: '#ffffff', fontWeight: 900, fontSize: 13 },
                    labelBgStyle: {
                        fill: badgeColor,
                        rx: 10, ry: 10,
                        stroke: badgeColor,
                        strokeWidth: 1,
                        filter: 'drop-shadow(0px 2px 2px rgba(0,0,0,0.1))'
                    },
                    labelBgPadding: [6, 2],
                };
            });
        setEdges(newEdges);
    }, [claims, nodes, setEdges, selectedId]);

    // [US-5] Simulation Ref (Captured from LayoutController)
    const simulationRef = React.useRef<any>(null);
    const d3NodesRef = React.useRef<any[]>([]);

    const onSimulationInit = useCallback(({ simulation, d3Nodes }: { simulation: any, d3Nodes: any[] }) => {
        simulationRef.current = simulation;
        d3NodesRef.current = d3Nodes;
    }, []);

    // --- DRAG HANDLER for System Layout ---
    const onNodeDrag = (_: React.MouseEvent, node: Node) => {
        // [US-5] Interaction Parity: Force Mode Dragging
        if (layoutMode === 'force') {
            if (simulationRef.current && d3NodesRef.current) {
                // Find D3 Node
                const d3Node = d3NodesRef.current.find((n: any) => n.id === node.id);
                if (d3Node) {
                    // Update Fixed Position (Pin it)
                    d3Node.fx = node.position.x;
                    d3Node.fy = node.position.y;

                    // Re-heat simulation to pull neighbors
                    simulationRef.current.alphaTarget(0.3).restart();
                }
            }
            return;
        }

        if (layoutMode !== 'system') return;

        const type = (node.data?.type || 'systeemelement').toLowerCase();

        // Strict border reordering for middelen, externen, criteria
        if (['middel', 'extern', 'criterium'].includes(type) || type === 'factor') {
            setNodes((prevNodes) => {
                // Determine Constraints (Rail)
                // Note: nodeOrigin is [0.5, 0.5], so (0,0) is center.
                // Left Border X: -width/2, Right Border X: width/2
                // Top Border Y: -height/2

                const halfW = systemScope.scopeW / 2;
                const halfH = systemScope.scopeH / 2;
                const CARD_W = 140; // Approx card width
                const CARD_H = 100; // Approx card height

                let constrainedPos = { ...node.position };

                if (type === 'middel') {
                    constrainedPos.x = -halfW;
                    // Clamp Y to box height (minus padding/half card)
                    constrainedPos.y = Math.max(-halfH + CARD_H / 2, Math.min(halfH - CARD_H / 2, node.position.y));
                }
                if (type === 'criterium') {
                    constrainedPos.x = halfW;
                    // Clamp Y to box height
                    constrainedPos.y = Math.max(-halfH + CARD_H / 2, Math.min(halfH - CARD_H / 2, node.position.y));
                }
                if (type === 'extern') {
                    constrainedPos.y = -halfH;
                    // Clamp X to box width
                    constrainedPos.x = Math.max(-halfW + CARD_W / 2, Math.min(halfW - CARD_W / 2, node.position.x));
                }

                // 1. Identify Group
                const group = prevNodes.filter(n => (n.data?.type || 'systeemelement').toLowerCase() === type);
                const others = prevNodes.filter(n => (n.data?.type || 'systeemelement').toLowerCase() !== type);

                // 2. Sort Group based on Axis
                const isVertical = type === 'middel' || type === 'criterium';

                // Helper to get efficient comparison value
                const getVal = (n: Node) => {
                    // Use the constrained, drag-updated position for the dragged node
                    if (n.id === node.id) return isVertical ? constrainedPos.y : constrainedPos.x;
                    return isVertical ? n.position.y : n.position.x;
                };

                // Sort
                const sortedGroup = [...group].sort((a, b) => getVal(a) - getVal(b));

                // 3. Redistribute Evenly (Snap to Grid)
                // Use 85% of edge (matching legacy logic)
                const totalLen = isVertical ? systemScope.scopeH : systemScope.scopeW;
                const usableLen = totalLen * 0.85;

                const finalGroup = sortedGroup.map((n, i) => {
                    const offset = ((i + 0.5) / sortedGroup.length - 0.5) * usableLen;

                    // We must construct the 'ideal' snapped position
                    const snappedPos = { ...n.position };

                    if (type === 'middel') { snappedPos.x = -halfW; snappedPos.y = offset; }
                    else if (type === 'criterium') { snappedPos.x = halfW; snappedPos.y = offset; }
                    else if (type === 'extern') { snappedPos.y = -halfH; snappedPos.x = offset; }

                    // We MUST update dragging node to constrained pos to feel responsive
                    if (n.id === node.id) {
                        return { ...n, position: constrainedPos };
                    }

                    return { ...n, position: snappedPos };
                });

                // 4. Check if order changed OR positions changed
                // (Always update because drag needs visual feedback on neighbors)
                return [...others, ...finalGroup];
            });
        } else {
            // Systeemelement (or others inside the box) -> Clamp to Box
            const { scopeW, scopeH } = systemScope;
            const CARD_WIDTH = 140;
            const CARD_HEIGHT = 100;
            const padding = 20;

            // Calculate bounds (relative to center 0,0)
            const maxX = (scopeW / 2) - CARD_WIDTH / 2 - padding;
            const maxY = (scopeH / 2) - CARD_HEIGHT / 2 - padding;

            setNodes((prevNodes) => prevNodes.map(n => {
                if (n.id === node.id) {
                    let newX = node.position.x;
                    let newY = node.position.y;

                    if (newX < -maxX) newX = -maxX;
                    if (newX > maxX) newX = maxX;
                    if (newY < -maxY) newY = -maxY;
                    if (newY > maxY) newY = maxY;

                    if (newX !== node.position.x || newY !== node.position.y) {
                        return { ...n, position: { x: newX, y: newY } };
                    }
                }
                return n;
            }));
        }
    };

    const onNodeDragStop = (_: React.MouseEvent, node: Node) => {
        // [US-5] Stop Simulation Heat
        if (layoutMode === 'force') {
            if (simulationRef.current && d3NodesRef.current) {
                const d3Node = d3NodesRef.current.find((n: any) => n.id === node.id);
                if (d3Node) {
                    d3Node.fx = null;
                    d3Node.fy = null;
                    simulationRef.current.alphaTarget(0); // Cooldown
                }
            }
            return;
        }

        if (layoutMode !== 'system') return;

        const type = (node.data?.type || 'systeemelement').toLowerCase();

        // On Stop, strictly snap everyone to the grid so the dragged node aligns perfectly
        if (['middel', 'extern', 'criterium'].includes(type) || type === 'factor') {
            setNodes((prevNodes) => {
                const group = prevNodes.filter(n => (n.data?.type || 'systeemelement').toLowerCase() === type);
                const others = prevNodes.filter(n => (n.data?.type || 'systeemelement').toLowerCase() !== type);

                const isVertical = type === 'middel' || type === 'criterium';
                const halfW = systemScope.scopeW / 2;
                const halfH = systemScope.scopeH / 2;

                // 1. Sort based on current positions (which includes the final drag position)
                // Use strict axis
                const sortedGroup = [...group].sort((a, b) => {
                    const posA = isVertical ? a.position.y : a.position.x;
                    const posB = isVertical ? b.position.y : b.position.x;
                    return posA - posB;
                });

                // 2. Redistribute
                const totalLen = isVertical ? systemScope.scopeH : systemScope.scopeW;
                const usableLen = totalLen * 0.85;

                const finalGroup = sortedGroup.map((n, i) => {
                    const offset = ((i + 0.5) / sortedGroup.length - 0.5) * usableLen;

                    let newPos = { ...n.position };
                    if (type === 'middel') { newPos.x = -halfW; newPos.y = offset; }
                    else if (type === 'criterium') { newPos.x = halfW; newPos.y = offset; }
                    else if (type === 'extern') { newPos.y = -halfH; newPos.x = offset; }

                    return { ...n, position: newPos };
                });

                return [...others, ...finalGroup];
            });
        }
    };

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlowProvider>
                <div className="absolute top-4 right-4 z-10 bg-white p-2 rounded shadow flex gap-2">
                    <button
                        onClick={() => switchLayout('force')}
                        className={`px-3 py-1 rounded text-sm font-semibold ${layoutMode === 'force' ? 'bg-blue-600 text-white' : 'bg-slate-100'}`}
                    >
                        Free
                    </button>
                    <button
                        onClick={() => switchLayout('system')}
                        className={`px-3 py-1 rounded text-sm font-semibold ${layoutMode === 'system' ? 'bg-blue-600 text-white' : 'bg-slate-100'}`}
                    >
                        System
                    </button>
                </div>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    connectionMode={ConnectionMode.Loose}
                    nodeOrigin={[0.5, 0.5]} // Fix: Center origin to match D3 and Scope Box
                    fitView
                    minZoom={0.1}
                    maxZoom={4}
                    onNodeClick={(_, node) => onSelect?.({ type: 'node', data: node.data })}
                    onEdgeClick={(_, edge) => onSelect?.({ type: 'link', data: edge.data })}
                    onPaneClick={() => onSelect?.(null)}
                    onNodeDrag={onNodeDrag}
                    onNodeDragStop={onNodeDragStop}
                    nodeTypes={nodeTypes}
                >
                    <LayoutController
                        key={layoutMode}
                        nodes={nodes}
                        edges={edges}
                        mode={layoutMode}
                        scope={systemScope}
                        layoutEpoch={layoutEpoch}
                        onInit={onSimulationInit}
                    />
                    <Background color="#f1f5f9" gap={16} />
                    <Controls />
                    <MiniMap />
                </ReactFlow>
            </ReactFlowProvider>
        </div>
    );
};
