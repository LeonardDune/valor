import type { LayoutNode, LayoutLink, LayoutConfig } from './types';
import type { CausalNode, CausalLink } from '../types';

/**
 * Encapsulates the state for a single layout run.
 * Ensures isolation by deep-copying input data.
 */
export class LayoutSession {
    private nodes: LayoutNode[];
    private links: LayoutLink[];
    private config: LayoutConfig;

    constructor(
        inputNodes: CausalNode[],
        inputLinks: CausalLink[],
        config: LayoutConfig,
        initialPositions?: Map<string, { x: number, y: number }>
    ) {
        this.config = config;

        // Deep copy and transform to Layout types
        // Initialize positions randomly OR from provided seed
        this.nodes = inputNodes.map(n => {
            const seed = initialPositions?.get(n.id);
            // Center Jitter Initialization
            // Instead of full random (0-1000), start near center to mimic "Explosion" effect
            const cx = config.width / 2;
            const cy = config.height / 2;
            return {
                id: n.id,
                x: seed ? seed.x : cx + (Math.random() - 0.5) * 50,
                y: seed ? seed.y : cy + (Math.random() - 0.5) * 50,
                vx: 0,
                vy: 0,
                radius: n.type === 'system' ? 40 : 20,
                isSystem: n.type === 'system',
                rawType: n.role || n.type
            };
        });

        this.links = inputLinks.map(l => ({
            id: l.id,
            source: l.source,
            target: l.target
        }));
    }

    public getNodes(): LayoutNode[] {
        return this.nodes;
    }

    public getLinks(): LayoutLink[] {
        return this.links;
    }

    public getConfig(): LayoutConfig {
        return this.config;
    }

    /**
     * Updates positions based on a tick or external force.
     * This is where the simulation writes back to the session state.
     */
    public updatePositions(updatedNodes: LayoutNode[]): void {
        // In a strictly immutable setup we might return a new Session,
        // but for performance in an animation loop mutation of internal state is acceptable
        // as long as the Session itself is an isolated instance.
        this.nodes = updatedNodes;
    }

    /**
     * Synchronizes the internal graph state with new domain data (Hydration).
     * Critical: Preserves positions of existing nodes to prevent 'jumping'.
     */
    public syncGraph(newNodes: CausalNode[], newLinks: CausalLink[]): void {
        const existingNodeMap = new Map(this.nodes.map(n => [n.id, n]));

        // 1. Merge Nodes (Preserve Physics State)
        this.nodes = newNodes.map(n => {
            const existing = existingNodeMap.get(n.id);
            if (existing) {
                // Keep existing position/velocity
                return {
                    ...existing,
                    radius: n.type === 'system' ? 40 : 20, // Update structural props if changed
                    isSystem: n.type === 'system',
                    rawType: n.role || n.type
                };
            }
            // New Node: Random Position
            // New Node: Center Jitter
            const cx = this.config.width / 2;
            const cy = this.config.height / 2;
            return {
                id: n.id,
                x: cx + (Math.random() - 0.5) * 50,
                y: cy + (Math.random() - 0.5) * 50,
                vx: 0,
                vy: 0,
                radius: n.type === 'system' ? 40 : 20,
                isSystem: n.type === 'system',
                rawType: n.role || n.type
            };
        });

        // 2. Refresh Links (Full Replace is usually fine for links, D3 re-binds them)
        // But we need to ensure Source/Target match the NEW node objects (or IDs if D3 handles it).
        // Since our Interface defines source/target as string | LayoutNode, 
        // we reset them to strings so D3 can re-resolve them in the next tick?
        // OR we map them to the new node objects immediately if we have them.

        // Strategy: Reset to IDs. The Runner/Simulation will need to re-initialize links.
        // NOTE: This implies the Runner needs to be notified of topology changes.
        this.links = newLinks.map(l => ({
            id: l.id,
            source: l.source,
            target: l.target,
            // Defaults from US-CAUSA-05
            status: 'validated',
            certainty: 1.0
        }));
    }
}
