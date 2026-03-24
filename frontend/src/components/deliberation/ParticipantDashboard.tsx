import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Button } from '@/components/ui/button';
import { X, MessageSquareText, Hourglass, CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { VotingRefine } from './dashboard/VotingRefine';
import { VotingRanking } from './dashboard/VotingRanking';
import { VotingConsent } from './dashboard/VotingConsent';

interface ParticipantDashboardProps {
    sessionId: string;
    versionId: string;
    stage: 'start' | 'refine' | 'ranking' | 'consent' | 'closed';
    onClose: () => void;
    currentUserId?: string;
    factors?: any[];
}

export const ParticipantDashboard: React.FC<ParticipantDashboardProps> = ({
    sessionId,
    versionId,
    stage,
    onClose,
    currentUserId,
    factors = []
}) => {
    const { data: currentUser } = useQuery({
        queryKey: ['me'],
        queryFn: () => api.getProfile(),
        enabled: !currentUserId
    });

    // Allow override
    const user = currentUserId ? { id: currentUserId } : currentUser;

    const handlePhaseComplete = async (phase: 'refine' | 'ranking' | 'consent') => {
        try {
            await api.completePhase(sessionId, phase);
            onClose();
        } catch (error) {
            console.error('Failed to complete phase:', error);
            // Close anyway to not block user
            onClose();
        }
    };

    const renderStageContent = () => {
        switch (stage) {
            case 'start':
                return (
                    <div className="flex flex-col items-center justify-center h-full p-8 text-center text-muted-foreground">
                        <Hourglass className="h-12 w-12 mb-4 opacity-50 animate-pulse" />
                        <h3 className="text-lg font-semibold mb-2">Sessie Start</h3>
                        <p>De moderator configureert de sessie. Wacht tot de stemming begint.</p>
                    </div>
                );
            case 'refine':
                return (
                    <VotingRefine
                        sessionId={sessionId}
                        versionId={versionId}
                        currentUser={user}
                        factors={factors}
                        onComplete={() => handlePhaseComplete('refine')}
                    />
                );
            case 'ranking':
                return (
                    <VotingRanking
                        sessionId={sessionId}
                        dsId={versionId}
                        onComplete={() => handlePhaseComplete('ranking')}
                    />
                );
            case 'consent':
                return (
                    <VotingConsent
                        sessionId={sessionId}
                        onComplete={() => handlePhaseComplete('consent')}
                    />
                );
            case 'closed':
                return (
                    <div className="flex flex-col items-center justify-center h-full p-8 text-center text-muted-foreground">
                        <CheckCircle2 className="h-12 w-12 mb-4 text-green-500" />
                        <h3 className="text-lg font-semibold mb-2">Sessie Gesloten</h3>
                        <p>De stemming is afgerond. Bedankt voor je deelname!</p>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="flex flex-col h-full bg-background border-l shadow-2xl">
            {/* Header */}
            <div className="p-4 border-b flex justify-between items-center bg-muted/5">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-primary/10 rounded-full">
                        <MessageSquareText className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                        <h2 className="font-bold text-lg leading-none">Stemmen</h2>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">Fase:</span>
                            <Badge variant="outline" className="text-[10px] h-4 uppercase">
                                {stage === 'refine' && 'Verfijnen'}
                                {stage === 'ranking' && 'Prioriteren'}
                                {stage === 'consent' && 'Instemmen'}
                                {stage === 'start' && 'Start'}
                                {stage === 'closed' && 'Gesloten'}
                            </Badge>
                        </div>
                    </div>
                </div>
                <Button variant="ghost" size="icon" onClick={onClose} className="hover:bg-destructive/10 hover:text-destructive">
                    <X className="h-4 w-4" />
                </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden">
                {renderStageContent()}
            </div>
        </div>
    );
};
