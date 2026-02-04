
import React from 'react';
import { type EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';
import { PlusCircle, MinusCircle, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

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

    return (
        <>
            <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={style} />
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
