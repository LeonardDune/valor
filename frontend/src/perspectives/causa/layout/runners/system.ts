import * as d3 from 'd3-force';
import type { LayoutRunner } from '../runner';
import type { LayoutSession } from '../session';
import type { LayoutNode, LayoutLink } from '../types';

/**
 * SystemRunner: Uses d3-force to layout nodes based on causal connections.
 * 
 * Goals:
 * 1. Pull related nodes together (Links).
 * 2. Push all nodes apart to prevent overlap (Collision/Charge).
 * 3. Center the graph.
 */
export class SystemRunner implements LayoutRunner {
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
        // System nodes (purple) might repel more?
        this.simulation.force('charge', d3.forceManyBody<LayoutNode>()
            .strength(d => d.isSystem ? -500 : -200)
            .distanceMax(500)
        );

        // Collision: Prevent overlap. Radius matches visual size approx.
        // Node is ~100px wide? Radius ~50-60 is safe.
        this.simulation.force('collide', d3.forceCollide<LayoutNode>()
            .radius(d => d.isSystem ? 70 : 60)
            .strength(0.7)
            .iterations(1)
        );

        // Links: Pull connected nodes together
        this.simulation.force('link', d3.forceLink<LayoutNode, LayoutLink>(session.getLinks())
            .id(d => d.id)
            .distance(150) // Ideal edge length
            .strength(0.2) // Not too rigid
        );

        // Custom Forces? (e.g. keeping 'Extern' on the left?)
        // For 'System' layout we mostly want organic grouping.
        // We can add discrete positioning forces later if needed.
    }

    public start(): void {
        if (this.isRunning) return;
        this.isRunning = true;

        // Alpha determines the "energy" of the simulation.
        // If restarting, we might want to reheat it if it cooled down.
        if (this.simulation.alpha() < 0.1) {
            this.simulation.alpha(1).restart();
        } else {
            this.simulation.restart();
        }

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
}
