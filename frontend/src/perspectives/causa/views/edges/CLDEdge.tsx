import type { FunctionComponent } from 'react';
import { BaseEdge, EdgeLabelRenderer, type EdgeProps, getBezierPath } from 'reactflow';

const CLDEdge: FunctionComponent<EdgeProps> = ({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data
}) => {
    const [edgePath, labelX, labelY] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });

    const polarity = data?.polarity; // '+' or '-'
    const status = data?.status || 'validated';
    const certainty = data?.certainty ?? 1.0;

    // Visual Mapping
    const isProposed = status === 'proposed';
    const opacity = 0.3 + (certainty * 0.7); // Min 0.3 opacity

    return (
        <>
            <BaseEdge
                path={edgePath}
                markerEnd={markerEnd}
                style={{
                    ...style,
                    opacity,
                    strokeDasharray: isProposed ? '5,5' : undefined,
                }}
            />
            {polarity && (
                <EdgeLabelRenderer>
                    <div
                        style={{
                            position: 'absolute',
                            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                            background: '#fff',
                            padding: '2px 4px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            border: '1px solid #ccc',
                            pointerEvents: 'all',
                        }}
                        className="nodrag nopan"
                    >
                        {polarity}
                    </div>
                </EdgeLabelRenderer>
            )}
        </>
    );
};

export default CLDEdge;
