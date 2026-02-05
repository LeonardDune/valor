import React, { useState, useEffect } from 'react';
import { X, Send, MessageSquare } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import type { Thread, ConversationMessage } from '../../types/conversation';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Card, CardHeader, CardContent } from '../ui/card';

interface FloatingThreadPanelProps {
    targetId: string;
    targetLabel?: string;
    onClose: () => void;
    onThreadCreated?: () => void;
    position?: { x: number; y: number };
    readOnly?: boolean;
}

export const FloatingThreadPanel: React.FC<FloatingThreadPanelProps> = ({
    targetId,
    targetLabel,
    onClose,
    onThreadCreated,
    position,
    readOnly = false
}) => {
    const [view, setView] = useState<'list' | 'chat' | 'create'>('list');
    const [threads, setThreads] = useState<Thread[]>([]);
    const [activeThread, setActiveThread] = useState<Thread | null>(null);
    const [messages, setMessages] = useState<ConversationMessage[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [newTopic, setNewTopic] = useState('');
    const [loading, setLoading] = useState(false);
    const { user } = useAuth();

    // Fetch threads on mount
    useEffect(() => {
        loadThreads();
    }, [targetId]);

    const loadThreads = async () => {
        if (!targetId) return;
        setLoading(true);
        try {
            const data = await api.getThreads(targetId);
            setThreads(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectThread = async (thread: Thread) => {
        setActiveThread(thread);
        setLoading(true);
        try {
            const msgs = await api.getThreadMessages(thread.id);
            setMessages(msgs);
            setView('chat');
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateThread = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (readOnly || !newTopic.trim()) return;

        setLoading(true);
        try {
            const newThread = await api.createThread(targetId, newTopic.trim());
            const threadObj: Thread = {
                ...newThread,
                status: 'active',
                created_at: new Date().toISOString()
            };
            setThreads([threadObj, ...threads]);
            setNewTopic('');
            handleSelectThread(threadObj);
            onThreadCreated?.(); // Notify parent to refresh stats
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const startCreating = () => {
        if (readOnly) return;
        setNewTopic(`Discussie over ${targetLabel || 'Item'}`);
        setView('create');
    };

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (readOnly || !newMessage.trim() || !activeThread) return;

        try {
            const msg = await api.createThreadMessage(activeThread.id, newMessage);
            setMessages([...messages, msg]);
            setNewMessage('');
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <Card
            className="fixed z-50 w-80 shadow-2xl flex flex-col overflow-hidden"
            style={{
                left: position ? position.x : '50%',
                top: position ? position.y : '50%',
                maxHeight: '500px',
                transform: position ? 'none' : 'translate(-50%, -50%)'
            }}
        >
            {/* Header */}
            <CardHeader className="flex flex-row items-center justify-between p-3 border-b bg-muted/20 space-y-0">
                <div className="flex items-center gap-2">
                    {view !== 'list' && (
                        <Button variant="ghost" size="icon" className="h-5 w-5 -ml-1" onClick={() => setView('list')}>
                            <span className="sr-only">Terug</span>
                            ←
                        </Button>
                    )}
                    <h3 className="font-medium text-sm truncate max-w-[200px]">
                        {view === 'list' ? 'Discussies' :
                            view === 'create' ? 'Nieuw Onderwerp' :
                                activeThread?.topic}
                    </h3>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
                    <X className="h-4 w-4" />
                </Button>
            </CardHeader>

            {/* Content */}
            <CardContent className="flex-1 overflow-hidden flex flex-col p-0">
                {loading && <div className="p-4 text-center text-xs text-muted-foreground">Laden...</div>}

                {!loading && view === 'list' && (
                    <ScrollArea className="flex-1">
                        {threads.length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">
                                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-20" />
                                <p className="text-sm">Nog geen discussies.</p>
                                {!readOnly && (
                                    <Button size="sm" variant="outline" className="mt-4" onClick={startCreating}>
                                        Discussie Starten
                                    </Button>
                                )}
                            </div>
                        ) : (
                            <div className="p-2 space-y-1">
                                {threads.map(thread => (
                                    <button
                                        key={thread.id}
                                        onClick={() => handleSelectThread(thread)}
                                        className="w-full text-left p-2 rounded hover:bg-muted text-sm flex items-center justify-between group"
                                    >
                                        <span className="truncate flex-1">{thread.topic}</span>
                                        <span className="text-[10px] text-muted-foreground">
                                            {new Intl.DateTimeFormat('nl-NL', { month: 'short', day: 'numeric' }).format(new Date(thread.created_at))}
                                        </span>
                                    </button>
                                ))}
                                {!readOnly && (
                                    <div className="pt-2 mt-2 border-t px-2">
                                        <Button size="sm" variant="secondary" className="w-full h-8" onClick={startCreating}>
                                            + Nieuw Onderwerp
                                        </Button>
                                    </div>
                                )}
                            </div>
                        )}
                    </ScrollArea>
                )}

                {!loading && view === 'create' && !readOnly && (
                    <div className="p-4 space-y-4">
                        <div className="space-y-2">
                            <label className="text-xs font-medium text-muted-foreground">Onderwerp</label>
                            <Input
                                value={newTopic}
                                onChange={e => setNewTopic(e.target.value)}
                                placeholder="Bijv. Definitie van deze factor"
                                className="h-9"
                                autoFocus
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button variant="ghost" className="flex-1" onClick={() => setView('list')}>Annuleren</Button>
                            <Button className="flex-1" onClick={handleCreateThread} disabled={!newTopic.trim()}>Starten</Button>
                        </div>
                    </div>
                )}

                {!loading && view === 'chat' && (
                    <>
                        <ScrollArea className="flex-1 p-3">
                            <div className="space-y-3">
                                {messages.map(msg => {
                                    const isOwnMessage = user?.id === msg.user_id;

                                    return (
                                        <div key={msg.id} className={`flex flex-col gap-1 w-full ${isOwnMessage ? 'items-end' : 'items-start'}`}>
                                            {!isOwnMessage && (
                                                <span className="text-[10px] text-muted-foreground px-1 font-medium">
                                                    {msg.author_name || 'Gebruiker'}
                                                </span>
                                            )}
                                            <div className={`p-2.5 rounded-2xl text-sm max-w-[85%] shadow-sm ${isOwnMessage
                                                ? 'bg-blue-600/10 text-blue-900 border border-blue-600/20 rounded-tr-none'
                                                : 'bg-muted text-foreground rounded-tl-none'
                                                }`}>
                                                {msg.content}
                                            </div>
                                            <span className="text-[10px] text-muted-foreground px-1 opacity-70">
                                                {isOwnMessage ? 'Jij' : (msg.author_name || 'Gebruiker')} • {new Intl.DateTimeFormat('nl-NL', { hour: '2-digit', minute: '2-digit' }).format(new Date(msg.created_at))}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        </ScrollArea>
                        {!readOnly && (
                            <form onSubmit={handleSendMessage} className="p-2 border-t flex gap-2">
                                <Input
                                    value={newMessage}
                                    onChange={e => setNewMessage(e.target.value)}
                                    placeholder="Schrijf een antwoord..."
                                    className="h-8 text-sm"
                                />
                                <Button type="submit" size="icon" className="h-8 w-8">
                                    <Send className="h-3.5 w-3.5" />
                                </Button>
                            </form>
                        )}
                    </>
                )}
            </CardContent>
        </Card>
    );
};
