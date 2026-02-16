import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/context/ThemeContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { X, Shield } from 'lucide-react';
import { useSessionParticipation, useUpdateSessionStage, useFinalizeDeliberation, useSessionValidation } from '@/hooks/queries/useSessions';
import { toast } from 'sonner';
import { PhaseStart } from './dashboard/PhaseStart';
import { PhaseRefine } from './dashboard/PhaseRefine';
import { PhaseRanking } from './dashboard/PhaseRanking';
import { PhaseConsent } from './dashboard/PhaseConsent';
import type { VotingSessionConfig } from '@/types/session';

interface ModeratorDashboardProps {
    sessionId?: string;
    stage?: string;
    onClose?: () => void;
    onStartSession?: (config: VotingSessionConfig) => void;
    isStartingSession?: boolean;
}

export const ModeratorDashboard: React.FC<ModeratorDashboardProps> = ({
    sessionId,
    stage,
    onClose,
    onStartSession,
    isStartingSession = false
}) => {
    const { refreshVersions } = useTheme();

    // Stage Mapping for Tabs
    const [activeTab, setActiveTab] = useState<string>('start');

    // Sync tab with active stage
    useEffect(() => {
        if (!sessionId && activeTab !== 'start') {
            setActiveTab('start');
        } else if (stage && activeTab !== stage) {
            setActiveTab(stage);
        }
    }, [sessionId, stage, activeTab]);
    // Query Hooks (only run if sessionId exists)
    const { data: participation = [] } = useSessionParticipation(sessionId || '');
    const updateStageMutation = useUpdateSessionStage();
    const finalizeMutation = useFinalizeDeliberation();

    // Determine next stage
    const nextStage = stage === 'refine' ? 'ranking' : stage === 'ranking' ? 'consent' : stage === 'consent' ? 'closed' : null;

    // Validation for next stage
    const { data: validation } = useSessionValidation(sessionId || '', nextStage || '');

    // Handlers
    const handleAdvance = () => {
        if (!sessionId || !nextStage) return;
        updateStageMutation.mutate({ sessionId, stage: nextStage });
        toast.success(`Fase gewijzigd naar ${getStageLabel(nextStage)}`);
    };

    const handleFinalize = () => {
        if (!sessionId) return;
        finalizeMutation.mutate(sessionId, {
            onSuccess: async () => {
                await refreshVersions();
                toast.success("Deliberatie succesvol afgerond!");
                if (onClose) onClose();
            },
            onError: (err: any) => {
                toast.error(err.message || "Fout bij finaliseren");
            }
        });
    };

    // Render Logic
    return (
        <div className="flex flex-col h-full max-h-[85vh]">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                        <Shield className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold">Moderator Dashboard</h2>
                        <p className="text-muted-foreground text-sm">
                            {sessionId
                                ? `Actieve Sessie: ${getStageLabel(stage || '')}`
                                : "Start een nieuwe sessie"}
                        </p>
                    </div>
                </div>
                {onClose && (
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                    <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
                        <TabsTrigger value="start" disabled={!!sessionId}>Start</TabsTrigger>
                        <TabsTrigger value="refine" disabled={!sessionId}>Verfijnen</TabsTrigger>
                        <TabsTrigger value="ranking" disabled={!sessionId || stage === 'refine'}>Prioriteren</TabsTrigger>
                        <TabsTrigger value="consent" disabled={!sessionId || stage === 'refine' || stage === 'ranking'}>Instemmen</TabsTrigger>
                    </TabsList>

                    <TabsContent value="start" className="space-y-4">
                        {!sessionId ? (
                            <PhaseStart
                                onStart={(config: VotingSessionConfig) => onStartSession?.(config)}
                                isStarting={isStartingSession}
                                participantCount={0} // TODO: Pass potential participants count?
                            />
                        ) : (
                            <div className="p-8 text-center border rounded-lg bg-muted/10">
                                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                                <h3 className="text-lg font-semibold">Sessie is gestart</h3>
                                <p className="text-muted-foreground">De sessie is momenteel actief in fase: <strong>{getStageLabel(stage || '')}</strong></p>
                            </div>
                        )}
                    </TabsContent>

                    <TabsContent value="refine">
                        <PhaseRefine
                            participants={participation}
                            onAdvance={handleAdvance}
                            isAdvancing={updateStageMutation.isPending}
                            canAdvance={!!validation?.allowed}
                            validationMessage={validation?.message}
                        />
                    </TabsContent>

                    <TabsContent value="ranking">
                        <PhaseRanking
                            participants={participation}
                            onAdvance={handleAdvance}
                            isAdvancing={updateStageMutation.isPending}
                            canAdvance={!!validation?.allowed}
                            validationMessage={validation?.message}
                        />
                    </TabsContent>

                    <TabsContent value="consent">
                        <PhaseConsent
                            participants={participation}
                            onFinalize={handleFinalize}
                            isFinalizing={finalizeMutation.isPending}
                        />
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
};

// Helpers
import { CheckCircle } from 'lucide-react';

const getStageLabel = (stage: string) => {
    switch (stage) {
        case 'refine': return 'Verfijnen';
        case 'ranking': return 'Prioritering';
        case 'consent': return 'Instemming';
        case 'closed': return 'Gesloten';
        default: return stage;
    }
};
