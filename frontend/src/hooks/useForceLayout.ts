import { useEffect, useRef, useMemo } from 'react';
import { type Node, type Edge, useReactFlow, useNodesInitialized } from 'reactflow';
import { forceSimulation, forceLink, forceManyBody, forceX, forceY, forceCollide } from 'd3-force';

const CARD_WIDTH = 140;
const CARD_HEIGHT = 100;

export const useForceLayout = (
    nodes: Node[],
    edges: Edge[],
    layoutMode: 'force' | 'system' = 'force',
    config: { scopeW: number; scopeH: number } = { scopeW: 1000, scopeH: 700 },
    layoutEpoch: number = 0 // [ADVISOR - EPOCH] Explicit versioning
) => {
    const { setNodes } = useReactFlow();
    const nodesInitialized = useNodesInitialized();
    const simulationRef = useRef<any>(null);

    // Convert React Flow nodes to D3 nodes (mutable)
    const d3Nodes = useMemo(() => {
        // [ADVISOR COMPLIANCE]
        // 1. Create BRAND NEW objects every time. Never reuse D3 objects.
        // 2. Trust the parent 'nodes' state (the parent defines the 'World').
        // 3. Filter out non-physics nodes (SystemScope).

        return nodes
            .filter(n => n.type !== 'systemScope')
            .map((n) => ({
                id: n.id,
                // Use passed positions as start (Parent controls reset vs restore)
                x: n.position.x ?? 0,
                y: n.position.y ?? 0,

                // FORCE FRESH STATE:
                vx: 0,
                vy: 0,

                // Metadata
                type: (n.data?.type || 'systeemelement').toLowerCase(),
                width: n.width || CARD_WIDTH,
                height: n.height || CARD_HEIGHT,

                // Initial Lock State (will be refined by layout mode blocks below)
                fx: null, // [ADVISOR] Explicit null for D3
                fy: null
            }));
    }, [nodes.length, layoutMode, layoutEpoch]); // New nodes or Mode Switch = Rebuild World

    const d3Links = useMemo(() => {
        return edges.map((e) => ({
            source: e.source,
            target: e.target
        }));
    }, [edges.length, layoutMode, layoutEpoch]); // Fix: Re-create links so D3 re-binds them to NEW d3Nodes

    useEffect(() => {
        if (!nodes.length || !nodesInitialized) return;
        if (simulationRef.current) simulationRef.current.stop();

        const simulation = forceSimulation(d3Nodes as any);

        if (layoutMode === 'force') {
            d3Nodes.forEach((n: any) => { n.fx = null; n.fy = null; });

            simulation
                .force('charge', forceManyBody().strength(-600).distanceMax(2000))
                .force('collide', forceCollide(150).strength(1.0)) // Parity with Legacy
                .force('link', forceLink(d3Links).id((d: any) => d.id).distance(200).strength(0.5))
                .force('x', forceX(0).strength(0.02))
                .force('y', forceY(0).strength(0.02));

            // Re-heat aggressively
            simulation.alpha(1).restart();

        } else if (layoutMode === 'system') {
            // --- SYSTEM LAYOUT ---
            const { scopeW, scopeH } = config;

            const middelen = d3Nodes.filter((n: any) => n.type === 'middel');
            const externen = d3Nodes.filter((n: any) => n.type === 'extern');
            const criteria = d3Nodes.filter((n: any) => n.type === 'criterium');
            const systemElements = d3Nodes.filter((n: any) => n.type === 'systeemelement' || n.type === 'factor'); // default fallback

            // Helper to pin nodes
            const distribute = (group: any[], axis: 'x' | 'y', fixedVal: number, len: number) => {
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

            // System Elements: Float in center, clamped
            systemElements.forEach((n: any) => { n.fx = null; n.fy = null; });

            // Boxing Force
            const boxingForce = () => {
                const padding = 20;
                const maxX = (scopeW / 2) - CARD_WIDTH - padding;
                const maxY = (scopeH / 2) - CARD_HEIGHT - padding;

                for (const node of systemElements as any[]) {
                    if (node.x < -maxX) { node.x = -maxX; node.vx *= 0.1; }
                    if (node.x > maxX) { node.x = maxX; node.vx *= 0.1; }
                    if (node.y < -maxY) { node.y = -maxY; node.vy *= 0.1; }
                    if (node.y > maxY) { node.y = maxY; node.vy *= 0.1; }
                }
            };

            simulation
                .force('charge', forceManyBody().strength(-300).distanceMax(500))
                .force('collide', forceCollide(80))
                .force('link', forceLink(d3Links).id((d: any) => d.id).distance(100).strength(0.5))
                .force('center_gravity_x', forceX(0).strength(0.05))
                .force('center_gravity_y', forceY(0).strength(0.2))
                .force('boxing', boxingForce);
        }

        simulation.on('tick', () => {
            setNodes((prevNodes) => {
                return prevNodes.map((node) => {
                    const d3Node = d3Nodes.find((d) => d.id === node.id);
                    if (!d3Node) return node;

                    // Optimization: Check for delta to avoid useless re-renders
                    if (Math.abs(node.position.x - d3Node.x!) < 0.1 && Math.abs(node.position.y - d3Node.y!) < 0.1) {
                        return node;
                    }

                    return {
                        ...node,
                        position: {
                            x: d3Node.x!,
                            y: d3Node.y!
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
