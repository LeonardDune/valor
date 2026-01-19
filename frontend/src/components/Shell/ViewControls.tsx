
import React from 'react';
import { useReactFlow } from 'reactflow';
import { Button } from '@/components/ui/button';
import { ZoomIn, ZoomOut, Maximize } from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from '@/lib/utils';

interface ViewControlsProps {
    className?: string;
}

export const ViewControls: React.FC<ViewControlsProps> = ({ className }) => {
    const { zoomIn, zoomOut, fitView } = useReactFlow();

    // Standard styling for control buttons
    const ControlButton = ({ onClick, icon: Icon, label }: { onClick: () => void, icon: any, label: string }) => (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onClick}
                        className="h-8 w-8 bg-background/80 backdrop-blur-sm border shadow-sm hover:bg-accent"
                    >
                        <Icon className="h-4 w-4" />
                    </Button>
                </TooltipTrigger>
                <TooltipContent side="right">
                    {label}
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );

    return (
        <div className={cn("absolute bottom-4 left-4 z-10 flex flex-col gap-1", className)}>
            <ControlButton onClick={() => zoomIn()} icon={ZoomIn} label="Inzoomen" />
            <ControlButton onClick={() => zoomOut()} icon={ZoomOut} label="Uitzoomen" />
            <ControlButton onClick={() => fitView()} icon={Maximize} label="Passend maken" />
        </div>
    );
};
