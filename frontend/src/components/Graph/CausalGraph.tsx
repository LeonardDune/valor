import React, { useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { Claim } from '../../services/api';

interface GraphData {
    nodes: { id: string; name: string; val: number }[];
    links: { source: string; target: string; type: string; polarity: string }[];
}

interface CausalGraphProps {
    claims: Claim[];
    onSelect?: (selection: { type: 'node' | 'link'; data: any } | null) => void;
    selectedId?: string | null;
}

const CausalGraph: React.FC<CausalGraphProps> = ({ claims, onSelect, selectedId }) => {
    const graphRef = useRef<any>(null);
    const [data, setData] = useState<GraphData>({ nodes: [], links: [] });
    const [containerDimensions, setContainerDimensions] = useState({ width: 0, height: 0 });
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Transform claims into graph data
        const nodesMap = new Map<string, { id: string; name: string; val: number; nodeId?: string }>();
        const links: any[] = [];

        claims.forEach(claim => {
            if (!nodesMap.has(claim.source_node)) {
                nodesMap.set(claim.source_node, { id: claim.source_node, name: claim.source_node, val: 5 });
            }
            if (!nodesMap.has(claim.target_node)) {
                nodesMap.set(claim.target_node, { id: claim.target_node, name: claim.target_node, val: 5 });
            }

            links.push({
                id: claim.id,
                source: claim.source_node,
                target: claim.target_node,
                type: claim.relationship_type,
                polarity: claim.polarity,
                confidence: claim.confidence,
                statement: claim.statement,
                explanation: claim.statement
            });
        });

        const newData = {
            nodes: Array.from(nodesMap.values()),
            links: links
        };
        setData(newData);

        // Force simulation reheat and zoom to fit (with delay to allow render)
        setTimeout(() => {
            if (graphRef.current) {
                graphRef.current.d3ReheatSimulation();
                graphRef.current.zoomToFit(400, 50, (_: any) => true);
            }
        }, 100);
    }, [claims]);

    useEffect(() => {
        // Resize observer
        const updateDimensions = () => {
            if (containerRef.current) {
                setContainerDimensions({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight
                });
            }
        };

        window.addEventListener('resize', updateDimensions);
        updateDimensions();

        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    const handleNodeClick = (node: any) => {
        if (onSelect) onSelect({ type: 'node', data: node });
    };

    const handleLinkClick = (link: any) => {
        if (onSelect) onSelect({ type: 'link', data: link });
    };

    const handleBackgroundClick = () => {
        if (onSelect) onSelect(null);
    };

    return (

        <div ref={containerRef} className="w-full h-full bg-slate-50 border rounded-xl overflow-hidden shadow-inner relative">
            <ForceGraph2D
                ref={graphRef}
                width={containerDimensions.width}
                height={containerDimensions.height}
                graphData={data}
                nodeRelSize={6}
                nodeColor={(node: any) => node.id === selectedId ? '#2563eb' : '#eff6ff'}
                nodeLabel="name"
                linkLabel={(link: any) => `<div style="padding: 4px; color: #fff; border-radius: 4px; background: rgba(0,0,0,0.8); max-width: 200px; font-size: 12px;"><strong>Argumentatie:</strong><br/>${link.explanation || 'Geen toelichting'}</div>`}

                onNodeClick={handleNodeClick}
                onLinkClick={handleLinkClick}
                onBackgroundClick={handleBackgroundClick}

                // Custom Node Rendering to show labels
                nodeCanvasObject={(node: any, ctx, globalScale) => {
                    const label = node.name;
                    const fontSize = 12 / globalScale;
                    const isSelected = node.id === selectedId;

                    ctx.font = `${fontSize}px Sans-Serif`;

                    // Text wrapping
                    const words = label.split(' ');
                    const lines: string[] = [];
                    let currentLine = words[0];
                    const maxLineWidth = fontSize * 10;

                    for (let i = 1; i < words.length; i++) {
                        const word = words[i];
                        const width = ctx.measureText(currentLine + " " + word).width;
                        if (width < maxLineWidth) {
                            currentLine += " " + word;
                        } else {
                            lines.push(currentLine);
                            currentLine = word;
                        }
                    }
                    lines.push(currentLine);

                    // Calculate Box Dimensions
                    const lineHeight = fontSize * 1.2;
                    const totalHeight = lines.length * lineHeight;
                    const maxWidth = Math.max(...lines.map(l => ctx.measureText(l).width));
                    const boxWidth = maxWidth + fontSize * 0.8;
                    const boxHeight = totalHeight + fontSize * 0.4;

                    // Draw Node Highlight if selected
                    if (isSelected) {
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false);
                        ctx.strokeStyle = '#2563eb';
                        ctx.lineWidth = 2 / globalScale;
                        ctx.stroke();
                    }

                    // Draw Node Circle
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
                    ctx.fillStyle = isSelected ? '#2563eb' : '#3b82f6';
                    ctx.fill();

                    // Draw Label Background
                    ctx.fillStyle = isSelected ? 'rgba(37, 99, 235, 0.1)' : 'rgba(255, 255, 255, 0.85)';
                    ctx.fillRect(
                        node.x - boxWidth / 2,
                        node.y - boxHeight / 2,
                        boxWidth,
                        boxHeight
                    );

                    if (isSelected) {
                        ctx.strokeStyle = '#2563eb';
                        ctx.lineWidth = 1 / globalScale;
                        ctx.strokeRect(node.x - boxWidth / 2, node.y - boxHeight / 2, boxWidth, boxHeight);
                    }

                    // Draw Text
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = isSelected ? '#1d4ed8' : '#1e293b';

                    lines.forEach((line, i) => {
                        const yOffset = (i - (lines.length - 1) / 2) * lineHeight;
                        ctx.fillText(line, node.x, node.y + yOffset);
                    });
                }}
                nodeCanvasObjectMode={() => 'replace'}

                // Link Styling
                linkColor={(link: any) => {
                    if (link.id === selectedId) return '#2563eb';
                    return link.polarity === '+' ? '#10b981' : '#ef4444';
                }}
                linkWidth={(link: any) => link.id === selectedId ? 4 : 2}
                linkDirectionalArrowLength={3.5}
                linkDirectionalArrowRelPos={1}
                linkCurvature={(link: any) => {
                    const links = data.links;
                    const source = typeof link.source === 'object' ? link.source.id : link.source;
                    const target = typeof link.target === 'object' ? link.target.id : link.target;
                    const siblings = links.filter((l: any) => {
                        const s = typeof l.source === 'object' ? l.source.id : l.source;
                        const t = typeof l.target === 'object' ? l.target.id : l.target;
                        return (s === source && t === target) || (s === target && t === source);
                    });
                    const numSiblings = siblings.length;
                    if (numSiblings <= 1) return 0;
                    const index = siblings.indexOf(link);
                    const step = 0.2;
                    return (index - (numSiblings - 1) / 2) * step;
                }}
                d3VelocityDecay={0.3}
                cooldownTicks={100}
                linkHoverPrecision={10}
                onEngineStop={() => {
                    // Zoom to fit only when engine stops to avoid jumpiness, 
                    // and limit the max zoom to prevent giant nodes
                    if (graphRef.current) {
                        graphRef.current.zoomToFit(400, 50, (_: any) => true);
                    }
                }}
            />

            {/* Legend Overlay */}
            <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur p-3 rounded-lg border border-slate-200 shadow-sm text-xs space-y-2">
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                    <span className="text-slate-600">Factor</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-8 h-0.5 bg-green-500"></span>
                    <span className="text-slate-600">Positieve Oorzaak (+)</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-8 h-0.5 bg-red-500"></span>
                    <span className="text-slate-600">Negatieve Oorzaak (-)</span>
                </div>
            </div>

            {claims.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <p className="text-slate-400 italic">Nog geen causaal model. Begin het gesprek!</p>
                </div>
            )}
        </div>
    );

};

export default CausalGraph;
