import axios from 'axios';
import { supabase } from '../lib/supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
export const apiClient = axios.create({
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
            // await supabase.auth.signOut();
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
    version_id?: string;
    claim_thread_id?: string;
    source_thread_id?: string;
    target_thread_id?: string;
    status?: string;
    evidence_text?: string;
    evidence_url?: string;
    claim_type?: string;
}

export interface ValidationResult {
    allowed: boolean;
    type: 'success' | 'warning' | 'error';
    message: string;
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

export type ShortlistStatus = 'positive' | 'contested' | 'rejected';

export interface ShortlistClaim extends Claim {
    status: ShortlistStatus;
    high_p: number;
    combined_p: number;
    discard_p: number;
    user_vote?: ConsentVoteType;
    user_motivation?: string;
}

export type ConsentVoteType = 'approve' | 'object';

export interface ConsentVotePayload {
    session_id: string;
    claim_version_id: string;
    vote: ConsentVoteType;
    motivation?: string;
}

export interface Factor {
    id: string;
    name: string;
    description: string;
    type: FactorType;
    version_id?: string;
    thread_id?: string;
    epistemic_status?: string;
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
    ds_id?: string;
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
    type: 'THEME' | 'ISSUE';
}

export interface DashboardProject {
    id: string;
    name: string;
    description?: string;
    role?: string;
    status?: string;
    type: 'PROJECT';
    themes: DashboardTheme[];  // backward compat alias voor issues
    issues?: DashboardTheme[]; // nieuwe veld van backend
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

export interface ThemeVersion {
    id: string;
    name: string;
    description: string;
    issue_id?: string;
    role?: string;
    status?: string;
    current_phase?: string;
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
    status: 'open' | 'closed' | 'archived' | 'active';
    created_at: string;
    target_id?: string;
    message_count?: number;
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

    getThemeUsers: async (dsId: string) => {
        const response = await apiClient.get<User[]>(`/designspace/${dsId}/members`);
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

    updateThemeMember: async (dsId: string, userId: string, role: string, _name?: string, _status?: string) => {
        const response = await apiClient.patch(`/designspace/${dsId}/members/${userId}`, { role });
        return response.data;
    },

    removeThemeMember: async (dsId: string, userId: string) => {
        const response = await apiClient.delete(`/designspace/${dsId}/members/${userId}`);
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
        if (entityType === 'theme') endpoint = `/designspace/${entityId}/invites`;

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
        const response = await apiClient.get<{ issue_id: string; ds_id: string; name: string; description: string; role?: string; status?: string; current_phase?: string }[]>(`/projects/${projectId}/issues`);
        return response.data.map(item => ({
            id: item.ds_id,
            ds_id: item.ds_id,
            issue_id: item.issue_id,
            name: item.name,
            description: item.description,
            role: item.role,
            status: item.status,
            current_phase: item.current_phase,
            project_id: projectId,
        })) as Theme[];
    },

    createTheme: async (projectId: string, name: string, description?: string) => {
        const response = await apiClient.post(`/projects/${projectId}/issues`, { name, description });
        return response.data;
    },

    updateTheme: async (dsId: string, name?: string, description?: string) => {
        const response = await apiClient.patch(`/designspace/${dsId}`, { name, description });
        return response.data;
    },

    archiveTheme: async (dsId: string) => {
        const response = await apiClient.delete(`/designspace/${dsId}`);
        return response.data;
    },

    // Theme Versions (nu DesignSpace)
    getThemeVersions: async (dsId: string) => {
        const response = await apiClient.get<any>(`/designspace/${dsId}`);
        const data = response.data;
        const version: ThemeVersion = { ...data, id: data.ds_id || data.id || dsId };
        return [version];
    },

    getThemeActiveVersion: async (dsId: string) => {
        const response = await apiClient.get<any>(`/designspace/${dsId}`);
        const data = response.data;
        return { ...data, id: data.ds_id || data.id || dsId } as ThemeVersion;
    },

    getThemeVersion: async (dsId: string) => {
        const response = await apiClient.get<any>(`/designspace/${dsId}`);
        const data = response.data;
        return { ...data, id: data.ds_id || data.id || dsId } as ThemeVersion;
    },

    createThemeVersion: async (_themeId: string, _name: string, _description?: string) => {
        // Niet meer ondersteund — DesignSpaces worden aangemaakt via createTheme
        return null;
    },

    updateThemeVersion: async (dsId: string, name?: string, description?: string) => {
        const response = await apiClient.patch(`/designspace/${dsId}`, { name, description });
        return response.data;
    },

    archiveThemeVersion: async (dsId: string) => {
        const response = await apiClient.delete(`/designspace/${dsId}`);
        return response.data;
    },

    getVersionThreads: async (dsId: string) => {
        const response = await apiClient.get<ConversationThread[]>(`/designspace/${dsId}/threads`);
        return response.data;
    },

    createVersionThread: async (dsId: string, topic: string) => {
        const response = await apiClient.post<ConversationThread>(`/designspace/${dsId}/threads`, { topic });
        return response.data;
    },

    getVersionMembers: async (dsId: string) => {
        const response = await apiClient.get<User[]>(`/designspace/${dsId}/members`);
        return response.data;
    },

    inviteVersionMember: async (dsId: string, email: string, role: string) => {
        const response = await apiClient.post(`/designspace/${dsId}/members`, { email, role });
        return response.data;
    },

    updateVersionMemberRole: async (dsId: string, userId: string, role: string) => {
        const response = await apiClient.patch(`/designspace/${dsId}/members/${userId}`, { role });
        return response.data;
    },

    removeVersionMember: async (dsId: string, userId: string) => {
        const response = await apiClient.delete(`/designspace/${dsId}/members/${userId}`);
        return response.data;
    },

    getThemeClaims: async (dsId: string) => {
        const response = await apiClient.get<Claim[]>(`/designspace/${dsId}/claims`);
        return response.data;
    },

    getThemeVersionClaims: async (dsId: string) => {
        const response = await apiClient.get<Claim[]>(`/designspace/${dsId}/claims`);
        return response.data;
    },

    getThemeFactors: async (dsId: string) => {
        const response = await apiClient.get<Factor[]>(`/designspace/${dsId}/factors`);
        return response.data;
    },

    getThemeVersionFactors: async (dsId: string) => {
        const response = await apiClient.get<Factor[]>(`/designspace/${dsId}/factors`);
        return response.data;
    },

    // Manual Editing
    createFactor: async (dsId: string, name: string, description?: string, type: FactorType = 'systeemelement') => {
        const response = await apiClient.post('/factors', { ds_id: dsId, name, description, type });
        return response.data;
    },

    updateFactor: async (id: string, name?: string, description?: string, type?: FactorType) => {
        const response = await apiClient.patch(`/factors/${id}`, { name, description, type });
        return response.data;
    },

    deleteFactor: async (id: string) => {
        const response = await apiClient.delete(`/factors/${id}`);
        return response.data;
    },

    createClaim: async (data: {
        ds_id: string;
        source_id: string;
        target_id: string;
        statement: string;
        polarity?: string;
        confidence?: number;
        evidence_text?: string;
        evidence_url?: string;
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
        evidence_text?: string;
        evidence_url?: string;
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
        // Normaliseer: backend geeft `issues` terug, frontend gebruikt `themes` als alias
        return response.data.map(org => ({
            ...org,
            projects: org.projects.map(proj => ({
                ...proj,
                themes: proj.issues ?? proj.themes ?? [],
            })),
        }));
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
    },

    // DesignSpace
    getDesignSpacesByProject: async (projectId: string, themeId?: string): Promise<{ id: string; name: string; status: string; current_phase: string }[]> => {
        const response = await apiClient.get(`/designspace/by-project/${projectId}`, {
            params: themeId ? { theme_id: themeId } : undefined,
        });
        return response.data;
    },

    // Ontologie endpoints
    getEpistemicStatuses: async (): Promise<{ uri: string; label_en: string; label_nl: string }[]> => {
        const response = await apiClient.get('/ontology/epistemic-statuses');
        return response.data;
    },

    // Threads (Fuseki-backed disc endpoints, Epic 16)
    getCanResolveThread: async (designSpaceId: string): Promise<{ can_resolve: boolean }> => {
        const response = await apiClient.get<{ can_resolve: boolean }>(`/designspace/${designSpaceId}/can-resolve`);
        return response.data;
    },

    resolveDiscThread: async (
        threadId: string,
        body: { design_space_id: string; resolution_outcome: string; resolution_rationale: string }
    ): Promise<{ resolution_id: string; thread_id: string; tessera_id: string; previous_status: string; new_status: string }> => {
        const response = await apiClient.post(`/threads/${threadId}/resolve`, body);
        return response.data;
    },

    getDiscThreads: async (tesseraId: string, designSpaceId: string): Promise<DiscThread[]> => {
        const response = await apiClient.get<DiscThread[]>('/threads', {
            params: { tessera_id: tesseraId, design_space_id: designSpaceId },
        });
        return response.data;
    },

    createDiscThread: async (tesseraId: string, designSpaceId: string, title?: string): Promise<{ thread_id: string }> => {
        const response = await apiClient.post<{ thread_id: string }>('/threads', {
            tessera_id: tesseraId,
            design_space_id: designSpaceId,
            title: title ?? null,
        });
        return response.data;
    },

    getDiscContributions: async (threadId: string, designSpaceId: string): Promise<DiscContribution[]> => {
        const response = await apiClient.get<DiscContribution[]>(`/threads/${threadId}/contributions`, {
            params: { design_space_id: designSpaceId },
        });
        return response.data;
    },

    createDiscContribution: async (
        threadId: string,
        body: { design_space_id: string; contribution_type: string; message_content: string; evidence_id?: string }
    ): Promise<{ contribution_id: string }> => {
        const response = await apiClient.post<{ contribution_id: string }>(`/threads/${threadId}/contribute`, body);
        return response.data;
    },

    advanceSession: async (sessionId: string) => {
        const response = await apiClient.post(`/sessions/${sessionId}/advance`);
        return response.data;
    },

    completePhase: async (sessionId: string, phase: 'refine' | 'ranking' | 'consent') => {
        const response = await apiClient.post(`/sessions/${sessionId}/complete-phase`, { phase });
        return response.data;
    }
};

export interface ConversationMessage {
    id: string;
    thread_id: string;
    content: string;
    role: 'user' | 'assistant';
    created_at: string;
}

// Disc (Fuseki-backed deliberation threads, Epic 16)
export interface DiscThread {
    thread_id: string;
    thread_uri: string;
    tessera_id: string;
    design_space_id: string;
    started_by: string;
    started_by_name: string;
    started_at: string;
    title: string | null;
}

export interface DiscContribution {
    contribution_id: string;
    contribution_uri: string;
    thread_id: string;
    design_space_id: string;
    contribution_type: string;
    message_content: string;
    contributed_by: string;
    contributed_by_name: string;
    contributed_at: string;
    evidence_id: string | null;
}

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
