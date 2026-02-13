import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

export const PROJECT_KEYS = {
    all: ['projects'] as const,
    list: (orgId?: string) => [...PROJECT_KEYS.all, 'list', { orgId }] as const,
    detail: (id: string) => [...PROJECT_KEYS.all, 'detail', id] as const,
};

export function useProjects(organizationId?: string) {
    return useQuery({
        queryKey: PROJECT_KEYS.list(organizationId),
        queryFn: () => organizationId ? api.getProjects(organizationId) : Promise.resolve([]),
        enabled: !!organizationId,
    });
}

export function useCreateProject() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ name, organizationId, description }: { name: string; organizationId: string; description?: string }) =>
            api.createProject(name, organizationId, description),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: PROJECT_KEYS.all });
        },
    });
}

export function useUpdateProject() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, name, description }: { id: string; name?: string; description?: string }) =>
            api.updateProject(id, name, description),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: PROJECT_KEYS.all });
            queryClient.invalidateQueries({ queryKey: PROJECT_KEYS.detail(variables.id) });
        },
    });
}

export function useArchiveProject() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => api.archiveProject(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: PROJECT_KEYS.all });
        },
    });
}
