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

export interface ConversationResponse {
    conversation_id: string;
    reply: string;
    extracted_claims: Claim[];
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
}

export interface User {
    id: string;
    email: string;
    name?: string;
    first_name?: string;
    last_name?: string;
    username?: string;
    role?: string;
    joined_at?: string;
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

    createUser: async (email: string, name?: string) => {
        const response = await apiClient.post('/users', { email, name });
        return response.data;
    },

    updateUserProfile: async (firstName: string, lastName: string, username: string) => {
        const response = await apiClient.put('/users/me', { first_name: firstName, last_name: lastName, username });
        return response.data;
    },


    getOrganizationUsers: async (orgId: string) => {
        const response = await apiClient.get<User[]>(`/organizations/${orgId}/users`);
        return response.data;
    },

    addOrganizationUser: async (orgId: string, email: string, role: string = 'member') => {
        const response = await apiClient.post(`/organizations/${orgId}/users`, { email, role });
        return response.data;
    },

    updateOrgMember: async (orgId: string, userId: string, role: string) => {
        const response = await apiClient.put(`/organizations/${orgId}/users/${userId}`, { role });
        return response.data;
    },

    removeOrgMember: async (orgId: string, userId: string) => {
        const response = await apiClient.delete(`/organizations/${orgId}/users/${userId}`);
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
    }
};
