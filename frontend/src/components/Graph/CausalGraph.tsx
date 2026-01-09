import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Wrench, Cloud, Cpu, Target, HelpCircle, Maximize } from 'lucide-react';
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

    const handleMouseMove = (e: React.MouseEvent) => {
        const node = findNodeAt(e.clientX, e.clientY);
        const link = !node ? findLinkAt(e.clientX, e.clientY) : null;

        const newNodeId = node ? String(node.id) : null;
        const newLinkId = link ? String(link.id) : null;

        if (newNodeId !== hoverNodeId || newLinkId !== hoverLinkId) {
            setHoverNodeId(newNodeId);
            setHoverLinkId(newLinkId);
            if (containerRef.current) containerRef.current.style.cursor = (node || link) ? 'pointer' : 'grab';
        }
    };

    const handleClick = (e: React.MouseEvent) => {
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

    // 4. Force Simulation Tuning
    useEffect(() => {
        if (graphRef.current) {
            const fg = graphRef.current;
            // Use much gentler forces for a compact layout
            fg.d3Force('charge', d3.forceManyBody().strength(-1500));
            fg.d3Force('collide', d3.forceCollide(160));
            fg.d3Force('link', d3.forceLink().distance(180));
            fg.d3Force('center', d3.forceCenter());
            fg.d3Force('x', d3.forceX(0).strength(0.08));
            fg.d3Force('y', d3.forceY(0).strength(0.08));

            fg.d3ReheatSimulation();

            // Zoom to fit on data change
            const timer = setTimeout(() => {
                fg.zoomToFit(800, 150);
            }, 600);
            return () => clearTimeout(timer);
        }
    }, [graphData.nodes.length, graphData.links.length]);

    useEffect(() => {
        const up = () => { if (containerRef.current) setContainerDimensions({ width: containerRef.current.clientWidth, height: containerRef.current.clientHeight }); };
        window.addEventListener('resize', up);
        up();
        return () => window.removeEventListener('resize', up);
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
    }, [selectedId, hoverNodeId, iconImages]);

    // Link Rendering with Highlights & Polarity
    const linkCanvasObject = useCallback((link: any, ctx: CanvasRenderingContext2D) => {
        const s = link.source;
        const t = link.target;
        if (typeof s.x !== 'number' || typeof t.x !== 'number') return;

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
            onClick={handleClick}
        >
            <ForceGraph2D
                ref={graphRef}
                width={containerDimensions.width}
                height={containerDimensions.height}
                graphData={graphData}

                // --- DISABLE LIBRARY EVENT ENGINE ---
                enablePointerInteraction={true}
                nodeLabel={() => ''}
                onNodeClick={() => { }}
                onNodeHover={() => { }}

                nodeCanvasObject={nodeCanvasObject}
                nodeCanvasObjectMode={() => 'replace'}

                linkCanvasObject={linkCanvasObject}
                linkCanvasObjectMode={() => 'replace'}

                // Minimal library hit-test to avoid conflicts
                nodeRelSize={0.1}
                linkHoverPrecision={0}

                d3VelocityDecay={0.4}
                cooldownTicks={200}
            />

            <div className="absolute bottom-6 left-6 z-20">
                <button
                    onClick={(e) => { e.stopPropagation(); graphRef.current?.zoomToFit(400, 100); }}
                    className="w-10 h-10 bg-white border border-slate-200 rounded-xl shadow-lg flex items-center justify-center text-slate-500 hover:text-blue-600 transition-all active:scale-95"
                >
                    <Maximize size={20} />
                </button>
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
