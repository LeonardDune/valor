import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

export const THEME_KEYS = {
    all: ['themes'] as const,
    list: (projectId?: string) => [...THEME_KEYS.all, 'list', { projectId }] as const,
    detail: (id: string) => [...THEME_KEYS.all, 'detail', id] as const,
};

export function useThemes(projectId: string) {
    return useQuery({
        queryKey: THEME_KEYS.list(projectId),
        queryFn: () => api.getProjectThemes(projectId),
        enabled: !!projectId,
    });
}

export function useDashboardThemes() {
    return useQuery({
        queryKey: [...THEME_KEYS.all, 'dashboard'],
        queryFn: api.getDashboardThemes,
    });
}

export function useCreateTheme() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, name, description }: { projectId: string; name: string; description?: string }) =>
            api.createTheme(projectId, name, description),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: THEME_KEYS.all });
        },
    });
}

export function useUpdateTheme() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, name, description }: { id: string; name?: string; description?: string }) =>
            api.updateTheme(id, name, description),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: THEME_KEYS.all });
            queryClient.invalidateQueries({ queryKey: THEME_KEYS.detail(variables.id) });
        },
    });
}

export function useArchiveTheme() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => api.archiveTheme(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: THEME_KEYS.all });
        },
    });
}
