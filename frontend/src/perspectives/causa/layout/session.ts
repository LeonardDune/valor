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
        config: LayoutConfig
    ) {
        this.config = config;

        // Deep copy and transform to Layout types
        // Initialize positions randomly or strictly if provided (future)
        this.nodes = inputNodes.map(n => ({
            id: n.id,
            x: Math.random() * config.width,
            y: Math.random() * config.height,
            vx: 0,
            vy: 0,
            radius: n.type === 'system' ? 40 : 20, // Example sizing logic
            isSystem: n.type === 'system'
        }));

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
}
