import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api, type ConversationThread } from '../services/api';
import ChatInterface from '../components/Chat/ChatInterface'; // Correct relative path from pages/
import { Plus, MessageSquare, Hash, Loader2 } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";

export const VersionChat: React.FC = () => {
    // Check for versionId first, then spaceId fallback
    const params = useParams();
    const versionId = params.versionId || params.spaceId;

    const [threads, setThreads] = useState<ConversationThread[]>([]);
    const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [newThreadTopic, setNewThreadTopic] = useState('');

    useEffect(() => {
        if (versionId) {
            loadThreads();
        }
    }, [versionId]);

    const loadThreads = async () => {
        if (!versionId) return;
        try {
            setIsLoading(true);
            const data = await api.getVersionThreads(versionId);
            setThreads(data);
            if (data.length > 0 && !activeThreadId) {
                // Auto-select first thread? Or wait for user?
                // Auto-selecting is usually friendly.
                // setActiveThreadId(data[0].id);
            }
        } catch (err) {
            console.error("Failed to load threads", err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateThread = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newThreadTopic.trim() || !versionId) return;

        try {
            const newThread = await api.createThread(versionId, newThreadTopic);
            setThreads(prev => [newThread, ...prev]);
            setActiveThreadId(newThread.id);
            setIsCreating(false);
            setNewThreadTopic('');
        } catch (err) {
            console.error("Failed to create thread", err);
        }
    };

    const activeThread = threads.find(t => t.id === activeThreadId);

    return (
        <div className="flex h-full w-full overflow-hidden">
            {/* Thread List Sidebar */}
            <div className="w-64 bg-background border-r border-border flex flex-col">
                <div className="p-4 border-b border-border flex justify-between items-center">
                    <h2 className="font-semibold text-sm">Gesprekken</h2>
                    <Button variant="ghost" size="icon" onClick={() => setIsCreating(!isCreating)}>
                        <Plus className="h-4 w-4" />
                    </Button>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {/* New Thread Input */}
                    {isCreating && (
                        <form onSubmit={handleCreateThread} className="p-2 mb-2 bg-muted/30 rounded-lg border border-border">
                            <Input
                                autoFocus
                                placeholder="Onderwerp..."
                                value={newThreadTopic}
                                onChange={e => setNewThreadTopic(e.target.value)}
                                className="h-8 text-sm mb-2"
                            />
                            <div className="flex justify-end gap-1">
                                <Button size="sm" variant="ghost" onClick={() => setIsCreating(false)} type="button" className="h-7 text-xs">Annuleren</Button>
                                <Button size="sm" type="submit" className="h-7 text-xs">Maken</Button>
                            </div>
                        </form>
                    )}

                    {isLoading ? (
                        <div className="flex justify-center p-4">
                            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                        </div>
                    ) : threads.length === 0 ? (
                        <div className="text-center p-4 text-xs text-muted-foreground">
                            Geen gesprekken. Start er een!
                        </div>
                    ) : (
                        threads.map(thread => (
                            <button
                                key={thread.id}
                                onClick={() => setActiveThreadId(thread.id)}
                                className={cn(
                                    "w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 transition-colors",
                                    activeThreadId === thread.id
                                        ? "bg-primary/10 text-primary font-medium"
                                        : "hover:bg-muted text-foreground"
                                )}
                            >
                                <Hash className="h-3.5 w-3.5 opacity-70" />
                                <span className="truncate">{thread.topic}</span>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col bg-muted/5">
                {activeThread ? (
                    <div className="flex-1 overflow-hidden">
                        {/* 
                          We reuse ChatInterface. 
                          It handles claims/initialization.
                          We pass initialConversationId.
                        */}
                        <ChatInterface
                            topicLabel={activeThread.topic}
                            topicId={activeThread.id}
                            initialConversationId={activeThread.id}
                            onClaimsUpdate={(claims) => {
                                console.log("Claims updated from thread", activeThread.topic, claims);
                                // Here we should ideally update global claims context or UI?
                                // For now just log it, as SpaceLayout has a "Claims" tab logic that fetches from backend.
                            }}
                        />
                    </div>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-muted-foreground">
                        <div className="text-center">
                            <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-20" />
                            <p>Selecteer een gesprek of start een nieuwe.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
