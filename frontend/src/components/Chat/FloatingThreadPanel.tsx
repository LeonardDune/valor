import React, { useState, useEffect } from 'react';
import { X, Send, MessageSquare, Gavel } from 'lucide-react';
import { api, type DiscThread, type DiscContribution } from '../../services/api';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Card, CardHeader, CardContent } from '../ui/card';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '../ui/select';

const CONTRIBUTION_TYPES = [
    'Vraag',
    'Stelling',
    'Bewijs',
    'Bezwaar',
    'Toelichting',
    'Akkoord',
] as const;

type ContributionTypeLabel = typeof CONTRIBUTION_TYPES[number];

const TYPE_BADGE_VARIANT: Record<ContributionTypeLabel, string> = {
    Vraag:       'bg-blue-100 text-blue-800 border-blue-200',
    Stelling:    'bg-purple-100 text-purple-800 border-purple-200',
    Bewijs:      'bg-green-100 text-green-800 border-green-200',
    Bezwaar:     'bg-red-100 text-red-800 border-red-200',
    Toelichting: 'bg-amber-100 text-amber-800 border-amber-200',
    Akkoord:     'bg-emerald-100 text-emerald-800 border-emerald-200',
};

function contributionTypeLabel(uri: string): ContributionTypeLabel {
    const fragment = uri.split('#').pop() ?? uri.split('/').pop() ?? uri;
    return (CONTRIBUTION_TYPES as readonly string[]).includes(fragment)
        ? (fragment as ContributionTypeLabel)
        : 'Toelichting';
}

function shortUri(uri: string): string {
    return uri.split(':').pop() ?? uri;
}

interface EpistemicStatus {
    uri: string;
    label_en: string;
    label_nl: string;
}

interface FloatingThreadPanelProps {
    tesseraId: string;
    designSpaceId?: string;
    targetLabel?: string;
    onClose: () => void;
    onThreadCreated?: () => void;
    position?: { x: number; y: number };
    readOnly?: boolean;
    canResolve?: boolean;
}

export const FloatingThreadPanel: React.FC<FloatingThreadPanelProps> = ({
    tesseraId,
    designSpaceId,
    targetLabel,
    onClose,
    onThreadCreated,
    position,
    readOnly = false,
    canResolve = false,
}) => {
    const [view, setView] = useState<'list' | 'contributions'>('list');
    const [threads, setThreads] = useState<DiscThread[]>([]);
    const [activeThread, setActiveThread] = useState<DiscThread | null>(null);
    const [contributions, setContributions] = useState<DiscContribution[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [newType, setNewType] = useState<ContributionTypeLabel>('Stelling');
    const [loading, setLoading] = useState(false);
    const [newTitle, setNewTitle] = useState('');

    // Resolution state
    const [epistemicStatuses, setEpistemicStatuses] = useState<EpistemicStatus[]>([]);
    const [resolveOutcome, setResolveOutcome] = useState('');
    const [resolveRationale, setResolveRationale] = useState('');
    const [resolving, setResolving] = useState(false);
    const [resolveResult, setResolveResult] = useState<{ label_nl: string } | null>(null);

    useEffect(() => {
        if (designSpaceId) loadThreads();
    }, [tesseraId, designSpaceId]);

    useEffect(() => {
        if (canResolve && view === 'contributions') {
            api.getEpistemicStatuses().then(setEpistemicStatuses).catch(() => {});
        }
    }, [canResolve, view]);

    const loadThreads = async () => {
        if (!designSpaceId) return;
        setLoading(true);
        try {
            const data = await api.getDiscThreads(tesseraId, designSpaceId!);
            setThreads(data);
            if (data.length === 1) {
                await openThread(data[0]);
            }
        } catch (e) {
            console.error('[FloatingThreadPanel] loadThreads:', e);
        } finally {
            setLoading(false);
        }
    };

    const openThread = async (thread: DiscThread) => {
        setActiveThread(thread);
        setResolveResult(null);
        setResolveOutcome('');
        setResolveRationale('');
        setLoading(true);
        try {
            const data = await api.getDiscContributions(thread.thread_id, designSpaceId!);
            setContributions(data);
            setView('contributions');
        } catch (e) {
            console.error('[FloatingThreadPanel] openThread:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateThread = async () => {
        if (readOnly) return;
        setLoading(true);
        try {
            await api.createDiscThread(tesseraId, designSpaceId!, newTitle.trim() || undefined);
            setNewTitle('');
            onThreadCreated?.();
            await loadThreads();
        } catch (e) {
            console.error('[FloatingThreadPanel] handleCreateThread:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleSendContribution = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (readOnly || !newMessage.trim() || !activeThread) return;

        try {
            await api.createDiscContribution(activeThread.thread_id, {
                design_space_id: designSpaceId!,
                contribution_type: newType,
                message_content: newMessage.trim(),
            });
            setNewMessage('');
            const data = await api.getDiscContributions(activeThread.thread_id, designSpaceId!);
            setContributions(data);
        } catch (e) {
            console.error('[FloatingThreadPanel] handleSendContribution:', e);
        }
    };

    const handleResolve = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!activeThread || !resolveOutcome || !resolveRationale.trim()) return;
        setResolving(true);
        try {
            await api.resolveDiscThread(activeThread.thread_id, {
                design_space_id: designSpaceId!,
                resolution_outcome: resolveOutcome,
                resolution_rationale: resolveRationale.trim(),
            });
            const status = epistemicStatuses.find(s => s.label_en === resolveOutcome);
            setResolveResult({ label_nl: status?.label_nl ?? resolveOutcome });
        } catch (e) {
            console.error('[FloatingThreadPanel] handleResolve:', e);
        } finally {
            setResolving(false);
        }
    };

    return (
        <Card
            className="fixed z-50 w-80 shadow-2xl flex flex-col overflow-hidden"
            style={{
                left: position ? position.x : '50%',
                top: position ? position.y : '50%',
                maxHeight: '560px',
                transform: position ? 'none' : 'translate(-50%, -50%)',
            }}
        >
            {/* Header */}
            <CardHeader className="flex flex-row items-center justify-between p-3 border-b bg-muted/20 space-y-0">
                <div className="flex items-center gap-2">
                    {view !== 'list' && (
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-5 w-5 -ml-1"
                            onClick={() => setView('list')}
                        >
                            <span className="sr-only">Terug</span>
                            ←
                        </Button>
                    )}
                    <h3 className="font-medium text-sm truncate max-w-[200px]">
                        {view === 'list'
                            ? `Discussies${targetLabel ? `: ${targetLabel}` : ''}`
                            : activeThread
                            ? new Intl.DateTimeFormat('nl-NL', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(activeThread.started_at))
                            : 'Discussie'}
                    </h3>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
                    <X className="h-4 w-4" />
                </Button>
            </CardHeader>

            {/* Content */}
            <CardContent className="flex-1 overflow-hidden flex flex-col p-0">
                {!designSpaceId && (
                    <div className="p-6 text-center text-xs text-muted-foreground">
                        <MessageSquare className="h-6 w-6 mx-auto mb-2 opacity-20" />
                        <p>Geen DesignSpace gekoppeld.</p>
                        <p className="mt-1 opacity-70">Discussies zijn beschikbaar in een actieve DesignSpace.</p>
                    </div>
                )}
                {designSpaceId && loading && (
                    <div className="p-4 text-center text-xs text-muted-foreground">Laden...</div>
                )}

                {/* Thread list */}
                {designSpaceId && !loading && view === 'list' && (
                    <ScrollArea className="flex-1">
                        {threads.length === 0 ? (
                            <div className="p-6 text-center text-muted-foreground">
                                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-20" />
                                <p className="text-sm">Nog geen discussies.</p>
                                {!readOnly && (
                                    <div className="mt-4 space-y-2">
                                        <Input
                                            value={newTitle}
                                            onChange={e => setNewTitle(e.target.value)}
                                            placeholder="Onderwerp (optioneel)"
                                            className="h-8 text-xs"
                                        />
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            className="w-full"
                                            onClick={handleCreateThread}
                                            disabled={loading}
                                        >
                                            Discussie Starten
                                        </Button>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="p-2 space-y-1">
                                {threads.map(thread => (
                                    <button
                                        key={thread.thread_id}
                                        onClick={() => openThread(thread)}
                                        className="w-full text-left p-2 rounded hover:bg-muted text-sm flex items-center justify-between group"
                                    >
                                        <span className="truncate flex-1 text-xs font-medium">
                                            {thread.title ?? `Discussie ${new Intl.DateTimeFormat('nl-NL', { month: 'short', day: 'numeric' }).format(new Date(thread.started_at))}`}
                                        </span>
                                        <span className="text-[10px] text-muted-foreground ml-2 shrink-0">
                                            {thread.started_by_name ?? shortUri(thread.started_by)}
                                        </span>
                                    </button>
                                ))}
                                {!readOnly && (
                                    <div className="pt-2 mt-2 border-t px-2 space-y-1">
                                        <Input
                                            value={newTitle}
                                            onChange={e => setNewTitle(e.target.value)}
                                            placeholder="Onderwerp (optioneel)"
                                            className="h-7 text-xs"
                                        />
                                        <Button
                                            size="sm"
                                            variant="secondary"
                                            className="w-full h-8"
                                            onClick={handleCreateThread}
                                            disabled={loading}
                                        >
                                            + Nieuwe Discussie
                                        </Button>
                                    </div>
                                )}
                            </div>
                        )}
                    </ScrollArea>
                )}

                {/* Contributions view */}
                {designSpaceId && !loading && view === 'contributions' && (
                    <>
                        <ScrollArea className="flex-1 p-3">
                            <div className="space-y-3">
                                {contributions.length === 0 && (
                                    <p className="text-xs text-muted-foreground text-center py-4">
                                        Nog geen bijdragen. Voeg de eerste toe.
                                    </p>
                                )}
                                {contributions.map(contrib => {
                                    const typeLabel = contributionTypeLabel(contrib.contribution_type);
                                    const badgeClass = TYPE_BADGE_VARIANT[typeLabel];
                                    return (
                                        <div key={contrib.contribution_id} className="flex flex-col gap-1">
                                            <div className="flex items-center gap-2">
                                                <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border ${badgeClass}`}>
                                                    {typeLabel}
                                                </span>
                                                <span className="text-[10px] text-muted-foreground truncate">
                                                    {contrib.contributed_by_name ?? shortUri(contrib.contributed_by)}
                                                </span>
                                                <span className="text-[10px] text-muted-foreground ml-auto shrink-0">
                                                    {new Intl.DateTimeFormat('nl-NL', { hour: '2-digit', minute: '2-digit' }).format(new Date(contrib.contributed_at))}
                                                </span>
                                            </div>
                                            <div className="bg-muted rounded-lg p-2 text-sm">
                                                {contrib.message_content}
                                                {contrib.evidence_id && (
                                                    <div className="mt-1 text-[10px] text-muted-foreground border-t pt-1">
                                                        Bewijs: {contrib.evidence_id}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </ScrollArea>

                        {/* Resolution banner (na succesvolle resolve) */}
                        {resolveResult && (
                            <div className="px-3 py-2 bg-emerald-50 border-t border-emerald-200 text-xs text-emerald-800 flex items-center gap-1.5">
                                <Gavel className="h-3.5 w-3.5 shrink-0" />
                                <span>Thread afgesloten als <strong>{resolveResult.label_nl}</strong></span>
                            </div>
                        )}

                        {/* Contribution form */}
                        {!readOnly && !resolveResult && (
                            <form onSubmit={handleSendContribution} className="p-2 border-t space-y-2">
                                <Select
                                    value={newType}
                                    onValueChange={v => setNewType(v as ContributionTypeLabel)}
                                >
                                    <SelectTrigger className="h-7 text-xs">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {CONTRIBUTION_TYPES.map(t => (
                                            <SelectItem key={t} value={t} className="text-xs">
                                                {t}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <div className="flex gap-2">
                                    <Input
                                        value={newMessage}
                                        onChange={e => setNewMessage(e.target.value)}
                                        placeholder="Schrijf een bijdrage..."
                                        className="h-8 text-sm"
                                    />
                                    <Button
                                        type="submit"
                                        size="icon"
                                        className="h-8 w-8 shrink-0"
                                        disabled={!newMessage.trim()}
                                    >
                                        <Send className="h-3.5 w-3.5" />
                                    </Button>
                                </div>
                            </form>
                        )}

                        {/* Resolution form (alleen voor moderator) */}
                        {canResolve && !resolveResult && (
                            <form onSubmit={handleResolve} className="p-2 border-t space-y-2 bg-muted/10">
                                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-medium uppercase tracking-wide">
                                    <Gavel className="h-3 w-3" />
                                    Afsluiten
                                </div>
                                <Select
                                    value={resolveOutcome}
                                    onValueChange={setResolveOutcome}
                                >
                                    <SelectTrigger className="h-7 text-xs">
                                        <SelectValue placeholder="Uitkomst kiezen..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {epistemicStatuses.map(s => (
                                            <SelectItem key={s.uri} value={s.label_en} className="text-xs">
                                                {s.label_nl}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Textarea
                                    value={resolveRationale}
                                    onChange={e => setResolveRationale(e.target.value)}
                                    placeholder="Motivatie voor afsluiting..."
                                    className="text-xs min-h-[48px] resize-none"
                                    rows={2}
                                />
                                <Button
                                    type="submit"
                                    size="sm"
                                    variant="outline"
                                    className="w-full h-7 text-xs"
                                    disabled={!resolveOutcome || !resolveRationale.trim() || resolving}
                                >
                                    <Gavel className="h-3 w-3 mr-1.5" />
                                    {resolving ? 'Bezig...' : 'Thread Afsluiten'}
                                </Button>
                            </form>
                        )}
                    </>
                )}
            </CardContent>
        </Card>
    );
};
