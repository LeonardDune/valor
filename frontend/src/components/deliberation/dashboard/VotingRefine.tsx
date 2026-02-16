import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { sessionService } from '@/services/sessions';
import { RefinementSidebar } from '../RefinementSidebar';
import { RefinementDecision } from '../RefinementDecision';
import { RefinementDetail } from '../RefinementDetail';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface RefinementViewProps {
    sessionId: string;
    versionId: string;
    currentUser: any; // user object
    factors?: any[];
    onComplete?: () => void;
}

export const VotingRefine: React.FC<RefinementViewProps> = ({ sessionId, versionId, currentUser, factors = [], onComplete }) => {
    const queryClient = useQueryClient();
    const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);

    // 1. Data Fetching (Copied from RefinementBoard)
    const { data: claims = [], isLoading: isLoadingClaims } = useQuery({
        queryKey: ['claims', versionId],
        queryFn: () => api.getThemeVersionClaims(versionId),
        enabled: !!versionId,
    });

    const { data: feedbackData = [] } = useQuery({
        queryKey: ['feedback', sessionId],
        queryFn: () => sessionService.getFeedback(sessionId),
        enabled: !!sessionId,
    });

    // 2. Mutation
    const feedbackMutation = useMutation({
        mutationFn: ({ color, motivation, claimId }: { color: string, motivation: string, claimId: string }) =>
            sessionService.submitFeedback(sessionId, claimId, color, motivation),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['feedback', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['participation', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['validation', sessionId] });
        },
        onError: (err) => {
            console.error("Failed to submit feedback", err);
            toast.error("Kon positie niet opslaan");
        }
    });

    // 3. Derived State
    const effectiveSelectedClaimId = selectedClaimId || claims[0]?.id || null;
    const selectedClaim = claims.find(c => c.id === effectiveSelectedClaimId) || null;

    const myFeedback = useMemo(() => {
        if (!currentUser?.id) return null;
        return feedbackData.find(f =>
            f.claim_version_id === selectedClaim?.version_id &&
            f.user_id === currentUser.id
        ) || null;
    }, [feedbackData, selectedClaim?.version_id, currentUser?.id]);

    if (isLoadingClaims) {
        return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;
    }

    return (
        <div className="flex h-full overflow-hidden bg-background">
            {/* Left: Sidebar (Claim List) - scaled down from w-80 to fit 800px */}
            <aside className="w-[30%] min-w-[220px] border-r border-border bg-muted/5 flex-shrink-0 flex flex-col">
                <div className="flex-1 h-full min-h-0">
                    <RefinementSidebar
                        claims={claims}
                        selectedId={effectiveSelectedClaimId}
                        onSelect={setSelectedClaimId}
                        feedbackData={feedbackData}
                        currentUserId={currentUser?.id}
                        onBack={onComplete}
                    />
                </div>
            </aside>

            {/* Center: Detail View */}
            <main className="flex-1 h-full min-h-0 min-w-[300px]">
                <RefinementDetail
                    claim={selectedClaim}
                    allClaims={claims}
                    factors={factors}
                />
            </main>

            {/* Right: Decision/Voting - scaled down from w-80 */}
            <aside className="w-[35%] min-w-[250px] border-l border-border bg-muted/5 flex-shrink-0 flex flex-col">
                <div className="flex-1 h-full min-h-0">
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
                </div>
            </aside>
        </div>
    );
};
