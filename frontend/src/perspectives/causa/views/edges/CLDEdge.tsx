
import React from 'react';
import { type EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';
import { PlusCircle, MinusCircle, MessageSquare, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { EpistemicStatus } from '../../types';

const epistemicStrokeColor: Record<EpistemicStatus, string> = {
    Proposed:     '#94a3b8', // slate-400
    Contested:    '#fb923c', // orange-400
    Accepted:     '#22c55e', // green-500
    Rejected:     '#ef4444', // red-500
    Reconsidered: '#a855f7', // purple-500
};

const CLDEdge = ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data,
}: EdgeProps) => {
    const [edgePath, labelX, labelY] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });

    const polarity = data?.polarity || '+';
    const isPositive = polarity === '+' || polarity === 'positive';
    const Icon = isPositive ? PlusCircle : MinusCircle;
    // Use global CSS variable for causal colors
    const color = isPositive ? 'var(--color-causal-positive)' : 'var(--color-causal-negative)';

    const epistemicStatus = (data?.epistemicStatus || 'Proposed') as EpistemicStatus;
    const strokeColor = epistemicStrokeColor[epistemicStatus] || epistemicStrokeColor.Proposed;
    const strokeOpacity = epistemicStatus === 'Rejected' ? 0.4 : 1;

    return (
        <>
            <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={{ ...style, stroke: strokeColor, strokeOpacity }} />
            <EdgeLabelRenderer>
                <div
                    style={{
                        position: 'absolute',
                        transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
                        fontSize: 12,
                        pointerEvents: 'all',
                        zIndex: 10,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                    }}
                    className="nodrag nopan"
                >
                    {/* Polarity Icon */}
                    <div className="bg-white rounded-full p-[2px] shadow-sm ring-1 ring-slate-200">
                        <Icon
                            size={16}
                            color={color}
                            fill="white"
                            strokeWidth={2}
                        />
                    </div>

                    {/* Evidence Indicator */}
                    {(data?.evidence_text || data?.evidence_url) && (
                        <div
                            className="bg-white rounded-full p-[3px] shadow-sm ring-1 ring-amber-200 text-amber-500 flex items-center justify-center pointer-events-none"
                            title="Bevat bewijs of context"
                        >
                            <FileText size={12} strokeWidth={2.5} />
                        </div>
                    )}

                    {/* Thread Indicator */}
                    {(data?.threadCount !== undefined) && (
                        <div
                            className={cn(
                                "flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium transition-all cursor-pointer border shadow-sm",
                                (data.threadCount > 0)
                                    ? "text-primary bg-white border-primary/20"
                                    : "text-muted-foreground bg-white/80 opacity-0 group-hover:opacity-100 border-slate-200"
                            )}
                            onClick={(e) => {
                                e.stopPropagation();
                                console.log("CLDEdge: Badge clicked. version_id:", data.version_id, "id:", id);
                                data.onOpenThread?.(data.version_id || id, data.statement || 'Relatie', { x: e.clientX, y: e.clientY });
                            }}
                        >
                            <MessageSquare className="w-3 h-3" />
                            {data.threadCount > 0 && <span>{data.threadCount}</span>}
                        </div>
                    )}
                </div>
            </EdgeLabelRenderer>
        </>
    );
};

export default React.memo(CLDEdge);
