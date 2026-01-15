import { type FunctionComponent, useEffect } from 'react';
import ReactFlow, {
    type Node,
    type Edge,
    useNodesState,
    useEdgesState,
    Background,
    Controls
} from 'reactflow';
import 'reactflow/dist/style.css';

import type { LayoutSession } from '../layout/session';
import type { LayoutRunner } from '../layout/runner';
import type { LayoutNode } from '../layout/types';
import CLDNode from './nodes/CLDNode';
import CLDEdge from './edges/CLDEdge';

interface CLDViewProps {
    session: LayoutSession;
    runner: LayoutRunner;
}

const nodeTypes = {
    cldNode: CLDNode
};

const edgeTypes = {
    cldEdge: CLDEdge
};

export const CLDView: FunctionComponent<CLDViewProps> = ({ session, runner }) => {
    // Initial State from Session
    const initialNodes: Node[] = session.getNodes().map(n => ({
        id: n.id,
        position: { x: n.x, y: n.y },
        data: { label: n.id }, // Todo: Use label from internal map if available
        type: 'cldNode'
    }));

    const initialEdges: Edge[] = session.getLinks().map(l => ({
        id: l.id,
        source: typeof l.source === 'object' ? (l.source as any).id : l.source,
        target: typeof l.target === 'object' ? (l.target as any).id : l.target,
        type: 'cldEdge',
        data: { polarity: '+' } // Todo: Real polarity from link data
    }));

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, , onEdgesChange] = useEdgesState(initialEdges);

    // Sync Loop
    useEffect(() => {
        const handleTick = (updatedLayoutNodes: LayoutNode[]) => {
            setNodes(currentNodes =>
                currentNodes.map(node => {
                    const layoutNode = updatedLayoutNodes.find(n => n.id === node.id);
                    if (!layoutNode) return node;

                    // Optimization: Only update if changed significantly? 
                    // For now, raw sync.
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
                fitView
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
};
