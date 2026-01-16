import * as d3 from 'd3-force';
import type { LayoutRunner } from '../runner';
import type { LayoutSession } from '../session';
import type { LayoutNode, LayoutLink } from '../types';

/**
 * ForceRunner: Uses d3-force to layout nodes based on causal connections.
 * 
 * Goals:
 * 1. Pull related nodes together (Links).
 * 2. Push all nodes apart to prevent overlap (Collision/Charge).
 * 3. Center the graph.
 */
export class ForceRunner implements LayoutRunner {
    private session: LayoutSession;
    private simulation: d3.Simulation<LayoutNode, LayoutLink>;
    private isRunning: boolean = false;
    private tickCallback: ((nodes: LayoutNode[]) => void) | null = null;

    constructor(session: LayoutSession) {
        this.session = session;
        const config = session.getConfig();

        // 1. Initialize Simulation with Nodes
        this.simulation = d3.forceSimulation<LayoutNode, LayoutLink>(session.getNodes())
            .stop(); // Don't auto-start, we control the loop

        // 2. Add Forces
        // Center Gravity: Keeps the graph visible in the viewport center
        this.simulation.force('center', d3.forceCenter(config.width / 2, config.height / 2).strength(0.05));

        // Charge (Many-Body): Nodes repel each other
        // Increased strength again to separate clusters (User feedback: they were too close)
        this.simulation.force('charge', d3.forceManyBody<LayoutNode>()
            .strength(d => d.isSystem ? -400 : -200)
            .distanceMax(800) // Increased interaction distance
        );

        // Collision: Prevent overlap.
        // Increased radius to ~85 (Node width ~140, height ~100) + margin
        // Increased strength to 1.0 (Hard collision)
        this.simulation.force('collide', d3.forceCollide<LayoutNode>()
            .radius(d => d.isSystem ? 100 : 85)
            .strength(1.0)
            .iterations(2)
        );

        // Links: Pull connected nodes together
        this.simulation.force('link', d3.forceLink<LayoutNode, LayoutLink>(session.getLinks())
            .id(d => d.id)
            .distance(180) // Increased distance to give breathing room inside clusters
            .strength(0.2)
        );

        // Custom Forces? (e.g. keeping 'Extern' on the left?)
        // For 'System' layout we mostly want organic grouping.
        // We can add discrete positioning forces later if needed.
    }

    public start(): void {
        if (this.isRunning) return;
        this.isRunning = true;

        // 1. Refresh Data from Session & Reheat
        // We reuse the update logic to ensure consistency
        this.updateData(this.session.getNodes(), this.session.getLinks());

        // Use the simulation's internal timer for efficient updates
        this.simulation.on('tick', () => {
            if (!this.isRunning) return;

            // D3 modifies the node objects in place (x, y, vx, vy)
            // We just need to notify the view.
            if (this.tickCallback) {
                this.tickCallback(this.session.getNodes());
            }
        });
    }

    public stop(): void {
        this.isRunning = false;
        this.simulation.stop();
    }

    public onTick(callback: (nodes: LayoutNode[]) => void): void {
        this.tickCallback = callback;
    }

    public updateData(nodes: LayoutNode[], links: LayoutLink[]): void {
        this.simulation.nodes(nodes);
        const linkForce = this.simulation.force('link') as d3.ForceLink<LayoutNode, LayoutLink>;
        if (linkForce) {
            linkForce.links(links);
        }

        // Reheat if running
        if (this.isRunning) {
            this.simulation.alpha(1).restart();
        }
    }

    public onDrag(nodeId: string, x: number, y: number, isDragging: boolean): void {
        const node = this.session.getNodes().find(n => n.id === nodeId);
        if (!node) return;

        if (isDragging) {
            // Pin the node and wake up simulation
            node.fx = x;
            node.fy = y;
            // Reheat significantly to make it feel reactive
            this.simulation.alphaTarget(0.3).restart();
        } else {
            // Release the node
            node.fx = null;
            node.fy = null;
            this.simulation.alphaTarget(0);
        }
    }
}
