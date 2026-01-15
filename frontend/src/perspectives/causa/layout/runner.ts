import type { LayoutNode } from './types';

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
}
