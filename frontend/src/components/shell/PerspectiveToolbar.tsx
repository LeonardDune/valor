import React from 'react';
import { LayoutDashboard, MessageSquareText, Network } from 'lucide-react';
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
     * Handler to open the Global/View conversation context
     */
    onOpenGlobalConversation?: () => void;

    /**
     * Optional export actions component (e.g. <ExportMenu />)
     */
    exportActions?: React.ReactNode;

    className?: string;
}

export const PerspectiveToolbar: React.FC<PerspectiveToolbarProps> = ({
    children,
    layoutMode = 'free',
    onLayoutChange,
    onOpenGlobalConversation,
    exportActions,
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

            {/* Global Actions */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={onOpenGlobalConversation}
                            className="h-8 w-8"
                        >
                            <MessageSquareText className="h-4 w-4 text-purple-500" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>Start Perspectief Chat</TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
    );
};
