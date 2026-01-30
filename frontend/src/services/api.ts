import axios from 'axios';
import { supabase } from '../lib/supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
    baseURL: API_URL
});

// Add request interceptor to inject session token
apiClient.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
});

// Add response interceptor to handle 401s (Token Expired / Invalid)
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            console.warn("Session expired or unauthorized (401). Signing out...");
            await supabase.auth.signOut();
            // Force reload/redirect if needed, but AuthContext should handle it
            // window.location.href = '/login'; 
        }
        return Promise.reject(error);
    }
);

export type FactorType = 'middel' | 'extern' | 'systeemelement' | 'criterium';

export interface Claim {
    id: string;
    statement: string;
    confidence: number;
    source_node: string;
    source_id?: string;
    source_type?: FactorType;
    target_node: string;
    target_id?: string;
    target_type?: FactorType;
    relationship_type: string;
    polarity: string;
    created_at?: string;
}

export interface AgentResponse {
    agent_name: string;
    perspective: string;
    reply: string;
    extracted_claims: Claim[];
}

export interface ConversationResponse {
    conversation_id: string;
    reply: string;
    extracted_claims: Claim[];
    agent_responses: AgentResponse[];
}

export interface Factor {
    id: string;
    name: string;
    description: string;
    type: FactorType;
}

export interface Organization {
    id: string;
    name: string;
    description: string;
    role?: string;
}

export interface User {
    id: string;
    email: string;
    name?: string;
    first_name?: string;
    last_name?: string;
    username?: string;
    role?: string;
    status?: string;
    joined_at?: string;
    is_platform_admin?: boolean;
}

export interface Theme {
    id: string;
    name: string;
    description: string;
    project_id: string;
    role?: string;
}

export interface DashboardTheme {
    id: string;
    name: string;
    description: string;
    project_name?: string;
    organization_name: string;
    role?: string;
    status?: string;
    is_archived?: boolean;
    stats?: {
        active_claims: number;
        members: number;
    };
    perspectives?: {
        name: string;
        color: string;
        progress: number;
    }[];
    type: 'THEME';
}

export interface DashboardProject {
    id: string;
    name: string;
    description?: string;
    role?: string;
    status?: string;
    type: 'PROJECT';
    themes: DashboardTheme[];
}

export interface DashboardEnvironment {
    id: string;
    name: string;
    description?: string;
    role?: string;
    status?: string;
    type: 'ORGANIZATION';
    projects: DashboardProject[];
}

export interface Space {
    id: string;
    name: string;
    description: string;
    theme_id: string;
    role?: string;
    status?: string;
    created_at?: string;
}

export interface Invite {
    id: string;
    email: string;
    role: string;
    created_at: string;
    expires_at: string;
    code: string;
}

export interface ConversationThread {
    id: string;
    topic: string;
    status: string;
    created_at: string;
}

export const api = {
    healthCheck: async () => {
        const response = await apiClient.get('/health');
        return response.data;
    },

    chat: async (message: string, conversationId?: string, topic?: string) => {
        const response = await apiClient.post<ConversationResponse>('/chat', {
            message,
            conversation_id: conversationId,
            topic
        });
        return response.data;
    },

    // Organization & User
    getOrganizations: async () => {
        const response = await apiClient.get<Organization[]>('/organizations');
        return response.data;
    },

    createOrganization: async (name: string, description?: string) => {
        const response = await apiClient.post('/organizations', { name, description });
        return response.data;
    },

    updateOrganization: async (orgId: string, name?: string, description?: string) => {
        const response = await apiClient.patch(`/organizations/${orgId}`, { name, description });
        return response.data;
    },

    archiveOrganization: async (orgId: string) => {
        const response = await apiClient.delete(`/organizations/${orgId}`);
        return response.data;
    },

    createUser: async (email: string, name?: string) => {
        const response = await apiClient.post('/users', { email, name });
        return response.data;
    },

    updateUserProfile: async (firstName: string, lastName: string, username: string) => {
        const response = await apiClient.put('/users/me', { first_name: firstName, last_name: lastName, username });
        return response.data;
    },

    getProfile: async () => {
        const response = await apiClient.get<User>('/users/me');
        return response.data;
    },


    getOrganizationUsers: async (orgId: string) => {
        const response = await apiClient.get<User[]>(`/organizations/${orgId}/users`);
        return response.data;
    },

    getProjectUsers: async (projectId: string) => {
        const response = await apiClient.get<User[]>(`/projects/${projectId}/users`);
        return response.data;
    },

    getThemeUsers: async (themeId: string) => {
        const response = await apiClient.get<User[]>(`/themes/${themeId}/users`);
        return response.data;
    },

    getAllUsers: async () => {
        const response = await apiClient.get<User[]>('/users');
        return response.data;
    },

    addOrganizationUser: async (orgId: string, email: string, role: string = 'member') => {
        const response = await apiClient.post(`/organizations/${orgId}/users`, { email, role });
        return response.data;
    },

    updateOrgMember: async (orgId: string, userId: string, role: string, name?: string, status?: string) => {
        const response = await apiClient.put(`/organizations/${orgId}/users/${userId}`, { role, name, status });
        return response.data;
    },

    removeOrgMember: async (orgId: string, userId: string) => {
        const response = await apiClient.delete(`/organizations/${orgId}/users/${userId}`);
        return response.data;
    },

    updateProjectMember: async (projectId: string, userId: string, role: string, name?: string, status?: string) => {
        const response = await apiClient.put(`/projects/${projectId}/users/${userId}`, { role, name, status });
        return response.data;
    },

    removeProjectMember: async (projectId: string, userId: string) => {
        const response = await apiClient.delete(`/projects/${projectId}/users/${userId}`);
        return response.data;
    },

    updateThemeMember: async (themeId: string, userId: string, role: string, name?: string, status?: string) => {
        const response = await apiClient.put(`/themes/${themeId}/users/${userId}`, { role, name, status });
        return response.data;
    },

    removeThemeMember: async (themeId: string, userId: string) => {
        const response = await apiClient.delete(`/themes/${themeId}/users/${userId}`);
        return response.data;
    },

    // Invites
    createInvite: async (email: string, entityId: string, role: string, expiresInDays: number = 7) => {
        // Use configured App URL (prod) or fallback to current origin (dev/local).
        const appUrl = import.meta.env.VITE_APP_URL || window.location.origin;
        const redirectUrl = appUrl.replace(/\/$/, ""); // Ensure no trailing slash

        const response = await apiClient.post('/invites', {
            email,
            entity_id: entityId,
            role,
            expires_in_days: expiresInDays,
            redirect_url: redirectUrl
        });
        return response.data;
    },

    getPendingInvites: async (entityId: string, entityType: 'organization' | 'project' | 'theme' = 'organization') => {
        let endpoint = `/organizations/${entityId}/invites`;
        if (entityType === 'project') endpoint = `/projects/${entityId}/invites`;
        if (entityType === 'theme') endpoint = `/themes/${entityId}/invites`;

        const response = await apiClient.get<Invite[]>(endpoint);
        return response.data;
    },

    acceptInvite: async (code: string) => {
        const response = await apiClient.post('/invites/accept', { code });
        return response.data;
    },

    // Projects
    getProjects: async (organizationId: string) => {
        const response = await apiClient.get('/projects', { params: { organization_id: organizationId } });
        return response.data;
    },

    createProject: async (name: string, organizationId: string, description?: string) => {
        const response = await apiClient.post('/projects', { name, organization_id: organizationId, description });
        return response.data;
    },

    updateProject: async (projectId: string, name?: string, description?: string) => {
        const response = await apiClient.patch(`/projects/${projectId}`, { name, description });
        return response.data;
    },

    archiveProject: async (projectId: string) => {
        const response = await apiClient.delete(`/projects/${projectId}`);
        return response.data;
    },

    getProjectThemes: async (projectId: string) => {
        const response = await apiClient.get<Theme[]>(`/projects/${projectId}/themes`);
        return response.data;
    },

    createTheme: async (projectId: string, name: string, description?: string) => {
        const response = await apiClient.post(`/projects/${projectId}/themes`, { project_id: projectId, name, description });
        return response.data;
    },

    updateTheme: async (themeId: string, name?: string, description?: string) => {
        const response = await apiClient.patch(`/themes/${themeId}`, { name, description });
        return response.data;
    },

    archiveTheme: async (themeId: string) => {
        const response = await apiClient.delete(`/themes/${themeId}`);
        return response.data;
    },

    // Spaces
    getThemeSpaces: async (themeId: string) => {
        const response = await apiClient.get<Space[]>(`/themes/${themeId}/spaces`);
        return response.data;
    },

    getSpace: async (spaceId: string) => {
        const response = await apiClient.get<Space>(`/spaces/${spaceId}`);
        return response.data;
    },

    createSpace: async (themeId: string, name: string, description?: string) => {
        const response = await apiClient.post(`/themes/${themeId}/spaces`, { name, description });
        return response.data;
    },

    updateSpace: async (spaceId: string, name?: string, description?: string) => {
        const response = await apiClient.patch(`/spaces/${spaceId}`, { name, description });
        return response.data;
    },

    archiveSpace: async (spaceId: string) => {
        const response = await apiClient.delete(`/spaces/${spaceId}`);
        return response.data;
    },

    getSpaceThreads: async (spaceId: string) => {
        const response = await apiClient.get<ConversationThread[]>(`/spaces/${spaceId}/threads`);
        return response.data;
    },

    createThread: async (spaceId: string, topic: string) => {
        const response = await apiClient.post<ConversationThread>(`/spaces/${spaceId}/threads`, { topic });
        return response.data;
    },
    getSpaceMembers: async (spaceId: string) => {
        const response = await apiClient.get<User[]>(`/spaces/${spaceId}/members`);
        return response.data;
    },

    inviteSpaceMember: async (spaceId: string, email: string, role: string) => {
        const response = await apiClient.post(`/spaces/${spaceId}/members`, { email, role });
        return response.data;
    },

    updateSpaceMemberRole: async (spaceId: string, userId: string, role: string) => {
        const response = await apiClient.patch(`/spaces/${spaceId}/members/${userId}`, { role });
        return response.data;
    },

    removeSpaceMember: async (spaceId: string, userId: string) => {
        const response = await apiClient.delete(`/spaces/${spaceId}/members/${userId}`);
        return response.data;
    },

    getThemeClaims: async (themeId: string) => {
        const response = await apiClient.get<Claim[]>(`/themes/${themeId}/claims`);
        return response.data;
    },

    getThemeFactors: async (themeId: string) => {
        const response = await apiClient.get<Factor[]>(`/themes/${themeId}/factors`);
        return response.data;
    },

    // Manual Editing
    createFactor: async (themeId: string, name: string, description?: string, type: FactorType = 'systeemelement') => {
        const response = await apiClient.post('/factors', { theme_id: themeId, name, description, type });
        return response.data;
    },

    updateFactor: async (id: string, name?: string, description?: string, type?: FactorType, themeId?: string) => {
        const response = await apiClient.patch(`/factors/${id}`, { name, description, type, theme_id: themeId });
        return response.data;
    },

    deleteFactor: async (id: string) => {
        const response = await apiClient.delete(`/factors/${id}`);
        return response.data;
    },

    createClaim: async (data: {
        theme_id: string;
        source_id: string;
        target_id: string;
        statement: string;
        polarity?: string;
        confidence?: number;
    }) => {
        const response = await apiClient.post('/claims_manual', data);
        return response.data;
    },

    updateClaim: async (id: string, data: {
        statement?: string;
        polarity?: string;
        confidence?: number;
        source_id?: string;
        target_id?: string;
    }) => {
        const response = await apiClient.patch(`/claims/${id}`, data);
        return response.data;
    },

    deleteClaim: async (id: string) => {
        const response = await apiClient.delete(`/claims/${id}`);
        return response.data;
    },

    // Dashboard
    getDashboardEnvironments: async () => {
        const response = await apiClient.get<DashboardEnvironment[]>('/dashboard/environments');
        return response.data;
    },

    getDashboardThemes: async () => {
        const response = await apiClient.get<DashboardTheme[]>('/dashboard/themes');
        return response.data;
    },

    // Proposals
    createProposal: async (data: {
        title: string;
        description?: string;
        type?: string;
        target_id?: string;
        author_id: string;
    }) => {
        // Backend expects CreateProposalRequest body
        const response = await apiClient.post('/proposals/', data);
        return response.data;
    },

    // ... existing interfaces ...

    getProposals: async (status?: string, author?: string) => {
        const response = await apiClient.get<Proposal[]>('/proposals/', {
            params: { status, author }
        });
        return response.data;
    }
};

export type LifecycleStatus = 'draft' | 'proposed' | 'accepted' | 'rejected' | 'deprecated';

export interface Proposal {
    id: string;
    title: string;
    description?: string;
    status: LifecycleStatus;
    author_id: string;
    created_at: string;
    type?: string;
    target_id?: string;
}
