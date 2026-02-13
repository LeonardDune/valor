import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionService } from '@/services/sessions';

export const SESSION_KEYS = {
    all: ['sessions'] as const,
    active: (themeVersionId: string) => [...SESSION_KEYS.all, 'active', { themeVersionId }] as const,
};

/**
 * Hook to fetch the active voting session for a theme version.
 * Uses React Query for automatic caching and revalidation.
 */
export function useActiveSession(themeVersionId: string | null) {
    return useQuery({
        queryKey: SESSION_KEYS.active(themeVersionId || ''),
        queryFn: async () => {
            if (!themeVersionId) return null;
            return sessionService.getActiveSession(themeVersionId);
        },
        enabled: !!themeVersionId,
        staleTime: 5000, // Consider data stale after 5 seconds
        refetchOnWindowFocus: true,
    });
}

/**
 * Mutation to update the stage of a voting session.
 * Automatically invalidates active session queries on success.
 */
export function useUpdateSessionStage() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ sessionId, stage }: { sessionId: string; stage: string }) =>
            sessionService.updateStage(sessionId, stage),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: SESSION_KEYS.all });
        },
    });
}

export function useSessionParticipation(sessionId: string | null) {
    return useQuery({
        queryKey: [...SESSION_KEYS.all, 'participation', sessionId],
        queryFn: () => sessionService.getSessionParticipation(sessionId!),
        enabled: !!sessionId,
    });
}

export function useFinalizeDeliberation() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (sessionId: string) => sessionService.finalizeDeliberation(sessionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sessions'] });
            queryClient.invalidateQueries({ queryKey: ['themes'] });
        },
    });
}

export function useManagedSessions() {
    return useQuery({
        queryKey: [...SESSION_KEYS.all, 'managed'],
        queryFn: () => sessionService.getManagedSessions(),
    });
}

export function useSessionValidation(sessionId: string, targetStage: string) {
    return useQuery({
        queryKey: [...SESSION_KEYS.all, 'validation', sessionId, targetStage],
        queryFn: () => sessionService.getTransitionValidation(sessionId, targetStage),
        enabled: !!sessionId && !!targetStage,
    });
}
