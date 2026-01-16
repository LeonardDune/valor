
import React from 'react';
import { type EdgeProps, getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';
import { PlusCircle, MinusCircle } from 'lucide-react';

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
    const color = isPositive ? '#10b981' : '#ef4444';

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
                    }}
                    className="nodrag nopan"
                >
                    <div className="bg-white rounded-full p-[2px] shadow-sm ring-1 ring-slate-200">
                        <Icon
                            size={16}
                            color={color}
                            fill="white"
                            strokeWidth={2}
                        />
                    </div>
                </div>
            </EdgeLabelRenderer>
        </>
    );
};

export default React.memo(CLDEdge);
