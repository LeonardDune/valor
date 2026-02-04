import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { X, ChevronLeft } from 'lucide-react';
import type { ConversationContext, Thread } from '@/types/conversation';
import ChatInterface from '@/components/Chat/ChatInterface';
import { ThreadList } from '@/components/Chat/ThreadList';
import type { Claim } from '@/services/api';

interface ConversationPaneProps {
    isOpen: boolean;
    onClose: () => void;
    context: ConversationContext | null;
    topicId?: string;
    topicLabel: string;
    onClaimsUpdate: (claims: Claim[]) => void;
    className?: string;
    isReadOnly?: boolean;
}

export const ConversationPane: React.FC<ConversationPaneProps> = ({
    isOpen,
    onClose,
    context,
    topicId,
    topicLabel,
    onClaimsUpdate,
    className,
    isReadOnly = false
}) => {
    const [activeThreadId, setActiveThreadId] = useState<string | undefined>(topicId);
    const [activeThreadLabel, setActiveThreadLabel] = useState<string>(topicLabel);

    // Sync props to state if they change externally (e.g. opening different node)
    useEffect(() => {
        if (topicId) {
            setActiveThreadId(topicId);
            setActiveThreadLabel(topicLabel);
        } else {
            // If opening a context without a specific thread, start in list mode
            setActiveThreadId(undefined);
            setActiveThreadLabel(topicLabel);
        }
    }, [topicId, topicLabel, context?.contextId, isOpen]);

    if (!isOpen) return null;

    const title = context?.label || 'Discussie';
    const subTitle = context ? `${context.perspective} • ${context.scope} Context` : 'Global Context';

    const handleBackToList = () => {
        setActiveThreadId(undefined);
    };

    const handleThreadSelect = (thread: Thread) => {
        setActiveThreadId(thread.id);
        setActiveThreadLabel(thread.topic);
    };

    const showChat = !!activeThreadId;
    const showList = !showChat && !!context?.contextId;

    return (
        <div className={cn(
            "fixed top-16 right-4 z-40 w-[450px] h-[calc(100vh-5rem)]",
            "bg-background border rounded-lg shadow-2xl flex flex-col",
            "animate-in slide-in-from-right duration-200",
            className
        )}>
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b shrink-0 bg-muted/20">
                <div className="flex items-center gap-2">
                    {showChat && showList && ( // Only show back button if we can go back to list (i.e. context exists)
                        // logic error: showChat is true, showList is false. We check contextId directly.
                        !!context?.contextId && (
                            <Button variant="ghost" size="icon" onClick={handleBackToList} className="h-6 w-6 mr-1">
                                <ChevronLeft className="h-4 w-4" />
                            </Button>
                        )
                    )}
                    <div>
                        <h3 className="font-semibold text-sm truncate max-w-[250px]">
                            {showChat ? activeThreadLabel : "Conversaties"}
                        </h3>
                        <p className="text-xs text-muted-foreground capitalize truncate max-w-[300px]">
                            {showChat ? subTitle : title}
                        </p>
                    </div>
                </div>
                <Button variant="ghost" size="icon" onClick={onClose} className="h-6 w-6">
                    <X className="h-4 w-4" />
                </Button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden relative flex flex-col">
                {showList ? (
                    <ThreadList
                        targetId={context!.contextId!}
                        onThreadSelect={handleThreadSelect}
                        activeThreadId={undefined}
                    />
                ) : activeThreadId ? (
                    <ChatInterface
                        topicLabel={activeThreadLabel}
                        topicId={activeThreadId}
                        initialConversationId={activeThreadId}
                        onClaimsUpdate={onClaimsUpdate}
                        isReadOnly={isReadOnly}
                    />
                ) : (
                    <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
                        Selecteer een context om conversaties te zien.
                    </div>
                )}
            </div>
        </div>
    );
};
