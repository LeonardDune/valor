import type { LayoutRunner } from '../runner';
import type { LayoutSession } from '../session';
import type { LayoutNode } from '../types';

/**
 * A basic runner that executes a simple update loop.
 * Currently uses requestAnimationFrame for the loop.
 */
export class BasicRunner implements LayoutRunner {
    private session: LayoutSession;
    private isRunning: boolean = false;
    private tickCallback: ((nodes: LayoutNode[]) => void) | null = null;
    private animationFrameId: number | null = null;

    constructor(session: LayoutSession) {
        this.session = session;
    }

    public start(): void {
        if (this.isRunning) return;
        this.isRunning = true;
        this.loop();
    }

    public stop(): void {
        this.isRunning = false;
        if (this.animationFrameId !== null) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    public onTick(callback: (nodes: LayoutNode[]) => void): void {
        this.tickCallback = callback;
    }

    private loop(): void {
        if (!this.isRunning) return;

        // In a real force simulation, we would call simulation.tick() here.
        // For now, we utilize the session's current state.
        // We could verify position updates here later.

        if (this.tickCallback) {
            this.tickCallback(this.session.getNodes());
        }

        this.animationFrameId = requestAnimationFrame(() => this.loop());
    }
}
