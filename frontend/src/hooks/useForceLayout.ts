import { useEffect, useRef, useMemo } from 'react';
import { type Node, type Edge, useReactFlow, useNodesInitialized } from 'reactflow';
import {
    forceSimulation,
    forceLink,
    forceManyBody,
    forceX,
    forceY,
    forceCollide,
    type SimulationNodeDatum,
    type SimulationLinkDatum,
    type Simulation
} from 'd3-force';

const CARD_WIDTH = 140;
const CARD_HEIGHT = 100;

// Define specific D3 Node type extending the simulation datum
interface D3Node extends SimulationNodeDatum {
    id: string;
    type: string;
    width: number;
    height: number;
    // Optional props used in logic
    position?: { x: number; y: number };
}

// Define specific D3 Link type
interface D3Link extends SimulationLinkDatum<D3Node> {
    source: string | D3Node;
    target: string | D3Node;
}

export const useForceLayout = (
    nodes: Node[],
    edges: Edge[],
    layoutMode: 'force' | 'system' = 'force',
    config: { scopeW: number; scopeH: number } = { scopeW: 1000, scopeH: 700 },
    layoutEpoch: number = 0
) => {
    const { setNodes } = useReactFlow();
    const nodesInitialized = useNodesInitialized();
    const simulationRef = useRef<Simulation<D3Node, D3Link> | null>(null);

    // Convert React Flow nodes to D3 nodes (mutable)
    const d3Nodes = useMemo<D3Node[]>(() => {
        return nodes
            .filter(n => n.type !== 'systemScope')
            .map((n) => ({
                id: n.id,
                x: n.position.x ?? 0,
                y: n.position.y ?? 0,
                vx: 0,
                vy: 0,
                type: (n.data?.type || 'systeemelement').toLowerCase(),
                width: n.width || CARD_WIDTH,
                height: n.height || CARD_HEIGHT,
                fx: null,
                fy: null
            }));
    }, [nodes.length, layoutMode, layoutEpoch]);

    const d3Links = useMemo<D3Link[]>(() => {
        return edges.map((e) => ({
            source: e.source,
            target: e.target
        }));
    }, [edges.length, layoutMode, layoutEpoch]);

    useEffect(() => {
        if (!nodes.length || !nodesInitialized) return;
        if (simulationRef.current) simulationRef.current.stop();

        const simulation = forceSimulation<D3Node, D3Link>(d3Nodes);

        if (layoutMode === 'force') {
            d3Nodes.forEach((n) => { n.fx = null; n.fy = null; });

            simulation
                .force('charge', forceManyBody().strength(-600).distanceMax(2000))
                .force('collide', forceCollide(150).strength(1.0))
                .force('link', forceLink<D3Node, D3Link>(d3Links).id((d) => d.id).distance(200).strength(0.5))
                .force('x', forceX(0).strength(0.02))
                .force('y', forceY(0).strength(0.02));

            simulation.alpha(1).restart();

        } else if (layoutMode === 'system') {
            const { scopeW, scopeH } = config;

            const middelen = d3Nodes.filter((n) => n.type === 'middel');
            const externen = d3Nodes.filter((n) => n.type === 'extern');
            const criteria = d3Nodes.filter((n) => n.type === 'criterium');
            const systemElements = d3Nodes.filter((n) => n.type === 'systeemelement' || n.type === 'factor');

            const distribute = (group: D3Node[], axis: 'x' | 'y', fixedVal: number, len: number) => {
                const usableLen = len * 0.85;
                group.forEach((n, i) => {
                    const offset = ((i + 0.5) / group.length - 0.5) * usableLen;
                    if (axis === 'y') { n.fx = fixedVal; n.fy = offset; }
                    else { n.fx = offset; n.fy = fixedVal; }
                });
            };

            distribute(middelen, 'y', -scopeW / 2, scopeH);
            distribute(externen, 'x', -scopeH / 2, scopeW);
            distribute(criteria, 'y', scopeW / 2, scopeH);

            systemElements.forEach((n) => { n.fx = null; n.fy = null; });

            const boxingForce = () => {
                const padding = 20;
                const maxX = (scopeW / 2) - CARD_WIDTH - padding;
                const maxY = (scopeH / 2) - CARD_HEIGHT - padding;

                for (const node of systemElements) {
                    if (node.x !== undefined && node.vx !== undefined) {
                        if (node.x < -maxX) { node.x = -maxX; node.vx *= 0.1; }
                        if (node.x > maxX) { node.x = maxX; node.vx *= 0.1; }
                    }
                    if (node.y !== undefined && node.vy !== undefined) {
                        if (node.y < -maxY) { node.y = -maxY; node.vy *= 0.1; }
                        if (node.y > maxY) { node.y = maxY; node.vy *= 0.1; }
                    }
                }
            };

            simulation
                .force('charge', forceManyBody().strength(-300).distanceMax(500))
                .force('collide', forceCollide(80))
                .force('link', forceLink<D3Node, D3Link>(d3Links).id((d) => d.id).distance(100).strength(0.5))
                .force('center_gravity_x', forceX(0).strength(0.05))
                .force('center_gravity_y', forceY(0).strength(0.2))
                .force('boxing', boxingForce);
        }

        simulation.on('tick', () => {
            setNodes((prevNodes) => {
                return prevNodes.map((node) => {
                    const d3Node = d3Nodes.find((d) => d.id === node.id);
                    if (!d3Node || d3Node.x === undefined || d3Node.y === undefined) return node;

                    // Optimization: Check for delta to avoid useless re-renders
                    if (Math.abs(node.position.x - d3Node.x) < 0.1 && Math.abs(node.position.y - d3Node.y) < 0.1) {
                        return node;
                    }

                    return {
                        ...node,
                        position: {
                            x: d3Node.x,
                            y: d3Node.y
                        }
                    };
                });
            });
        });

        simulationRef.current = simulation;

        return () => {
            simulation.stop();
        };
    }, [d3Nodes, d3Links, nodesInitialized, setNodes, layoutMode, config.scopeW, config.scopeH, layoutEpoch]);

    return {
        simulation: simulationRef.current,
        d3Nodes,
        stop: () => simulationRef.current?.stop(),
        restart: () => {
            if (simulationRef.current) {
                simulationRef.current.alpha(1).restart();
            }
        }
    };
};
