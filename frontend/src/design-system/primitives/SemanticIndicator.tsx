import React from 'react';
import { cn } from '../../lib/utils';

export type IndicatorStatus = 'valid' | 'warning' | 'error' | 'positive' | 'negative' | 'neutral';

interface SemanticIndicatorProps {
    status: IndicatorStatus;
    size?: 'sm' | 'md' | 'lg';
    label?: string; // Optional label to show next to indicator
    className?: string;
}

export const SemanticIndicator: React.FC<SemanticIndicatorProps> = ({
    status,
    size = 'md',
    label,
    className
}) => {

    const colorMap: Record<IndicatorStatus, string> = {
        valid: 'bg-status-valid',
        warning: 'bg-status-warning',
        error: 'bg-status-error',
        positive: 'bg-causal-positive',
        negative: 'bg-causal-negative',
        neutral: 'bg-causal-neutral',
    };

    const sizeMap = {
        sm: 'w-2 h-2',
        md: 'w-3 h-3',
        lg: 'w-4 h-4'
    };

    return (
        <div className={cn("inline-flex items-center gap-2", className)}>
            <span
                className={cn(
                    "rounded-full inline-block",
                    colorMap[status],
                    sizeMap[size]
                )}
            />
            {label && <span className="text-sm text-text-secondary">{label}</span>}
        </div>
    );
};
