// 
import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { api, type Factor } from '@/services/api';
import { sessionService } from '@/services/sessions';
import { useActiveSession } from '@/hooks/queries/useSessions';
import { RefinementSidebar } from './RefinementSidebar.tsx';
import { RefinementDetail } from './RefinementDetail.tsx';
import { RefinementDecision } from './RefinementDecision.tsx';
import { Loader2, AlertCircle, Target } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert.tsx';
import { Button } from '@/components/ui/button.tsx';
import { toast } from 'sonner';

interface RefinementBoardProps {
    versionId?: string;
    onBack?: () => void;
    factors?: Factor[];
    currentUserId?: string;
    isModerator?: boolean;
}

export const RefinementBoardComponent: React.FC<RefinementBoardProps> = ({
    versionId: propVersionId,
    onBack,
    factors,
    currentUserId,
    isModerator
}) => {
    const { versionId: routeVersionId } = useParams<{ versionId: string }>();
    const versionId = propVersionId || routeVersionId;
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);

    // 1. Get active session via centralized hook
    const {
        data: session,
        isLoading: isLoadingSession,
        error: sessionError
    } = useActiveSession(versionId || null);

    // 2. Get claims for this version
    const {
        data: claims = [],
        isLoading: isLoadingClaims,
        error: claimsError
    } = useQuery({
        queryKey: ['claims', versionId],
        queryFn: () => api.getThemeVersionClaims(versionId!),
        enabled: !!versionId,
    });


    // 3. Get feedback if session exists
    const {
        data: feedbackData = []
    } = useQuery({
        queryKey: ['feedback', session?.id],
        queryFn: () => sessionService.getFeedback(session!.id),
        enabled: !!session?.id,
    });

    // 4. Mutation for submitting feedback
    const feedbackMutation = useMutation({
        mutationFn: ({ color, motivation, claimId }: { color: string, motivation: string, claimId: string }) =>
            sessionService.submitFeedback(session!.id, claimId, color, motivation),
        onSuccess: () => {
            // No toast for auto-save to keep UI clean, but could add a subtle indicator
            queryClient.invalidateQueries({ queryKey: ['feedback', session?.id] });
            queryClient.invalidateQueries({ queryKey: ['participation', session?.id] });
            queryClient.invalidateQueries({ queryKey: ['validation', session?.id] });
        },
        onError: (err) => {
            console.error("Failed to submit feedback", err);
            toast.error("Kon positie niet opslaan");
        }
    });

    // 5. Mutation for advancing stage
    const advanceStageMutation = useMutation({
        mutationFn: () => sessionService.updateStage(session!.id, 'ranking'),
        onSuccess: () => {
            toast.success("Ranking fase gestart");
            queryClient.invalidateQueries({ queryKey: ['sessions'] });
        },
        onError: (err) => {
            console.error("Failed to advance stage", err);
            toast.error("Kon fase niet wijzigen");
        }
    });

    const isLoading = isLoadingSession || isLoadingClaims;
    const error = sessionError || claimsError;

    // Derived state for the selected claim
    const effectiveSelectedClaimId = selectedClaimId || claims[0]?.id || null;
    const selectedClaim = claims.find(c => c.id === effectiveSelectedClaimId) || null;

    // Filter feedback for current user using version_id
    const myFeedback = useMemo(() => {
        if (!currentUserId || currentUserId === 'anon') return null;
        return feedbackData.find(f =>
            f.claim_version_id === selectedClaim?.version_id &&
            f.user_id === currentUserId
        ) || null;
    }, [feedbackData, selectedClaim?.version_id, currentUserId]);

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-muted-foreground">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p>Verfijningsbord laden...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8">
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Fout</AlertTitle>
                    <AlertDescription>Kon de gegevens voor verfijning niet laden.</AlertDescription>
                </Alert>
            </div>
        );
    }

    if (!session) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-8 text-center gap-4">
                <AlertCircle className="h-12 w-12 text-muted-foreground opacity-20" />
                <h2 className="text-2xl font-semibold">Geen actieve sessie</h2>
                <p className="text-muted-foreground max-w-md">
                    Er is momenteel geen actieve deliberatie-sessie voor deze versie.
                    Vraag een moderator om er een te starten.
                </p>
                <button
                    onClick={() => navigate(`/designspace/${versionId}`)}
                    className="text-primary hover:underline"
                >
                    Terug naar Dashboard
                </button>
            </div>
        );
    }

    return (
        <div className="flex h-full overflow-hidden bg-background">
            {/* Left: Sidebar (Claim List) */}
            <aside className="w-80 border-r border-border bg-muted/5 flex-shrink-0 flex flex-col">
                <div className="flex-1 overflow-y-auto">
                    <RefinementSidebar
                        claims={claims}
                        selectedId={effectiveSelectedClaimId}
                        onSelect={setSelectedClaimId}
                        feedbackData={feedbackData}
                        currentUserId={currentUserId}
                        onBack={onBack || (() => navigate(-1))}
                    />
                </div>

                {/* Moderator Controls */}
                {isModerator && (
                    <div className="p-4 border-t border-border bg-background">
                        <Button
                            className="w-full gap-2"
                            onClick={() => advanceStageMutation.mutate()}
                            disabled={advanceStageMutation.isPending}
                        >
                            {advanceStageMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <Target className="h-4 w-4" />
                            )}
                            Start Ranking Fase
                        </Button>
                    </div>
                )}
            </aside>

            {/* Center: Detail View */}
            <main className="flex-1 overflow-y-auto">
                <RefinementDetail
                    claim={selectedClaim}
                    allClaims={claims}
                    factors={factors}
                />
            </main>

            {/* Right: Decision/Voting */}
            <aside className="w-80 border-l border-border bg-muted/5 flex-shrink-0">
                <RefinementDecision
                    key={selectedClaim?.id}
                    claim={selectedClaim}
                    initialFeedback={myFeedback}
                    isSubmitting={feedbackMutation.isPending}
                    onFeedbackSubmitted={(color, motivation) => {
                        if (selectedClaim?.version_id) {
                            feedbackMutation.mutate({ color, motivation, claimId: selectedClaim.version_id });
                        }
                    }}
                />
            </aside>
        </div>
    );
};
