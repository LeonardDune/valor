import { memo } from 'react';

export const SystemScopeNode = memo(({ data }: { data: { width: number; height: number } }) => {
    return (
        <div style={{
            width: data.width,
            height: data.height,
            position: 'relative',
            pointerEvents: 'none',
            boxSizing: 'border-box',
            margin: 0,
        }}>
            {/* SVG Overlay for perfect center-aligned border */}
            <svg
                width="100%"
                height="100%"
                style={{ overflow: 'visible', position: 'absolute', top: 0, left: 0 }}
            >
                <rect
                    x={0}
                    y={0}
                    width={data.width}
                    height={data.height}
                    fill="none"
                    stroke="#94a3b8"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                    vectorEffect="non-scaling-stroke"
                />
            </svg>

            <div style={{
                position: 'absolute',
                top: -24,
                left: 0,
                color: '#94a3b8',
                fontSize: 12,
                fontWeight: 600,
                fontFamily: 'Inter, sans-serif'
            }}>
                SCOPE / SYSTEEMGRENS
            </div>
        </div>
    );
});
