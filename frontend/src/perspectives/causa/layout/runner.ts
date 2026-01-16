import type { LayoutNode, LayoutLink } from './types';

export interface LayoutRunner {
    /**
     * Starts the layout simulation.
     */
    start(): void;

    /**
     * Stops the layout simulation.
     */
    stop(): void;

    /**
     * Register a callback to be called on every simulation tick.
     * @param callback Function receiving the updated nodes
     */
    onTick(callback: (nodes: LayoutNode[]) => void): void;

    /**
     * Optional hook to notify runner of data changes without recreating it.
     */
    updateData?(nodes: LayoutNode[], links: LayoutLink[]): void;

    /**
     * Optional method to handle manual node dragging.
     * Useful for physics runners to "wake up" or pin nodes.
     */
    onDrag?(nodeId: string, x: number, y: number, isDragging: boolean): void;
}
