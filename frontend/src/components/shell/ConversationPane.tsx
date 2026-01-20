import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import type { ConversationContext } from '@/types/conversation';
import ChatInterface from '@/components/Chat/ChatInterface';
import type { Claim } from '@/services/api';

interface ConversationPaneProps {
    isOpen: boolean;
    onClose: () => void;
    context: ConversationContext | null; // The context determining WHAT to show
    topic: string; // Global topic (Theme Name) for fallback
    onClaimsUpdate: (claims: Claim[]) => void;
    className?: string;
}

/**
 * Standardized Conversation Pane (Template).
 * Acts as a container for conversation views (e.g. ChatInterface).
 */
export const ConversationPane: React.FC<ConversationPaneProps> = ({
    isOpen,
    onClose,
    context,
    topic,
    onClaimsUpdate,
    className
}) => {
    // If not open or no context, we render nothing (or null)
    if (!isOpen) return null;

    // Derived State
    const title = context?.label || 'AI Agent';
    const subTitle = context ? `${context.perspective} • ${context.scope} Context` : 'Global Context';

    const chatTopic = (context?.scope === 'object' && context.label)
        ? `${topic} - ${context.label}`
        : topic;

    return (
        <div className={cn(
            "fixed top-16 right-4 z-40 w-[450px] h-[calc(100vh-5rem)]",
            "bg-background border rounded-lg shadow-2xl flex flex-col",
            "animate-in slide-in-from-right duration-200",
            className
        )}>
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b shrink-0 bg-muted/20">
                <div>
                    <h3 className="font-semibold text-sm">{title}</h3>
                    <p className="text-xs text-muted-foreground capitalize">{subTitle}</p>
                </div>
                <Button variant="ghost" size="icon" onClick={onClose} className="h-6 w-6">
                    <X className="h-4 w-4" />
                </Button>
            </div>

            {/* Content Area - Router Switch would go here later */}
            <div className="flex-1 overflow-hidden relative">
                <ChatInterface
                    topic={chatTopic}
                    onClaimsUpdate={onClaimsUpdate}
                />
            </div>
        </div>
    );
};
