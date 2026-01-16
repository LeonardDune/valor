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
            className="w-full h-full border-2 border-dashed border-slate-300 rounded-lg relative pointer-events-none"
            style={{
                ...style, // Merge ReactFlow dimensions
                backgroundColor: 'rgba(241, 245, 249, 0.3)' // Subtle fill
            }}
        >
            <div className="absolute -top-3 left-4 bg-slate-50 px-2 text-[10px] font-bold text-slate-400 tracking-wider">
                SCOPE / SYSTEEMGRENS
            </div>
        </div>
    );
});
