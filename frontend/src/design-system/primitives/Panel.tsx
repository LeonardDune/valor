import React from 'react';
import { cn } from '../../lib/utils'; // Assuming cn exists or clsx/tailwind-merge is used



interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'translucent' | 'plain';
    padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Panel: React.FC<PanelProps> = ({
    children,
    className,
    variant = 'default',
    padding = 'md',
    ...props
}) => {
    const baseStyles = 'rounded-panel transition-all';

    const variants = {
        default: 'bg-panel border border-border-standard shadow-sm',
        translucent: 'bg-panel-translucent backdrop-blur-sm border border-border-standard shadow-sm',
        plain: 'bg-transparent' // useful for just grouping without visual box
    };

    const paddings = {
        none: '',
        sm: 'p-2',
        md: 'p-4',
        lg: 'p-6'
    };

    return (
        <div
            className={cn(baseStyles, variants[variant], paddings[padding], className)}
            {...props}
        >
            {children}
        </div>
    );
};
