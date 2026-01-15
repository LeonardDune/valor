import { type FunctionComponent, useEffect } from 'react';
import ReactFlow, {
    useNodesState,
    useEdgesState,
    Background,
    Controls,
} from 'reactflow';
import 'reactflow/dist/style.css';

import type { LayoutSession } from '../layout/session';
import type { LayoutRunner } from '../layout/runner';
import type { LayoutNode } from '../layout/types';
import CLDNode from './nodes/CLDNode';
import CLDEdge from './edges/CLDEdge';

// Correct path if types are in parent/parent
import type { CausalNode, CausalLink } from '../types';

interface CLDViewProps {
    nodes: CausalNode[];
    links: CausalLink[];
    session: LayoutSession;
    runner: LayoutRunner;
    onSelect?: (selection: { type: 'node' | 'link'; data: any } | null) => void;
    selection?: { type: 'node' | 'link'; data: any } | null;
}

const nodeTypes = {
    cldNode: CLDNode
};

const edgeTypes = {
    cldEdge: CLDEdge
};

export const CLDView: FunctionComponent<CLDViewProps> = ({
    nodes: causalNodes,
    links: causalLinks,
    session,
    runner,
    onSelect
}) => {
    // React Flow State
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // 1. Topology Sync (Handle Adds/Removes/Updates from Domain)
    useEffect(() => {
        const layoutNodes = session.getNodes();
        const layoutNodeMap = new Map(layoutNodes.map(n => [n.id, n]));

        setNodes(currentNodes => {
            // Merge Logic:
            // 1. Keep strings that overlap (updates?)
            // 2. Add new
            // 3. Remove old

            // Simplified: Map all causalNodes to RF Nodes
            return causalNodes.map(cn => {
                const existing = currentNodes.find(n => n.id === cn.id);
                const layout = layoutNodeMap.get(cn.id);

                // Use existing position if available, else layout, else 0
                const position = existing ? existing.position : (layout ? { x: layout.x, y: layout.y } : { x: 0, y: 0 });

                return {
                    id: cn.id,
                    type: 'cldNode',
                    position,
                    data: { label: cn.label, type: cn.type, role: cn.role, description: cn.description } // Pass down type/role/desc for styling
                };
            });
        });

        setEdges(() => {
            return causalLinks.map(cl => ({
                id: cl.id,
                source: cl.source,
                target: cl.target,
                type: 'cldEdge',
                data: {
                    polarity: cl.polarity,
                    status: cl.status || 'validated',
                    certainty: cl.certainty
                }
            }));
        });

    }, [causalNodes, causalLinks, session, setNodes, setEdges]); // Dep on causal data


    // 2. Physics Sync (Handle Position Updates from Runner)
    useEffect(() => {
        const handleTick = (updatedLayoutNodes: LayoutNode[]) => {
            setNodes(currentNodes =>
                currentNodes.map(node => {
                    const layoutNode = updatedLayoutNodes.find(n => n.id === node.id);
                    if (!layoutNode) return node;

                    // Only update position
                    return {
                        ...node,
                        position: { x: layoutNode.x, y: layoutNode.y }
                    };
                })
            );
        };

        runner.onTick(handleTick);
        runner.start();

        return () => {
            runner.stop();
        };
    }, [runner, setNodes]);

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                onNodeClick={(_, node) => {
                    if (onSelect) {
                        // Reconstruct a data object that mimics what Inspector expects.
                        // Ideally we pass the full Factor object.
                        // For now: passing id and data.
                        onSelect({ type: 'node', data: { id: node.id, ...node.data } });
                    }
                }}
                onEdgeClick={(_, edge) => {
                    if (onSelect) {
                        onSelect({ type: 'link', data: { id: edge.id, ...edge.data } });
                    }
                }}
                onPaneClick={() => {
                    if (onSelect) onSelect(null);
                }}
                onNodeDrag={(_, node) => {
                    // Sync drag position back to LayoutSession
                    // This is critical effectively to "commit" the drag to the physics/layout state
                    const layoutNodes = session.getNodes();
                    const layoutNode = layoutNodes.find(n => n.id === node.id);
                    if (layoutNode) {
                        layoutNode.x = node.position.x;
                        layoutNode.y = node.position.y;
                        // If using D3, we might want to set fx/fy here or wake simulation
                        // For basic stability, just updating x/y is enough for BasicRunner
                    }
                }}
                fitView
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
};
