import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { MessageSquareText, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export interface ContextObject {
    id: string;
    type: string;
    label?: string;
    [key: string]: any;
}

export interface ContextAction {
    id: string;
    label: string;
    icon?: React.ReactNode;
    onClick: (object: ContextObject) => void;
    variant?: 'default' | 'destructive' | 'ghost';
}

interface CanvasContextMenuProps {
    /**
     * Screen/Canvas coordinates for the menu
     */
    position: { x: number; y: number };

    /**
     * The object the menu is active for
     */
    contextObject: ContextObject;

    /**
     * Handler to dismiss the menu
     */
    onDismiss: () => void;

    /**
     * Handler to open the Object-Bound conversation context
     */
    onOpenObjectConversation: (object: ContextObject) => void;

    /**
     * Handler to edit the object
     */
    onEdit?: (object: ContextObject) => void;

    /**
     * Additional actions to show in the menu
     */
    additionalActions?: ContextAction[];

    className?: string;
}

export const CanvasContextMenu: React.FC<CanvasContextMenuProps> = ({
    position,
    contextObject,
    onDismiss,
    onOpenObjectConversation,
    onEdit,
    additionalActions = [],
    className
}) => {
    const menuRef = useRef<HTMLDivElement>(null);

    // Handle click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                onDismiss();
            }
        };

        // Use mousedown to capture the start of the click, preventing potential conflicts
        document.addEventListener('mousedown', handleClickOutside);
        // Determine scroll/pan interactions on canvas? 
        // Usually clicking on canvas background is handled by the canvas itself, 
        // but the global listener helps if the click is on UI overlays.

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [onDismiss]);

    // Adjust position to fetch viewport boundaries if needed (simple implementation for now)
    const style = {
        top: position.y,
        left: position.x,
    };

    return createPortal(
        <div
            ref={menuRef}
            style={style}
            className={cn(
                "fixed z-50 min-w-[200px] flex flex-col gap-1",
                "p-1.5 rounded-lg bg-background/95 backdrop-blur-md border shadow-lg animate-in fade-in zoom-in-95 duration-100",
                className
            )}
        >
            {/* Header */}
            <div className="px-2 py-1.5 border-b mb-1 flex justify-between items-center">
                <span className="text-xs font-medium text-muted-foreground truncate max-w-[140px]">
                    {contextObject.label || contextObject.type}
                </span>
                <button
                    onClick={onDismiss}
                    className="text-muted-foreground hover:text-foreground"
                    aria-label="Close menu"
                >
                    <X className="h-3 w-3" />
                </button>
            </div>

            {/* Edit Action */}
            {onEdit && (
                <Button
                    variant="ghost"
                    size="sm"
                    className="justify-start gap-2 h-8 px-2 w-full"
                    onClick={() => {
                        onEdit(contextObject);
                        onDismiss();
                    }}
                >
                    <span className="h-4 w-4 flex items-center justify-center">✎</span>
                    <span>Bewerken</span>
                </Button>
            )}

            {/* Primary Action: Conversation */}
            <Button
                variant="ghost"
                size="sm"
                className="justify-start gap-2 h-8 px-2 w-full text-purple-600 hover:text-purple-700 hover:bg-purple-50 dark:hover:bg-purple-900/20"
                onClick={() => {
                    onOpenObjectConversation(contextObject);
                    onDismiss();
                }}
            >
                <MessageSquareText className="h-4 w-4" />
                <span>Open Conversation</span>
            </Button>

            {/* Additional Actions */}
            {additionalActions.map((action) => (
                <Button
                    key={action.id}
                    variant="ghost"
                    size="sm"
                    className={cn(
                        "justify-start gap-2 h-8 px-2 w-full",
                        action.variant === 'destructive' && "text-red-500 hover:text-red-600 hover:bg-red-50"
                    )}
                    onClick={() => {
                        action.onClick(contextObject);
                        onDismiss();
                    }}
                >
                    {action.icon}
                    <span>{action.label}</span>
                </Button>
            ))}
        </div>,
        document.body // Rendering in portal to avoid z-index/overflow issues within canvas containers
    );
};
