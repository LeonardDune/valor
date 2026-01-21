import React from 'react';
import type { ReactNode } from 'react';
import { AgentPanelRegion } from '@/components/shell/AgentPanelRegion';
import { cn } from '@/lib/utils';

interface PerspectiveShellProps {
    children: ReactNode; // The ViewArea content
    className?: string;
}

export const PerspectiveShell: React.FC<PerspectiveShellProps> = ({ children, className }) => {
    return (
        <div className={cn("flex w-full h-full bg-background-primary", className)}>
            {/* Main View Area */}
            <main className="flex-1 relative overflow-hidden flex flex-col">
                {/* Toolbar could go here */}
                <div className="flex-1 relative">
                    {children}
                </div>
            </main>

            {/* Agent Sidebar Region */}
            {/* Fixed width for now, could be resizable */}
            <aside className="w-80 h-full flex-shrink-0 z-10 shadow-xl">
                <AgentPanelRegion />
            </aside>
        </div>
    );
};
