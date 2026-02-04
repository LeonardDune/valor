import React, { useState, useEffect } from 'react';
import { api } from '@/services/api';
import type { Thread } from '@/types/conversation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Plus, MessageSquare, Hash } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ThreadListProps {
    targetId: string;
    activeThreadId?: string | null;
    onThreadSelect: (thread: Thread) => void;
    className?: string;
}

export const ThreadList: React.FC<ThreadListProps> = ({
    targetId,
    activeThreadId,
    onThreadSelect,
    className
}) => {
    const [threads, setThreads] = useState<Thread[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [newTopic, setNewTopic] = useState('');

    useEffect(() => {
        if (targetId) {
            loadThreads();
        }
    }, [targetId]);

    const loadThreads = async () => {
        try {
            setIsLoading(true);
            const data = await api.getThreads(targetId);
            setThreads(data);
        } catch (error) {
            console.error("Failed to load threads", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newTopic.trim()) return;

        try {
            await api.createThread(targetId, newTopic.trim());
            // The API returns {id, topic, target_id}, but we need Thread compatible object
            // Just cast or map it.
            // Assuming response matches Thread locally or close enough.
            // Wait, api.createThread return type matches backend response.
            // Let's refine types if needed. Backend returns {id, topic, target_id}. Thread needs created_at too?
            // Checking api.ts definition... createThread returns {id, topic, target_id} (Promise object).
            // Thread interface has status, created_at.
            // We might need to refresh or mock the missing fields.
            await loadThreads(); // Simplest way to get full object
            setIsCreating(false);
            setNewTopic('');
        } catch (error) {
            console.error("Failed to create thread", error);
        }
    };

    if (isLoading) {
        return <div className="flex justify-center p-4"><Loader2 className="h-4 w-4 animate-spin text-muted-foreground" /></div>;
    }

    return (
        <div className={cn("flex flex-col h-full bg-muted/10", className)}>
            <div className="flex items-center justify-between p-3 border-b border-border/50">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">
                    Discussies
                </h3>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setIsCreating(!isCreating)}>
                    <Plus className="h-4 w-4" />
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {isCreating && (
                    <form onSubmit={handleCreate} className="p-2 mb-2 bg-card rounded border shadow-sm">
                        <Input
                            autoFocus
                            placeholder="Onderwerp..."
                            value={newTopic}
                            onChange={(e) => setNewTopic(e.target.value)}
                            className="h-7 text-xs mb-2"
                        />
                        <div className="flex justify-end gap-1">
                            <Button size="sm" variant="ghost" onClick={() => setIsCreating(false)} type="button" className="h-6 text-[10px]">Annuleren</Button>
                            <Button size="sm" type="submit" className="h-6 text-[10px]">Maken</Button>
                        </div>
                    </form>
                )}

                {threads.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                        <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-10" />
                        <p className="text-xs">Geen discussies.</p>
                        <Button variant="link" className="text-xs mt-1 h-auto p-0" onClick={() => setIsCreating(true)}>
                            Start de eerste
                        </Button>
                    </div>
                ) : (
                    threads.map(thread => (
                        <button
                            key={thread.id}
                            onClick={() => onThreadSelect(thread)}
                            className={cn(
                                "w-full text-left px-3 py-2.5 rounded-md text-sm flex items-center gap-2.5 transition-all group",
                                activeThreadId === thread.id
                                    ? "bg-primary/10 text-primary font-medium border border-primary/20"
                                    : "hover:bg-muted border border-transparent hover:border-border/50 text-foreground"
                            )}
                        >
                            <Hash className={cn("h-3.5 w-3.5 shrink-0", activeThreadId === thread.id ? "opacity-100" : "opacity-50 group-hover:opacity-80")} />
                            <div className="flex flex-col min-w-0 flex-1">
                                <span className="truncate leading-none mb-1">{thread.topic}</span>
                                <span className="text-[10px] text-muted-foreground truncate opacity-70">
                                    {new Date(thread.created_at).toLocaleDateString()}
                                </span>
                            </div>
                        </button>
                    ))
                )}
            </div>
        </div>
    );
};
