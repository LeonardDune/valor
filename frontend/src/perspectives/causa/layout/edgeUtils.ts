export const getGeometricHandles = (sourcePos: { x: number, y: number }, targetPos: { x: number, y: number }) => {
    const dx = targetPos.x - sourcePos.x;
    const dy = targetPos.y - sourcePos.y;

    let sourceHandle = 'source-right';
    let targetHandle = 'target-left';

    // Use 1.2 factor to bias slightly towards horizontal connections 
    // unless clearly vertical (matching CLDView.tsx)
    if (Math.abs(dy) > Math.abs(dx) * 1.2) {
        // Primarily vertical
        if (dy > 0) { // Target is below
            sourceHandle = 'source-bottom';
            targetHandle = 'target-top';
        } else { // Target is above
            sourceHandle = 'source-top';
            targetHandle = 'target-bottom';
        }
    } else {
        // Primarily horizontal
        if (dx > 0) { // Target is right
            sourceHandle = 'source-right';
            targetHandle = 'target-left';
        } else { // Target is left
            sourceHandle = 'source-left';
            targetHandle = 'target-right';
        }
    }

    return { sourceHandle, targetHandle };
};
