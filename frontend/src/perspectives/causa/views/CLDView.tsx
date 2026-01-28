import { type FunctionComponent, useEffect, useState } from 'react';
import ReactFlow, {
    useNodesState,
    useEdgesState,
    Background,
    MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import type { LayoutSession } from '../layout/session';
import type { LayoutRunner } from '../layout/runner';
import type { LayoutNode } from '../layout/types';
import CLDNode from './nodes/CLDNode';
import { SystemScopeNode } from './nodes/SystemScopeNode';
import CLDEdge from './edges/CLDEdge';
import { CanvasContextMenu } from '@/components/shell/CanvasContextMenu';
import { ViewControls } from '@/components/shell/ViewControls';
import type { ConversationContext } from '@/types/conversation';

// Correct path if types are in parent/parent
import type { CausalNode, CausalLink } from '../types';

interface CLDViewProps {
    nodes: CausalNode[];
    links: CausalLink[];
    session: LayoutSession;
    runner: LayoutRunner;
    onSelect?: (selection: { type: 'node' | 'link'; data: any } | null) => void;
    selection?: { type: 'node' | 'link'; data: any } | null;
    layoutMode?: 'free' | 'system';
    onOpenConversation: (context: ConversationContext) => void;
    onEdit?: (selection: { type: 'node' | 'link'; data: any }) => void;
    onViewportChange?: (viewport: { x: number; y: number; zoom: number }) => void;
    onInit?: (instance: any) => void;
}



const nodeTypes = {
    cldNode: CLDNode,
    systemScope: SystemScopeNode
};

const edgeTypes = {
    cldEdge: CLDEdge
};

export const CLDView: FunctionComponent<CLDViewProps> = ({
    nodes: causalNodes,
    links: causalLinks,
    session,
    runner,
    onSelect,
    layoutMode,
    onOpenConversation,
    onEdit,
    onViewportChange,
    onInit
}) => {
    // React Flow State
    const [rfInstance, setRfInstance] = useState<any>(null);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);





    // Context Menu State
    const [contextMenu, setContextMenu] = useState<{ visible: boolean; x: number; y: number; nodeId: string; type: string; label?: string; data?: any } | null>(null);

    const onNodeContextMenu = (event: React.MouseEvent, node: any) => {
        event.preventDefault();
        setContextMenu({
            visible: true,
            x: event.clientX,
            y: event.clientY,
            nodeId: node.id,
            type: 'node', // Explicitly 'node' to match Shell contract
            label: node.data?.label || node.id // Use label from data
        });
    };

    const onEdgeContextMenu = (event: React.MouseEvent, edge: any) => {
        event.preventDefault();
        setContextMenu({
            visible: true,
            x: event.clientX,
            y: event.clientY,
            nodeId: edge.id,
            type: 'link',
            label: 'Relatie', // Static label for edges for now
            data: { id: edge.id, source: edge.source, target: edge.target, ...edge.data } // Pass full data for editing
        });
    };

    const handleOpenObjectConversation = (object: any) => {
        onOpenConversation({
            scope: 'object',
            perspective: 'CAUSA',
            contextId: object.id,
            label: object.label || object.type
        });
    };

    // 1. Topology Sync (Handle Adds/Removes/Updates from Domain)
    useEffect(() => {
        const layoutNodes = session.getNodes();
        const layoutNodeMap = new Map(layoutNodes.map(n => [n.id, n]));

        setNodes(currentNodes => {
            // Map all causalNodes to RF Nodes
            const mappedNodes = causalNodes.map(cn => {
                const existing = currentNodes.find(n => n.id === cn.id);
                const layout = layoutNodeMap.get(cn.id);

                // Use existing position if available, else layout, else 0
                const position = existing ? existing.position : (layout ? { x: layout.x, y: layout.y } : { x: 0, y: 0 });

                return {
                    id: cn.id,
                    type: 'cldNode',
                    position,
                    data: { label: cn.label, type: cn.type, role: cn.role, description: cn.description }
                };
            });

            if (layoutMode === 'system') {
                // Determine Scope Dimensions (Logic duplicated from RailRunner for visual consistency)
                const middelen = causalNodes.filter(n => ((n.role as string) === 'middel' || (n.type as string) === 'middel'));
                const criteria = causalNodes.filter(n => ((n.role as string) === 'criterium' || (n.type as string) === 'criterium'));
                const externen = causalNodes.filter(n => ((n.role as string) === 'extern' || (n.type as string) === 'extern'));

                const minWidth = 1000;
                const minHeight = 700;
                const spacing = 180;

                const neededW = Math.max(minWidth, externen.length * spacing);
                const neededH = Math.max(minHeight, Math.max(middelen.length, criteria.length) * spacing);

                const targetAspect = 1.6;
                let finalW = neededW;
                let finalH = neededW / targetAspect;

                if (finalH < neededH) {
                    finalH = neededH;
                    finalW = finalH * targetAspect;
                }
                const scopeW = Math.max(minWidth, finalW);
                const scopeH = Math.max(minHeight, finalH);

                mappedNodes.push({
                    id: 'system-scope-border',
                    type: 'systemScope',
                    position: { x: 0, y: 0 }, // It centers itself visually via CSS or we center it here?
                    // SystemScopeNode uses w-full h-full, but ReactFlow nodes need width/height style
                    // We also ensure zIndex is -10 here, and explicitly on the node style
                    style: { width: scopeW, height: scopeH, zIndex: -10 },
                    data: { label: 'Scope' },
                    draggable: false,
                    selectable: false
                } as any);
            }

            return mappedNodes;
        });

        setEdges(() => {
            return causalLinks.map(cl => {
                const sourceNode = layoutNodeMap.get(cl.source);
                const targetNode = layoutNodeMap.get(cl.target);

                // [US-09] Revert to Legacy Geometric Logic (matches ReactFlowCanvas.tsx)
                // This ensures connections follow the visual physics rather than arbitrary role rules.

                let sourceHandle = 'source-right';
                let targetHandle = 'target-left';

                if (sourceNode && targetNode) {
                    const dx = targetNode.x - sourceNode.x;
                    const dy = targetNode.y - sourceNode.y;

                    // Use 1.2 factor to bias slightly towards horizontal connections 
                    // unless clearly vertical.
                    if (Math.abs(dy) > Math.abs(dx) * 1.2) {
                        // Primarily vertical
                        if (dy > 0) { // Target is below
                            sourceHandle = 'source-bottom';
                            targetHandle = 'target-top';
                        } else { // Target is above
                            sourceHandle = 'source-top';
                            targetHandle = 'target-bottom';
                        }
                    } else {
                        // Primarily horizontal
                        if (dx > 0) { // Target is right
                            sourceHandle = 'source-right';
                            targetHandle = 'target-left';
                        } else { // Target is left
                            sourceHandle = 'source-left';
                            targetHandle = 'target-right';
                        }
                    }
                }
                const isPositive = cl.polarity === 'positive';
                const edgeStrokeColor = isPositive ? 'var(--color-causal-positive-line)' : 'var(--color-causal-negative-line)';
                const edgeMarkerColor = isPositive ? 'var(--color-causal-positive-marker)' : 'var(--color-causal-negative-marker)';

                return {
                    id: cl.id,
                    source: cl.source,
                    target: cl.target,
                    sourceHandle,
                    targetHandle,
                    type: 'cldEdge',
                    style: {
                        strokeWidth: 2,
                        stroke: edgeStrokeColor,
                    },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        width: 20,
                        height: 20,
                        color: edgeMarkerColor,
                    },
                    data: {
                        polarity: cl.polarity,
                        status: cl.status || 'validated',
                        certainty: cl.certainty,
                        statement: cl.statement, // Include statement/claim text
                        source: cl.source, // redundancy for data access
                        target: cl.target  // redundancy for data access
                    }
                };
            });
        });

        // 2. Notify Runner of Data Change
        // Ensure ForceRunner gets the new topology to restart simulation
        if (runner.updateData) {
            runner.updateData(session.getNodes(), session.getLinks());
        }

    }, [causalNodes, causalLinks, session, setNodes, setEdges, layoutMode, runner]);


    // Fit View on Layout Mode Change
    useEffect(() => {
        if (rfInstance) {
            const isForce = (layoutMode as string) === 'free' || (layoutMode as string) === 'force';

            // Strategy: 
            // 1. Immediate Fit: Ensure we verify context (especially going System -> Free).
            // 2. Delayed Fit: Wait for simulation to settle (Force mode only).

            // First Snap (Fast)
            const t1 = setTimeout(() => {
                rfInstance.fitView({ padding: 0.2, duration: 600 });
            }, 50);

            // Second Snap (Final Polish for Force Layout)
            // Force simulation takes ~2s to stabilize with current alpha.
            let t2: ReturnType<typeof setTimeout>;
            if (isForce) {
                t2 = setTimeout(() => {
                    rfInstance.fitView({ padding: 0.2, duration: 800 });
                }, 2000);
            }

            return () => {
                clearTimeout(t1);
                if (t2) clearTimeout(t2);
            };
        }
    }, [layoutMode, rfInstance]);

    // Helper: Calculate geometric handles based on positions
    const getGeometricHandles = (source: LayoutNode, target: LayoutNode) => {
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        let sourceHandle = 'source-right';
        let targetHandle = 'target-left';

        if (Math.abs(dy) > Math.abs(dx) * 1.2) {
            if (dy > 0) { // Target is below
                sourceHandle = 'source-bottom';
                targetHandle = 'target-top';
            } else { // Target is above
                sourceHandle = 'source-top';
                targetHandle = 'target-bottom';
            }
        } else {
            if (dx > 0) { // Target is right
                sourceHandle = 'source-right';
                targetHandle = 'target-left';
            } else { // Target is left
                sourceHandle = 'source-left';
                targetHandle = 'target-right';
            }
        }
        return { sourceHandle, targetHandle };
    };

    // 2. Physics Sync (Handle Position Updates from Runner)
    useEffect(() => {
        const handleTick = (updatedLayoutNodes: LayoutNode[]) => {
            const layoutNodeMap = new Map(updatedLayoutNodes.map(n => [n.id, n]));

            // A. Update Nodes
            setNodes(currentNodes =>
                currentNodes.map(node => {
                    const layoutNode = layoutNodeMap.get(node.id);
                    if (!layoutNode) return node;
                    return {
                        ...node,
                        position: { x: layoutNode.x, y: layoutNode.y }
                    };
                })
            );

            // B. Update Edges (Dynamic Handles) - [US-CAUSA-Visual]
            // We update handles on every tick so they snap to the correct side during drag
            setEdges(currentEdges =>
                currentEdges.map(edge => {
                    const sourceNode = layoutNodeMap.get(edge.source);
                    const targetNode = layoutNodeMap.get(edge.target);

                    if (!sourceNode || !targetNode) return edge;

                    const { sourceHandle, targetHandle } = getGeometricHandles(sourceNode, targetNode);

                    // Optimization: Only return new object if changed
                    if (edge.sourceHandle === sourceHandle && edge.targetHandle === targetHandle) {
                        return edge;
                    }

                    return {
                        ...edge,
                        sourceHandle,
                        targetHandle
                    };
                })
            );
        };

        runner.onTick(handleTick);
        runner.start();

        return () => {
            runner.stop();
        };
    }, [runner, setNodes, setEdges]);

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onInit={(instance) => {
                    setRfInstance(instance);
                    if (onInit) onInit(instance);
                }}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                onNodeClick={(_, node) => {
                    if (onSelect) {
                        // Reconstruct a data object that mimics what Inspector expects.
                        onSelect({ type: 'node', data: { id: node.id, ...node.data } });
                    }
                }}
                onNodeDoubleClick={(_, node) => {
                    if (onEdit) {
                        onEdit({ type: 'node', data: { id: node.id, ...node.data } });
                    }
                }}
                onEdgeClick={(_, edge) => {
                    if (onSelect) {
                        onSelect({ type: 'link', data: { id: edge.id, source: edge.source, target: edge.target, ...edge.data } });
                    }
                }}
                onEdgeDoubleClick={(_, edge) => {
                    if (onEdit) {
                        onEdit({ type: 'link', data: { id: edge.id, source: edge.source, target: edge.target, ...edge.data } });
                    }
                }}
                onPaneClick={() => {
                    if (onSelect) onSelect(null);
                    setContextMenu(null);
                }}
                onNodeDragStart={(_, node) => {
                    if (runner.onDrag) {
                        runner.onDrag(node.id, node.position.x, node.position.y, true);
                    }
                }}
                onNodeDrag={(_, node) => {
                    // 1. Sync ReactFlow position to LayoutSession (Legacy/Rail support)
                    const layoutNodes = session.getNodes();
                    const layoutNode = layoutNodes.find(n => n.id === node.id);
                    if (layoutNode) {
                        layoutNode.x = node.position.x;
                        layoutNode.y = node.position.y;
                    }

                    // 2. Notify Runner (Force Physics)
                    if (runner.onDrag) {
                        runner.onDrag(node.id, node.position.x, node.position.y, true);
                    }
                }}
                onNodeDragStop={(_, node) => {
                    if (runner.onDrag) {
                        runner.onDrag(node.id, node.position.x, node.position.y, false);
                    }
                }}
                nodeOrigin={[0.5, 0.5]}
                onNodeContextMenu={onNodeContextMenu}
                onEdgeContextMenu={onEdgeContextMenu}
                minZoom={0.1}
                maxZoom={4}
                fitView
                onMove={(_, viewport) => {
                    if (onViewportChange) {
                        onViewportChange(viewport);
                    }
                }}
            >
                <Background />
                <ViewControls />
            </ReactFlow>

            {contextMenu && (
                <CanvasContextMenu
                    position={{ x: contextMenu.x, y: contextMenu.y }}
                    contextObject={{ id: contextMenu.nodeId, type: contextMenu.type, label: contextMenu.label }}
                    onDismiss={() => setContextMenu(null)}
                    onOpenObjectConversation={handleOpenObjectConversation}
                    onEdit={(obj) => onEdit && onEdit({ type: obj.type as any, data: contextMenu.data || obj })}
                />
            )}
        </div>
    );
};
