import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Wrench, Cloud, Cpu, Target, HelpCircle, Maximize, Plus, Minus } from 'lucide-react';
import { renderToStaticMarkup } from 'react-dom/server';
import * as d3 from 'd3';
import type { Claim } from '../../services/api';

const CARD_WIDTH = 140;
const CARD_HEIGHT = 100;

const iconMap = { middel: Wrench, extern: Cloud, systeemelement: Cpu, criterium: Target, unknown: HelpCircle };
const iconColors = { middel: '#3b82f6', extern: '#64748b', systeemelement: '#8b5cf6', criterium: '#f59e0b', unknown: '#94a3b8' };

const CausalGraph: React.FC<CausalGraphProps> = ({ claims = [], factors = [], onSelect, selectedId }) => {
    const graphRef = useRef<any>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [containerDimensions, setContainerDimensions] = useState({ width: 0, height: 0 });
    const [iconImages, setIconImages] = useState<Record<string, HTMLImageElement>>({});

    // --- MANUAL INTERACTION STATE ---
    const [hoverNodeId, setHoverNodeId] = useState<string | null>(null);
    const [hoverLinkId, setHoverLinkId] = useState<string | null>(null);
    const nodesRef = useRef<any[]>([]);
    const linksRef = useRef<any[]>([]);

    const dragNode = useRef<any | null>(null);
    const isDragging = useRef<boolean>(false);

    // Constants for System Layout (must match layout logic)
    // removed static constants, now dynamic


    // 1. Prepare Icons (Cached)
    useEffect(() => {
        const images: Record<string, HTMLImageElement> = {};
        Object.keys(iconMap).forEach(type => {
            const Icon = iconMap[type as keyof typeof iconMap];
            const color = iconColors[type as keyof typeof iconColors] || iconColors.unknown;
            const svgString = renderToStaticMarkup(<Icon color={color} size={24} />);
            const img = new Image();
            img.src = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svgString as string)))}`;
            images[type] = img;
        });
        setIconImages(images);
    }, []);

    // 2. Data Transformation (Stable IDs)
    const graphData = useMemo(() => {
        const nodes: any[] = [];
        const links: any[] = [];
        const seen = new Set<string>();

        const addNode = (name: string, type: string, dbId?: string) => {
            const id = String(name || 'Unknown').trim();
            if (!seen.has(id)) {
                seen.add(id);
                nodes.push({ id, name: id, type: (type || 'systeemelement').toLowerCase(), dbId });
            }
        };

        // Add explicit factors (orphaned nodes)
        factors.forEach(f => {
            addNode(f.name, f.type, f.id);
        });

        claims.forEach(c => {
            addNode(c.source_node || '', c.source_type || '', c.source_id);
            addNode(c.target_node || '', c.target_type || '', c.target_id);
            links.push({
                source: String(c.source_node || '').trim(),
                target: String(c.target_node || '').trim(),
                source_id: c.source_id,
                target_id: c.target_id,
                polarity: c.polarity || '+',
                id: c.id
            });
        });

        const data = { nodes, links };
        console.log('TRANSFORM: GraphData update', { nodes: nodes.length, links: links.length });
        return data;
    }, [claims, factors]);

    // 2b. Dynamic System Layout Calculations
    const systemLayoutData = useMemo(() => {
        const nodes = graphData.nodes as any[];
        const middelen = nodes.filter(n => (n.type || 'systeemelement') === 'middel');
        const externen = nodes.filter(n => (n.type || 'systeemelement') === 'extern');
        const criteria = nodes.filter(n => (n.type || 'systeemelement') === 'criterium');
        const systemElements = nodes.filter(n => (n.type || 'systeemelement') === 'systeemelement');

        const MIN_W = 1000;
        const MIN_H = 700;
        const ITEM_SPACING = 180; // Card (140) + Gap (40)

        // Calculate needed dimensions based on content
        const neededW = Math.max(MIN_W, externen.length * ITEM_SPACING);
        const neededH = Math.max(MIN_H, Math.max(middelen.length, criteria.length) * ITEM_SPACING);

        // Aspect preservation (aim for ~1.6 or container ratio)
        const targetAspect = containerDimensions.width && containerDimensions.height
            ? containerDimensions.width / containerDimensions.height
            : 1.6;

        let finalW = neededW;
        let finalH = neededW / targetAspect;

        // Ensure Height compliance
        if (finalH < neededH) {
            finalH = neededH;
            finalW = finalH * targetAspect;
        }

        // Ensure MIN dimensions again (redundant but safe)
        finalW = Math.max(MIN_W, finalW);
        finalH = Math.max(MIN_H, finalH);

        return { middelen, externen, criteria, systemElements, scopeW: finalW, scopeH: finalH };
    }, [graphData.nodes, containerDimensions]);

    // Keep nodesRef in sync with simulation values (for manual hit testing)
    useEffect(() => {
        nodesRef.current = graphData.nodes;
        linksRef.current = graphData.links;
    }, [graphData.nodes, graphData.links]);

    // 3. MANUAL INTERACTION LOGIC (The "No-Guesswork" Layer)
    const findNodeAt = useCallback((screenX: number, screenY: number) => {
        if (!graphRef.current || !containerRef.current) return null;
        const rect = containerRef.current.getBoundingClientRect();
        const { x: gx, y: gy } = graphRef.current.screen2GraphCoords(screenX - rect.left, screenY - rect.top);

        const nodes = nodesRef.current;
        for (let i = nodes.length - 1; i >= 0; i--) {
            const n = nodes[i];
            if (typeof n.x === 'number') {
                if (Math.abs(n.x - gx) < CARD_WIDTH / 2 && Math.abs(n.y - gy) < CARD_HEIGHT / 2) return n;
            }
        }
        return null;
    }, []);

    const findLinkAt = useCallback((screenX: number, screenY: number) => {
        if (!graphRef.current || !containerRef.current) return null;
        const rect = containerRef.current.getBoundingClientRect();
        const { x: gx, y: gy } = graphRef.current.screen2GraphCoords(screenX - rect.left, screenY - rect.top);

        const links = linksRef.current;
        const HIT_DISTANCE = 15; // Increased hit area for easier selection

        for (const link of links) {
            const s = link.source;
            const t = link.target;
            if (typeof s.x !== 'number' || typeof t.x !== 'number') continue;

            const x1 = s.x, y1 = s.y, x2 = t.x, y2 = t.y;
            const dx = x2 - x1, dy = y2 - y1;
            const l2 = dx * dx + dy * dy;
            if (l2 === 0) continue;

            let projection = ((gx - x1) * dx + (gy - y1) * dy) / l2;
            projection = Math.max(0, Math.min(1, projection));

            const closestX = x1 + projection * dx;
            const closestY = y1 + projection * dy;
            const dist = Math.sqrt((gx - closestX) ** 2 + (gy - closestY) ** 2);

            if (dist < HIT_DISTANCE) return link;
        }
        return null;
    }, []);

    const handleMouseDown = (e: React.MouseEvent) => {
        const node = findNodeAt(e.clientX, e.clientY);
        if (node) {
            dragNode.current = node;
            isDragging.current = false; // Reset drag status (it's just a click so far)

            // Fix position immediately
            node.fx = node.x;
            node.fy = node.y;
        }
    }


    const snapSystemNodes = useCallback(() => {
        if (!graphRef.current) return;

        const { middelen, externen, criteria, scopeW, scopeH } = systemLayoutData;

        // Helper to snap a group
        const snapGroup = (group: any[], axis: 'x' | 'y', fixedValue: number) => {
            // 1. Sort by current position on the axis
            group.sort((a, b) => {
                const posA = axis === 'y' ? (a.fy ?? a.y) : (a.fx ?? a.x);
                const posB = axis === 'y' ? (b.fy ?? b.y) : (b.fx ?? b.x);
                return posA - posB;
            });

            // 2. Redistribute evenly
            const totalLen = axis === 'y' ? scopeH : scopeW;
            // Use 80% of the edge to avoid corners
            const usableLen = totalLen * 0.85;

            group.forEach((n, i) => {
                const offset = ((i + 0.5) / group.length - 0.5) * usableLen;

                if (axis === 'y') {
                    n.fx = fixedValue;
                    n.fy = offset;
                } else {
                    n.fx = offset;
                    n.fy = fixedValue;
                }
            });
        };

        // Snap all groups
        snapGroup(middelen, 'y', -scopeW / 2);      // Left
        snapGroup(externen, 'x', -scopeH / 2);      // Top
        snapGroup(criteria, 'y', scopeW / 2);       // Right

        // Don't need to snap systemElements (they float)

        graphRef.current.d3ReheatSimulation();
    }, [systemLayoutData]);

    const handleMouseUp = () => {
        if (dragNode.current) {
            const node = dragNode.current;

            // If in System Mode and it's a Systeemelement, release it to float
            if (layoutMode === 'system') {
                if ((node.type || 'systeemelement') === 'systeemelement') {
                    node.fx = undefined;
                    node.fy = undefined;
                    if (graphRef.current) graphRef.current.d3ReheatSimulation();
                } else {
                    // It's a border node! Snap everything to grid to resolve overlaps
                    snapSystemNodes();
                }
            }

            dragNode.current = null;
        }
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        // 1. Handle Dragging
        if (dragNode.current) {
            isDragging.current = true;
            const node = dragNode.current;

            if (!graphRef.current || !containerRef.current) return;
            const rect = containerRef.current.getBoundingClientRect();
            const { x: gx, y: gy } = graphRef.current.screen2GraphCoords(e.clientX - rect.left, e.clientY - rect.top);

            if (layoutMode === 'system') {
                // --- CONSTRAINED DRAGGING ---
                const { scopeW, scopeH } = systemLayoutData;
                const type = (node.type || 'systeemelement');

                if (type === 'middel') {
                    node.fx = -scopeW / 2; // Locked X
                    node.fy = gy; // Free Y
                } else if (type === 'extern') {
                    node.fx = gx; // Free X
                    node.fy = -scopeH / 2; // Locked Y
                } else if (type === 'criterium') {
                    node.fx = scopeW / 2; // Locked X
                    node.fy = gy; // Free Y
                } else {
                    // Systeemelement: Constrained to Box
                    const padding = 20;
                    const maxX = (scopeW / 2) - CARD_WIDTH - padding;
                    const maxY = (scopeH / 2) - CARD_HEIGHT - padding;

                    // Clamp
                    node.fx = Math.max(-maxX, Math.min(maxX, gx));
                    node.fy = Math.max(-maxY, Math.min(maxY, gy));
                }
            } else {
                // --- FREE DRAGGING ---
                node.fx = gx;
                node.fy = gy;
            }

            // Reheat simulation to resolve overlaps/links smoothly
            graphRef.current.d3ReheatSimulation();
            return;
        }

        // 2. Handle Hover (only if not dragging)
        const node = findNodeAt(e.clientX, e.clientY);
        const link = !node ? findLinkAt(e.clientX, e.clientY) : null;

        // --- INTERACTION CONFLICT FIX ---
        // If we are over a node/link OR dragging, disable the library's canvas interaction
        // so it doesn't hijack the event for Panning/Zooming.
        const canvas = containerRef.current?.querySelector('canvas');
        if (canvas) {
            if (node || link || isDragging.current) {
                canvas.style.pointerEvents = 'none';
            } else {
                canvas.style.pointerEvents = 'all';
            }
        }

        const newNodeId = node ? String(node.id) : null;
        const newLinkId = link ? String(link.id) : null;

        if (newNodeId !== hoverNodeId || newLinkId !== hoverLinkId) {
            setHoverNodeId(newNodeId);
            setHoverLinkId(newLinkId);
            if (containerRef.current) containerRef.current.style.cursor = (node || link) ? 'pointer' : 'default';
        }
    };

    const handleClick = (e: React.MouseEvent) => {
        if (isDragging.current) return; // Ignore clicks if we just dragged

        const node = findNodeAt(e.clientX, e.clientY);
        if (node) {
            onSelect?.({ type: 'node', data: node });
            return;
        }

        const link = findLinkAt(e.clientX, e.clientY);
        if (link) {
            onSelect?.({ type: 'link', data: link });
            return;
        }

        onSelect?.(null);
    };

    // --- LAYOUT MODES ---
    const [layoutMode, setLayoutMode] = useState<'force' | 'system'>('force');

    // 4. Force Simulation Tuning
    useEffect(() => {
        if (graphRef.current) {
            const fg = graphRef.current;
            const nodes = graphData.nodes;

            if (layoutMode === 'system') {
                // --- SYSTEM DIAGRAM LAYOUT ---

                // Use calculated Layout Data
                const { middelen, externen, criteria, systemElements, scopeW, scopeH } = systemLayoutData;

                // 1. Position "Middel" (Left Side) - ON THE BORDER
                // Initial distribution (Snap logic will refine this on drag)
                // We re-use logic similar to snapSystemNodes but driven by index for default stability
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

                // 4. Position "Systeemelement" (Inside Scope - Semi-dynamic)
                // We remove fx/fy to let them float, but add a strong center force
                systemElements.forEach(n => {
                    n.fx = undefined;
                    n.fy = undefined;
                });

                // Apply standard forces for the inner elements
                // Limit charge distance so top nodes don't push bottom nodes forever
                fg.d3Force('charge', d3.forceManyBody().strength(-300).distanceMax(500));
                fg.d3Force('collide', d3.forceCollide(80));
                fg.d3Force('link', d3.forceLink().distance(100).strength(0.5));
                fg.d3Force('center', null); // IMPORTANT: Disable auto-centering of mass

                // Centering "Gravity" to prevent sinking
                fg.d3Force('center_gravity_x', d3.forceX(0).strength(0.05));
                fg.d3Force('center_gravity_y', d3.forceY(0).strength(0.2)); // Moderate pull is now enough due to limited charge


                // Add bounding box force for system elements
                // Custom force to keep them inside the dotted rectangle
                const boxingForce = () => {
                    const padding = 20;
                    // To prevent overlap, the center of the inner node must be at least 
                    // CARD_WIDTH away from the center of the border node (which is at SCOPE_W/2).
                    // Calculation: Limit = (Scope/2) - (CardWidth/2 "border node inner half") - (CardWidth/2 "inner node outer half") - padding
                    // Simplifies to: Limit = (Scope/2) - CardWidth - padding

                    const maxX = (scopeW / 2) - CARD_WIDTH - padding;
                    const maxY = (scopeH / 2) - CARD_HEIGHT - padding;

                    for (const node of systemElements) {
                        // Strict Clamping
                        if (node.x < -maxX) { node.x = -maxX; node.vx *= 0.1; }
                        if (node.x > maxX) { node.x = maxX; node.vx *= 0.1; }
                        if (node.y < -maxY) { node.y = -maxY; node.vy *= 0.1; }
                        if (node.y > maxY) { node.y = maxY; node.vy *= 0.1; }
                    }
                };
                fg.d3Force('boxing', boxingForce);

            } else {
                // --- FORCE DIRECTED LAYOUT ---
                nodes.forEach(n => {
                    n.fx = undefined;
                    n.fy = undefined;
                    // No need to manually reset x/y/vx/vy anymore because key={layoutMode} 
                    // forces a fresh component mount, which handles initialization perfectly.
                });

                // 1. Repulsion: Stronger range to separate local clumps
                // 1. Repulsion: Moderate range to separate local clumps without excessive spreading
                fg.d3Force('charge', d3.forceManyBody().strength(-500).distanceMax(2000));

                // 2. Collision: Prevent overlap (Card diag is ~170)
                fg.d3Force('collide', d3.forceCollide(140));

                // 3. Links: Longer to accommodate card size without fighting collision
                fg.d3Force('link', d3.forceLink().distance(200).strength(0.5));

                // 4. Center: Use forceCenter to keep the whole graph in view, 
                // but use VERY weak gravity so clusters can drift apart.
                fg.d3Force('center', d3.forceCenter());
                fg.d3Force('x', d3.forceX(0).strength(0.005));
                fg.d3Force('y', d3.forceY(0).strength(0.005));

                // Disable System Mode forces
                fg.d3Force('boxing', null);
                fg.d3Force('center_gravity_x', null);
                fg.d3Force('center_gravity_y', null);
            }

            fg.d3ReheatSimulation();

            // Auto zoom/pan to fit
            setTimeout(() => fg.zoomToFit(800, 150), 600);
        }
    }, [graphData, layoutMode, systemLayoutData]);

    // 4b. Resize Observer (Fixes Gray Plane Issue)
    useEffect(() => {
        if (!containerRef.current) return;

        const ro = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                setContainerDimensions({ width, height });
            }
        });

        ro.observe(containerRef.current);
        return () => ro.disconnect();
    }, []);

    // 5. Visual Rendering
    const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D) => {
        const nx = node.x ?? 0;
        const ny = node.y ?? 0;

        const isSelected = String(node.id) === String(selectedId) || String(node.dbId) === String(selectedId);
        const isHovered = String(node.id) === hoverNodeId;
        const type = (node.type || 'systeemelement').toLowerCase();
        const color = iconColors[type as keyof typeof iconColors] || iconColors.unknown;

        const x = nx - CARD_WIDTH / 2;
        const y = ny - CARD_HEIGHT / 2;

        ctx.save();
        // Shadow for depth
        ctx.shadowColor = 'rgba(0,0,0,0.08)';
        ctx.shadowBlur = isHovered || isSelected ? 20 : 10;
        ctx.shadowOffsetY = 4;

        // Card Body
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(x, y, CARD_WIDTH, CARD_HEIGHT, 12);
        else ctx.rect(x, y, CARD_WIDTH, CARD_HEIGHT);
        ctx.fill();
        ctx.restore();

        // Border & Selection Highlight
        ctx.lineWidth = isSelected ? 4 : isHovered ? 2 : 1;
        ctx.strokeStyle = isSelected ? '#2563eb' : isHovered ? '#3b82f6' : '#e2e8f0';
        ctx.strokeRect(x, y, CARD_WIDTH, CARD_HEIGHT);

        // Header Tag
        const labelText = type.charAt(0).toUpperCase() + type.slice(1);
        ctx.font = '600 10px Inter, sans-serif';
        const tw = ctx.measureText(labelText).width + 12;
        ctx.fillStyle = color + '15';
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(x + 10, y + 10, tw, 18, 5);
        ctx.fill();
        ctx.fillStyle = color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(labelText, x + 10 + tw / 2, y + 19);

        // Title Central Text
        ctx.fillStyle = '#0f172a';
        ctx.font = 'bold 13px Inter, sans-serif';
        const words = node.name.split(' ');
        let lines: string[] = [];
        let cur = words[0];
        for (let i = 1; i < words.length; i++) {
            if (ctx.measureText(cur + " " + words[i]).width < CARD_WIDTH - 24) cur += " " + words[i];
            else { lines.push(cur); cur = words[i]; }
        }
        lines.push(cur);
        const lh = 18;
        lines.forEach((line, i) => {
            ctx.fillText(line, node.x, node.y + (i - (lines.length - 1) / 2) * lh + 5);
        });

        // Bottom-Right Icon
        const img = iconImages[type] || iconImages.unknown;
        if (img) ctx.drawImage(img, x + CARD_WIDTH - 28, y + CARD_HEIGHT - 28, 18, 18);

        ctx.restore();
    }, [selectedId, hoverNodeId, iconImages, layoutMode]); // Re-render when layout changes (though not strictly needed for nodes)

    const drawScopeBox = useCallback((ctx: CanvasRenderingContext2D) => {
        if (layoutMode !== 'system') return;

        const { scopeW, scopeH } = systemLayoutData;

        const x = -scopeW / 2;
        const y = -scopeH / 2;

        ctx.save();
        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 8]); // Dashed line
        ctx.strokeRect(x, y, scopeW, scopeH);

        // Label
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('SCOPE / SYSTEEMGRENS', x + 10, y - 10);
        ctx.restore();
    }, [layoutMode, systemLayoutData]);

    // Link Rendering with Highlights & Polarity
    const linkCanvasObject = useCallback((link: any, ctx: CanvasRenderingContext2D) => {
        const s = link.source;
        const t = link.target;
        if (typeof s.x !== 'number' || typeof t.x !== 'number') return;

        // Draw Scope Box FIRST (hacky but works since links are drawn after background?)
        // Actually, links are drawn per frame. Better to use onRenderFramePost if possible, 
        // but force-graph doesn't expose a dedicated background draw easily.
        // We will draw it once on the first link (inefficient) or just rely on a separate canvas layer if needed.
        // For now, let's skip drawing it inside link loop to avoid 100x draws.

        const isSelected = String(link.id) === String(selectedId);
        const isHovered = String(link.id) === hoverLinkId;
        const polarity = link.polarity || '+';

        // Draw selection/hover highlight (glow)
        if (isSelected || isHovered) {
            ctx.beginPath();
            ctx.moveTo(s.x, s.y);
            ctx.lineTo(t.x, t.y);
            ctx.lineWidth = isSelected ? 10 : 8;
            ctx.strokeStyle = isSelected ? 'rgba(37, 99, 235, 0.15)' : 'rgba(59, 130, 246, 0.1)';
            ctx.stroke();
        }

        // Main line
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);
        ctx.lineWidth = isSelected ? 2.5 : isHovered ? 2 : 1.5;
        ctx.strokeStyle = isSelected ? '#2563eb' : isHovered ? '#3b82f6' : '#94a3b8';
        ctx.stroke();

        // Arrow head logic (Intersection with card boundary)
        const arrowSize = 8;
        const ang = Math.atan2(t.y - s.y, t.x - s.x);

        // Simple but effective boundary offset
        const cos = Math.abs(Math.cos(ang));
        const sin = Math.abs(Math.sin(ang));
        const scale = Math.min((CARD_WIDTH / 2) / cos, (CARD_HEIGHT / 2) / sin);
        const tx = t.x - (scale + 2) * Math.cos(ang);
        const ty = t.y - (scale + 2) * Math.sin(ang);

        ctx.fillStyle = ctx.strokeStyle;
        ctx.beginPath();
        ctx.moveTo(tx, ty);
        ctx.lineTo(tx - arrowSize * Math.cos(ang - Math.PI / 7), ty - arrowSize * Math.sin(ang - Math.PI / 7));
        ctx.lineTo(tx - arrowSize * Math.cos(ang + Math.PI / 7), ty - arrowSize * Math.sin(ang + Math.PI / 7));
        ctx.fill();

        // Polarity Badge (Mid-point)
        const mx = (s.x + t.x) / 2;
        const my = (s.y + t.y) / 2;

        ctx.save();
        ctx.translate(mx, my);
        ctx.rotate(ang); // Align with line? No, keep it upright for readability
        ctx.rotate(-ang);

        // Badge Background
        ctx.shadowBlur = 4;
        ctx.shadowColor = 'rgba(0,0,0,0.1)';
        ctx.fillStyle = isSelected ? '#2563eb' : (polarity === '-' ? '#ef4444' : '#10b981');
        ctx.beginPath();
        ctx.arc(0, 0, 10, 0, Math.PI * 2);
        ctx.fill();

        // Text (+/-)
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(polarity, 0, 0.5);
        ctx.restore();

    }, [selectedId, hoverLinkId]);

    return (
        <div
            ref={containerRef}
            className="w-full h-full border rounded-xl overflow-hidden relative bg-[#f8fafc] miro-grid"
            onMouseMove={handleMouseMove}
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onClick={handleClick}
        >
            <ForceGraph2D
                ref={graphRef}
                key={layoutMode} // FORCE RE-MOUNT on mode change to fully reset simulation state
                width={containerDimensions.width}
                height={containerDimensions.height}
                graphData={graphData}

                // --- DISABLE LIBRARY EVENT ENGINE ---
                // --- DISABLE LIBRARY EVENT ENGINE ---
                enablePointerInteraction={true}
                enablePanInteraction={true}
                nodeLabel={() => ''}
                onNodeClick={() => { }}
                onNodeHover={() => { }}

                nodeCanvasObject={nodeCanvasObject}
                nodeCanvasObjectMode={() => 'replace'}

                linkCanvasObject={linkCanvasObject}
                linkCanvasObjectMode={() => 'replace'}

                // Render Scope Box before nodes (behind them)
                onRenderFramePre={(ctx) => drawScopeBox(ctx)}

                // Minimal library hit-test to avoid conflicts
                nodeRelSize={0.1}
                linkHoverPrecision={0}

                d3VelocityDecay={0.4}
                cooldownTicks={200}
            />

            {/* Layout Controls - Bottom Right */}
            <div className="absolute bottom-6 right-6 z-20 flex gap-4 items-end">

                {/* Mode Selector */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-1.5 flex flex-col gap-1">
                    <label className="text-[10px] uppercase font-bold text-slate-400 px-2 pt-1">Layout</label>
                    <select
                        value={layoutMode}
                        onChange={(e) => setLayoutMode(e.target.value as any)}
                        className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg block w-full p-2.5 outline-none focus:ring-2 focus:ring-blue-500/20 font-bold cursor-pointer"
                    >
                        <option value="force">⚡ Force Directed</option>
                        <option value="system">🏗️ System Diagram</option>
                    </select>
                </div>

                <div className="flex flex-col gap-2">
                    <button
                        onClick={(e) => { e.stopPropagation(); graphRef.current?.zoom(graphRef.current.zoom() * 1.2, 200); }}
                        className="w-10 h-10 bg-white border border-slate-200 rounded-xl shadow-lg flex items-center justify-center text-slate-500 hover:text-blue-600 transition-all active:scale-95"
                        title="Zoom In"
                    >
                        <Plus size={20} />
                    </button>
                    <button
                        onClick={(e) => { e.stopPropagation(); graphRef.current?.zoom(graphRef.current.zoom() / 1.2, 200); }}
                        className="w-10 h-10 bg-white border border-slate-200 rounded-xl shadow-lg flex items-center justify-center text-slate-500 hover:text-blue-600 transition-all active:scale-95"
                        title="Zoom Out"
                    >
                        <Minus size={20} />
                    </button>
                    <button
                        onClick={(e) => { e.stopPropagation(); graphRef.current?.zoomToFit(400, 100); }}
                        className="w-10 h-10 bg-white border border-slate-200 rounded-xl shadow-lg flex items-center justify-center text-slate-500 hover:text-blue-600 transition-all active:scale-95"
                        title="Fit to Screen"
                    >
                        <Maximize size={20} />
                    </button>
                </div>
            </div>

            <style>{`
                .miro-grid {
                    background-image: radial-gradient(#cbd5e1 0.75px, transparent 0.75px);
                    background-size: 24px 24px;
                }
            `}</style>
        </div>
    );
};

interface CausalGraphProps {
    claims: Claim[];
    factors?: any[];
    onSelect?: (selection: { type: 'node' | 'link'; data: any } | null) => void;
    selectedId?: string | null;
}

export default CausalGraph;
