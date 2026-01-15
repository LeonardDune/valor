/**
 * Layout-specific type definitions.
 * These are optimized for the simulation and may differ from the render/domain types.
 */

export interface LayoutNode {
    id: string; // d3 expects string or number, strict string here
    x: number;
    y: number;
    vx?: number;
    vy?: number;
    fx?: number | null; // Fixed X position (for dragging)
    fy?: number | null; // Fixed Y position

    // Domain data attached for weight/sizing calculations
    radius: number;
    isSystem: boolean;
}

export interface LayoutLink {
    id: string;
    source: string | LayoutNode; // D3 mutates this to object ref
    target: string | LayoutNode; // D3 mutates this to object ref

    // Layout properties
    strength?: number;
    distance?: number;

    // Visualization properties (from US-CAUSA-05)
    status?: 'proposed' | 'validated' | 'rejected';
    certainty?: number; // 0.0 - 1.0 (Opacity)
}

export interface LayoutConfig {
    width: number;
    height: number;
    alphaDecay: number;
    velocityDecay: number;
    // ... future physics params
}
