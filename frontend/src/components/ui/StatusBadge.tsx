import React from 'react';
import { SemanticIndicator } from '@/design-system/primitives/SemanticIndicator';
import type { IndicatorStatus } from '@/design-system/primitives/SemanticIndicator';
import { cn } from '@/lib/utils'; // Adjust path if needed

export type LifecycleStatus = 'draft' | 'proposed' | 'accepted' | 'rejected' | 'deprecated';

interface StatusBadgeProps {
    status: LifecycleStatus;
    className?: string;
    showLabel?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className, showLabel = true }) => {

    const mapStatusToIndicator = (s: LifecycleStatus): IndicatorStatus => {
        switch (s) {
            case 'draft': return 'neutral';
            case 'proposed': return 'warning'; // Needs attention
            case 'accepted': return 'valid'; // Good
            case 'rejected': return 'error'; // Bad
            case 'deprecated': return 'negative';
            default: return 'neutral';
        }
    };

    const labelMap: Record<LifecycleStatus, string> = {
        draft: 'Draft',
        proposed: 'Proposed',
        accepted: 'Accepted',
        rejected: 'Rejected',
        deprecated: 'Deprecated'
    };

    return (
        <SemanticIndicator
            status={mapStatusToIndicator(status)}
            label={showLabel ? labelMap[status] : undefined}
            className={cn("px-2 py-1 bg-white/5 rounded-full border border-white/10", className)}
        />
    );
};
