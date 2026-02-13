import React from 'react';
import { LayoutDashboard, MessageSquareText, Network, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
    ToggleGroup,
    ToggleGroupItem,
} from "@/components/ui/toggle-group";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

export type LayoutMode = 'free' | 'system';

interface PerspectiveToolbarProps {
    /**
     * Additional tools specific to the perspective
     */
    children?: React.ReactNode;

    /**
     * Current layout mode (if supported)
     */
    layoutMode?: LayoutMode;

    /**
     * Handler for layout changes
     */
    onLayoutChange?: (mode: LayoutMode) => void;


    /**
     * Optional export actions component (e.g. <ExportMenu />)
     */
    exportActions?: React.ReactNode;

    /**
     * Handler to resume/open deliberation
     */
    onResumeDeliberation?: () => void;

    /**
     * Handler to open the moderator dashboard
     */
    onOpenModeratorDashboard?: () => void;

    /**
     * Whether the current user is a moderator
     */
    isModerator?: boolean;

    className?: string;
}

export const PerspectiveToolbar: React.FC<PerspectiveToolbarProps> = ({
    children,
    layoutMode = 'free',
    onLayoutChange,
    exportActions,
    onResumeDeliberation,
    onOpenModeratorDashboard,
    isModerator,
    className
}) => {
    return (
        <div className={cn(
            "absolute top-4 right-4 z-10 flex items-center gap-2 no-export",
            "p-1.5 rounded-lg bg-background/80 backdrop-blur-md border shadow-sm",
            className
        )}>
            {/* Custom Perspective Tools */}
            {children && (
                <>
                    <div className="flex items-center gap-1">
                        {children}
                    </div>
                    <div className="w-px h-6 bg-border mx-1" />
                </>
            )}

            {/* Layout Switcher */}
            {onLayoutChange && (
                <>
                    <ToggleGroup
                        type="single"
                        value={layoutMode}
                        onValueChange={(value) => value && onLayoutChange(value as LayoutMode)}
                        className="gap-1"
                    >
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <ToggleGroupItem value="free" size="sm" aria-label="Vrije Layout">
                                        <Network className="h-4 w-4" />
                                    </ToggleGroupItem>
                                </TooltipTrigger>
                                <TooltipContent>Vrije Layout</TooltipContent>
                            </Tooltip>
                        </TooltipProvider>

                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <ToggleGroupItem value="system" size="sm" aria-label="Systeem Layout">
                                        <LayoutDashboard className="h-4 w-4" />
                                    </ToggleGroupItem>
                                </TooltipTrigger>
                                <TooltipContent>Systeem Layout</TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </ToggleGroup>
                    <div className="w-px h-6 bg-border mx-1" />
                </>
            )}

            {/* Export Actions */}
            {exportActions && (
                <>
                    {exportActions}
                    <div className="w-px h-6 bg-border mx-1" />
                </>
            )}

            {/* Deliberation Resume */}
            {onResumeDeliberation && (
                <>
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={onResumeDeliberation}
                                    className="h-8 gap-2 px-3 text-orange-600 bg-orange-600/5 hover:bg-orange-600/10 border border-orange-600/20"
                                >
                                    <MessageSquareText className="h-4 w-4" />
                                    <span className="text-xs font-semibold">Stemsessie</span>
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>Terug naar Deliberatie</TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                    <div className="w-px h-6 bg-border mx-1" />
                </>
            )}

            {/* Moderator Dashboard */}
            {isModerator && onOpenModeratorDashboard && (
                <>
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={onOpenModeratorDashboard}
                                    className="h-8 w-8 text-primary hover:text-primary hover:bg-primary/10"
                                >
                                    <Shield className="h-4 w-4" />
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>Moderatie Overzicht</TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                    <div className="w-px h-6 bg-border mx-1" />
                </>
            )}

        </div>
    );
};
