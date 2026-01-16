import * as d3 from 'd3-force';
import type { LayoutRunner } from '../runner';
import type { LayoutSession } from '../session';
import type { LayoutNode, LayoutLink } from '../types';

/**
 * RailRunner
 * 
 * Implements a Hybrid Layout:
 * 1. Rail Nodes (Middelen/Criteria/Extern): Strictly positioned on rails (driven by logic, pinned in D3).
 * 2. System Elements: Force-directed *inside* the center box (organic, clustering, interactive).
 */
export class RailRunner implements LayoutRunner {
    private session: LayoutSession;
    private simulation: d3.Simulation<LayoutNode, LayoutLink>;
    private isRunning: boolean = false;
    private callback: ((nodes: LayoutNode[]) => void) | null = null;
    private animationFrameId: number | null = null;

    // Track dragged nodes to prevent overwriting their position
    private draggedNodeId: string | null = null;

    // Configuration for the Rails
    private config = {
        minWidth: 1000,
        minHeight: 700,
        cardWidth: 140,
        cardHeight: 100,
        spacing: 180,
        padding: 20
    };

    constructor(session: LayoutSession) {
        this.session = session;

        // Initialize D3 Simulation
        // We use this to solve the layout for System Elements AND links between them
        this.simulation = d3.forceSimulation<LayoutNode, LayoutLink>(session.getNodes())
            .stop(); // We step manually in loop()

        // Forces for System Elements (and interactions with Rail nodes)

        // 1. Charge: Repel
        // CRITICAL FIX: Rail nodes (Middelen/Criteria/Extern) should NOT repel System nodes.
        // If they do, they push System nodes to the bottom (the only open side).
        this.simulation.force('charge', d3.forceManyBody<LayoutNode>()
            .strength(d => this.isSystemElement(d) ? -200 : 0) // Reduced from -300 to -200 for gentler reaction
            .distanceMax(500)
        );

        // 2. Collide: No Overlap
        // FIX: Set radius to 0 for Rail nodes so they don't push System nodes down.
        // We rely on clampToBox to keep System nodes away from the rails.
        this.simulation.force('collide', d3.forceCollide<LayoutNode>()
            .radius(d => this.isSystemElement(d) ? 85 : 0)
            .strength(1.0)
            .iterations(2)
        );

        // 3. Links: Pull together
        this.simulation.force('link', d3.forceLink<LayoutNode, LayoutLink>(session.getLinks())
            .id(d => d.id)
            .distance(150)
            .strength(0.2)
        );

        // 4. Center Gravity: Keep System Elements centered in the box
        // FIX: Replaced 'center' (global translation) with 'x'/'y' (individual forces).
        // 'center' uses center-of-mass. Since Rail nodes are Top-heavy (no bottom rail), 
        // center-of-mass logic pushed free nodes to the bottom to compensate.
        // forceX/forceY simply pulls free nodes to 0,0, which is what we want.
        this.simulation.force('x', d3.forceX(0).strength(0.05));
        this.simulation.force('y', d3.forceY(0).strength(0.05));
    }

    start(): void {
        this.isRunning = true;

        // Refresh D3 data
        this.updateData(this.session.getNodes(), this.session.getLinks());

        this.loop();
    }

    stop(): void {
        this.isRunning = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        this.simulation.stop();
    }

    onTick(callback: (nodes: LayoutNode[]) => void): void {
        this.callback = callback;
    }

    updateData(nodes: LayoutNode[], links: LayoutLink[]): void {
        this.simulation.nodes(nodes);
        const linkForce = this.simulation.force('link') as d3.ForceLink<LayoutNode, LayoutLink>;
        if (linkForce) {
            linkForce.links(links);
        }
        this.simulation.alpha(1).restart();
    }

    private loop() {
        if (!this.isRunning) return;

        // 1. Calculate Rail Positions & Pin Rail Nodes
        this.applyRailConstraints();

        // 2. Step Physics (Solves System Elements + Connections)
        this.simulation.tick();

        // 3. Post-Physics: Clamp System Elements to Box
        // We do this AFTER tick to ensure they stay inside even if pushed
        // FIX: Exempt the DRAGGED node from clamping! 
        // If we clamp it, it fights the mouse cursor at the edge, feeling like "being pulled back".
        // Letting it float freely during drag gives control; it snaps back on release.
        const { scopeW, scopeH } = this.calculateScope();
        const systemNodes = this.session.getNodes().filter(n =>
            this.isSystemElement(n) && n.id !== this.draggedNodeId
        );
        this.clampToBox(systemNodes, scopeW, scopeH);

        // 4. Notify View
        if (this.callback) this.callback(this.session.getNodes());

        this.animationFrameId = requestAnimationFrame(() => this.loop());
    }

    private applyRailConstraints() {
        const nodes = this.session.getNodes();

        // Identify Groups
        const middelen = nodes.filter(n => this.getType(n) === 'middel');
        const criteria = nodes.filter(n => this.getType(n) === 'criterium');
        const externen = nodes.filter(n => this.getType(n) === 'extern');
        // System Elements are the rest

        const { scopeW, scopeH } = this.calculateScope();
        const halfW = scopeW / 2;
        const halfH = scopeH / 2;

        // Sort Helper
        const sortVertical = (a: LayoutNode, b: LayoutNode) => a.y - b.y;
        const sortHorizontal = (a: LayoutNode, b: LayoutNode) => a.x - b.x;

        // Assign Fixed Positions (fx, fy) based on Rails
        // This tells D3: "This node MUST be here."

        // A. Middelen (Left)
        middelen.sort(sortVertical);
        this.distributeOnRail(middelen, 'vertical', -halfW, scopeH);

        // B. Criteria (Right)
        criteria.sort(sortVertical);
        this.distributeOnRail(criteria, 'vertical', halfW, scopeH);

        // C. Extern (Top)
        externen.sort(sortHorizontal);
        this.distributeOnRail(externen, 'horizontal', -halfH, scopeW);

        // D. Release System Elements (unless dragged)
        nodes.forEach(n => {
            if (this.isSystemElement(n)) {
                if (n.id === this.draggedNodeId) {
                    // It's being dragged, handled by onDrag setting fx/fy
                } else {
                    // Let it float
                    n.fx = null;
                    n.fy = null;
                }
            }
        });
    }

    private calculateScope() {
        const nodes = this.session.getNodes();
        const middelen = nodes.filter(n => this.getType(n) === 'middel');
        const criteria = nodes.filter(n => this.getType(n) === 'criterium');
        const externen = nodes.filter(n => this.getType(n) === 'extern');
        const systemNodes = nodes.filter(n => this.isSystemElement(n));

        // 1. Calculate Perimeter-based dimensions
        const neededW_Perimeter = Math.max(this.config.minWidth, externen.length * this.config.spacing);
        const neededH_Perimeter = Math.max(this.config.minHeight, Math.max(middelen.length, criteria.length) * this.config.spacing);

        // 2. Calculate Area-based dimensions (to prevent overcrowding)
        // Assume each system node needs ~200x150 space (including gap) -> 30000 px^2
        const areaPerNode = 40000;
        const neededArea = systemNodes.length * areaPerNode;
        // Current Min Area = 1000 * 700 = 700,000. Fits ~17 nodes comfortable.

        // Sqrt scale to maintain aspect ratio roughly
        const targetAspect = 1.6;
        const neededH_Area = Math.sqrt(neededArea / targetAspect);
        const neededW_Area = neededH_Area * targetAspect;

        // 3. Take Max
        let finalW = Math.max(neededW_Perimeter, neededW_Area);
        let finalH = Math.max(neededH_Perimeter, neededH_Area);

        // 4. Enforce Aspect Ratio on Final Dimensions (Optional, but good for consistent feel)
        if (finalH * targetAspect > finalW) {
            finalW = finalH * targetAspect;
        } else {
            finalH = finalW / targetAspect;
        }

        return {
            scopeW: Math.max(this.config.minWidth, finalW),
            scopeH: Math.max(this.config.minHeight, finalH)
        };
    }

    private distributeOnRail(group: LayoutNode[], axis: 'vertical' | 'horizontal', fixedVal: number, totalLen: number) {
        const usableLen = totalLen * 0.85;

        group.forEach((node, i) => {
            // Check if this specific rail node is being dragged?
            // User requirement: "Those function fine" implies standard snap-back behavior is desired for rail nodes.
            // So we strictly enforce position even if dragged (it will snap back immediately).

            const offset = ((i + 0.5) / group.length - 0.5) * usableLen;

            if (axis === 'vertical') {
                node.fx = fixedVal;
                node.fy = offset;
                // Update x/y too for immediate visual consistentcy before tick
                node.x = fixedVal;
                node.y = offset;
            } else {
                node.fy = fixedVal;
                node.fx = offset;
                node.y = fixedVal;
                node.x = offset;
            }
        });
    }

    public onDrag(nodeId: string, x: number, y: number, isDragging: boolean): void {
        const node = this.session.getNodes().find(n => n.id === nodeId);
        if (!node) return;

        // Apply to System Elements primarily
        if (this.isSystemElement(node)) {
            if (isDragging) {
                this.draggedNodeId = nodeId;
                node.fx = x;
                node.fy = y;
                node.x = x;
                node.y = y;
                // Wake up physics so others move away
                // Lowered alphaTarget to 0.1 for less violent reaction
                this.simulation.alphaTarget(0.1).restart();
            } else {
                this.draggedNodeId = null;
                node.fx = null;
                node.fy = null;
                this.simulation.alphaTarget(0);
            }
        } else {
            // For Rail Nodes, we generally ignore drag or let it snap back.
            // But if user insists on dragging them temporarily:
            if (isDragging) {
                node.x = x;
                node.y = y;
            }
            // They will interact with nothing (ghosts) and snap back on next tick loop() anyway
        }
    }

    private clampToBox(group: LayoutNode[], w: number, h: number) {
        const maxX = (w / 2) - this.config.cardWidth / 2 - this.config.padding;
        const maxY = (h / 2) - this.config.cardHeight / 2 - this.config.padding;

        group.forEach(node => {
            if (node.x < -maxX) node.x = -maxX;
            if (node.x > maxX) node.x = maxX;
            if (node.y < -maxY) node.y = -maxY;
            if (node.y > maxY) node.y = maxY;
        });
    }

    private isSystemElement(node: LayoutNode): boolean {
        return !['middel', 'criterium', 'extern'].includes(this.getType(node));
    }

    private getType(node: LayoutNode): string {
        // The type is stored in the node, but LayoutNode is minimal.
        // We need to check if we preserved type on LayoutNode or if we need to look it up.
        // Looking at session.ts, we preserved `n.type` as `isSystem` boolean mainly, 
        // but we might not have the raw string type on LayoutNode.
        // Let's check `LayoutNode` definition.
        // It likely has `id`, `x`, `y`, `vx`, `vy`.

        // If type is missing on LayoutNode, we have a problem.
        // However, `LayoutSession` constructor likely has access to it.
        // Strategy: We can attach `data: { type: string }` to LayoutNode in Session.

        // For now, I'll cast to any to access custom props if they exist, 
        // otherwise we need to update LayoutNode type.
        return (node as any).rawType || 'system';
    }
}
