import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { AlertCircle, Loader2, Clock, User, Tag } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { api, type DecisionEpisodeRaw } from '@/services/api';

const FASE_LABELS: Record<string, string> = {
    refine: 'Verfijnen',
    Refine: 'Verfijnen',
    ranking: 'Prioritering',
    Ranking: 'Prioritering',
    consent: 'Instemming',
    Consent: 'Instemming',
};

const VOTE_TYPE_LABELS: Record<string, string> = {
    Accept: 'Akkoord',
    accept: 'Akkoord',
    Reject: 'Afwijzen',
    reject: 'Afwijzen',
    Defer: 'Uitstellen',
    defer: 'Uitstellen',
};

const VOTE_TYPE_VARIANT: Record<string, 'default' | 'destructive' | 'outline' | 'secondary'> = {
    Accept: 'default',
    accept: 'default',
    Reject: 'destructive',
    reject: 'destructive',
    Defer: 'secondary',
    defer: 'secondary',
};

const TYPE_LABELS: Record<string, string> = {
    DecisionEpisode: 'Beslissing',
    PhaseTransition: 'Faseovergang',
};

function formatDateTime(iso: string): string {
    try {
        return new Intl.DateTimeFormat('nl-NL', {
            dateStyle: 'medium',
            timeStyle: 'short',
        }).format(new Date(iso));
    } catch {
        return iso;
    }
}

function formatUri(uri: string): string {
    const fragment = uri.split('/').pop()?.split('#').pop() ?? uri;
    // Verwijder UUID-achtige suffixen en toon alleen leesbaar deel
    if (fragment.length > 36 && fragment.includes('-')) {
        return fragment.substring(0, 8) + '…';
    }
    return fragment;
}

interface EpisodeCardProps {
    episode: DecisionEpisodeRaw;
}

const EpisodeCard: React.FC<EpisodeCardProps> = ({ episode }) => {
    const typeLabel = TYPE_LABELS[episode.type] ?? episode.type;
    const faseLabel = episode.phase ? (FASE_LABELS[episode.phase] ?? episode.phase) : null;

    return (
        <div className="flex gap-4">
            {/* Tijdlijn indicator */}
            <div className="flex flex-col items-center">
                <div className="w-3 h-3 rounded-full bg-primary mt-1 shrink-0" />
                <div className="w-px flex-1 bg-border mt-1" />
            </div>

            {/* Kaartinhoud */}
            <div className="pb-6 flex-1 min-w-0">
                <div className="rounded-lg border bg-card p-4 shadow-sm">
                    {/* Header */}
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                        <Badge variant="outline" className="text-xs">
                            {typeLabel}
                        </Badge>
                        {faseLabel && (
                            <Badge variant="secondary" className="text-xs">
                                <Tag className="h-3 w-3 mr-1" />
                                {faseLabel}
                            </Badge>
                        )}
                    </div>

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-4 text-xs text-muted-foreground mt-2">
                        {episode.startedAt && (
                            <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {formatDateTime(episode.startedAt)}
                            </span>
                        )}
                        {episode.startedBy && (
                            <span className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {formatUri(episode.startedBy)}
                            </span>
                        )}
                    </div>

                    {/* Stemmen */}
                    {episode.votes.length > 0 && (
                        <div className="mt-3 pt-3 border-t">
                            <p className="text-xs font-medium text-muted-foreground mb-2">
                                Stemmen ({episode.votes.length})
                            </p>
                            <div className="flex flex-wrap gap-2">
                                {episode.votes.map((vote) => {
                                    const label = VOTE_TYPE_LABELS[vote.voteType] ?? vote.voteType;
                                    const variant = VOTE_TYPE_VARIANT[vote.voteType] ?? 'outline';
                                    return (
                                        <div key={vote.voteUri} className="flex items-center gap-1.5">
                                            <Badge variant={variant} className="text-xs">
                                                {label}
                                            </Badge>
                                            <span className="text-xs text-muted-foreground">
                                                {formatUri(vote.castBy)}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

interface DecisionTimelineProps {
    dsId?: string;
}

export const DecisionTimeline: React.FC<DecisionTimelineProps> = ({ dsId: dsProp }) => {
    const { dsId: dsParam } = useParams<{ dsId: string }>();
    const dsId = dsProp ?? dsParam ?? '';

    const { data, isLoading, isError } = useQuery({
        queryKey: ['decision-timeline', dsId],
        queryFn: () => api.getDecisionTimeline(dsId),
        enabled: !!dsId,
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64 gap-2 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm">Beslissingen laden...</span>
            </div>
        );
    }

    if (isError) {
        return (
            <Alert variant="destructive" className="m-6">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                    De beslissingstijdlijn kon niet worden geladen. Controleer de verbinding en probeer het opnieuw.
                </AlertDescription>
            </Alert>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
                Nog geen beslissingen vastgelegd.
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto px-6 py-8">
            <h1 className="text-xl font-semibold mb-6">Beslissingstijdlijn</h1>
            <div className="flex flex-col">
                {data.map((episode) => (
                    <EpisodeCard key={episode.episodeUri} episode={episode} />
                ))}
            </div>
        </div>
    );
};
