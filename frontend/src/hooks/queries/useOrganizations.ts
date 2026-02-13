import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

export const ORGANIZATION_KEYS = {
    all: ['organizations'] as const,
    list: () => [...ORGANIZATION_KEYS.all, 'list'] as const,
    detail: (id: string) => [...ORGANIZATION_KEYS.all, 'detail', id] as const,
};

export function useOrganizations() {
    return useQuery({
        queryKey: ORGANIZATION_KEYS.list(),
        queryFn: api.getOrganizations,
    });
}

export function useDashboardEnvironments() {
    return useQuery({
        queryKey: [...ORGANIZATION_KEYS.all, 'dashboard'],
        queryFn: api.getDashboardEnvironments,
    });
}

export function useCreateOrganization() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ name, description }: { name: string; description?: string }) =>
            api.createOrganization(name, description),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ORGANIZATION_KEYS.all });
        },
    });
}

export function useUpdateOrganization() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, name, description }: { id: string; name?: string; description?: string }) =>
            api.updateOrganization(id, name, description),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ORGANIZATION_KEYS.all });
            queryClient.invalidateQueries({ queryKey: ORGANIZATION_KEYS.detail(variables.id) });
        },
    });
}

export function useArchiveOrganization() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => api.archiveOrganization(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ORGANIZATION_KEYS.all });
        },
    });
}
