import { memo } from 'react';

/**
 * SystemScopeNode
 * 
 * Visual representation of the "System Boundary" for the System Layout.
 * It renders a dashed box with a label "SCOPE / SYSTEEMGRENS".
 * 
 * It is purely visual and should be placed behind other nodes (zIndex: -1).
 */
export const SystemScopeNode = memo(({ style }: { style?: React.CSSProperties, data?: any }) => {
    // Width and height are passed via style from ReactFlow (set in CLDView)

    return (
        <div
            className="w-full h-full border-2 border-dashed border-border-standard rounded-overlay relative pointer-events-none"
            style={{
                ...style, // Merge ReactFlow dimensions
                backgroundColor: 'var(--color-slate-100)', // Subtle fill for scope
                opacity: 0.5
            }}
        >
            <div className="absolute -top-3 left-4 bg-canvas px-2 text-[10px] font-bold text-text-muted tracking-wider">
                SCOPE / SYSTEEMGRENS
            </div>
        </div>
    );
});
