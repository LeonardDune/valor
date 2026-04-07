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
export type ClaimViewType = 'AsIsType' | 'ToBeType';

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
    gdi_flag?: string;
}

export interface ValidationResult {
    allowed: boolean;
    type: 'success' | 'warning' | 'error';
    message: string;
}

export interface EntityRegistryEntry {
    uri: string;
    label?: string;
    entity_type?: string;
    entity_type_local?: string;
    supabase_id?: string;
}

export interface SociaOntologyEntry {
    uri: string;
    local_name: string;
    label_en: string;
    label_nl: string;
}

export interface SociaOntology {
    actor_types: SociaOntologyEntry[];
    claim_types: SociaOntologyEntry[];
    roles: SociaOntologyEntry[];
    dependency_types: SociaOntologyEntry[];
}

// AXIA schema (ontologie-gedreven, geladen bij perspectief-initialisatie)
export interface AxiaOntologyEntry {
    uri: string;
    local_name: string;
    label_en: string;
    label_nl: string;
}

export interface AxiaEpistemicStatus {
    uri: string;
    label_en: string;
    label_nl: string;
    allowed_transitions: string[];
    requires_decision_episode: boolean;
}

export interface AxiaSchema {
    value_types: AxiaOntologyEntry[];
    claim_polarities: AxiaOntologyEntry[];
    epistemic_statuses: AxiaEpistemicStatus[];
    uncertainty_levels: AxiaOntologyEntry[];
}

export interface StakeholderActor {
    uri: string;
    label: string;
    entity_type: string;
    entity_type_local: string;
    role_uri: string | null;
    role_label_nl: string | null;
}

export interface StakeholderDependency {
    from_uri: string;
    to_uri: string;
    dependency_type: string;
    dependency_type_local: string;
    dependency_label_nl: string;
}

export interface StakeholderMap {
    actors: StakeholderActor[];
    dependencies: StakeholderDependency[];
}

export interface CreateActorRequest {
    label: string;
    actor_type_uri: string;  // Volledige URI uit VALOR-O SOCIA-ontologie
}

export interface CreateActorResponse {
    actor_id: string;
    actor_uri: string;
    label: string;
    actor_type_uri: string;
    claimed_by: string;
    claimed_at: string;
    design_space_id: string;
}

export interface UpdateActorRequest {
    label?: string;
    actor_type_uri?: string;
}

export interface CreateStakeholderClaimRequest {
    claim_type_uri: string;  // Volledige URI uit VALOR-O SOCIA-ontologie
    claim_content: string;
    actor_uri: string;
}

export interface StakeholderClaimResponse {
    tessera_id: string;
    tessera_uri: string;
    claim_type_uri: string;
    claim_content: string;
    epistemic_status: string;
    actor_uri: string;
    claimed_by: string;
    claimed_at: string;
    design_space_id: string;
}

export interface CreateEcosystemAgentRequest {
    label: string;
    commitment_duration_uri: string;  // Volledige URI uit VALOR-O NEXUS-ontologie
    member_agent_uris: string[];
}

export interface EcosystemAgentConditionLayers {
    commitment: boolean;
    architecture: boolean;
    disposition_config: boolean;
}

export interface EcosystemAgent {
    agent_uri: string;
    label: string;
    commitment_uri: string | null;
    commitment_duration_uri: string | null;
    member_agent_uris: string[];
    condition_status: 'Volledig' | 'Gedeeltelijk' | 'Onvolledig';
    condition_layers: EcosystemAgentConditionLayers;
}

export interface CreateEcosystemAgentResponse {
    agent_id: string;
    agent_uri: string;
    label: string;
    commitment_uri: string;
    commitment_duration_uri: string;
    member_agent_uris: string[];
    created_by: string;
    created_at: string;
    design_space_id: string;
}

// StakeholderGroepen (US-6.5)
export interface CreateStakeholderGroupRequest {
    label: string;
    interest_level_uri: string;  // Volledige URI uit VALOR-O DEMOS-ontologie
    represented_by_uri?: string;
}

export interface StakeholderGroup {
    group_uri: string;
    label: string;
    interest_level_uri: string;
    is_represented: boolean;
    represented_by_uri: string | null;
}

export interface CreateStakeholderGroupResponse {
    group_id: string;
    group_uri: string;
    label: string;
    interest_level_uri: string;
    represented_by_uri: string | null;
    is_represented: boolean;
    created_by: string;
    created_at: string;
    design_space_id: string;
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
    tessera_base_id: string;
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
    gdi_flag?: string;
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

    getThemeClaims: async (dsId: string, claimType?: ClaimViewType) => {
        const params = claimType ? { claim_type: claimType } : undefined;
        const response = await apiClient.get<Claim[]>(`/designspace/${dsId}/claims`, { params });
        return response.data;
    },

    detectCycles: async (dsId: string): Promise<string[]> => {
        const response = await apiClient.get<{ cycle_node_ids: string[] }>(`/designspace/${dsId}/cycles`);
        return response.data.cycle_node_ids;
    },

    getThemeVersionClaims: async (dsId: string, phase?: string) => {
        const params = phase ? { phase } : {};
        const response = await apiClient.get<Claim[]>(`/designspace/${dsId}/claims`, { params });
        return response.data;
    },

    getThemeFactors: async (dsId: string, phase?: string) => {
        const params = phase ? { phase } : {};
        const response = await apiClient.get<Factor[]>(`/designspace/${dsId}/factors`, { params });
        return response.data;
    },

    getThemeVersionFactors: async (dsId: string, phase?: string) => {
        const params = phase ? { phase } : {};
        const response = await apiClient.get<Factor[]>(`/designspace/${dsId}/factors`, { params });
        return response.data;
    },

    getPhaseSnapshots: async (dsId: string): Promise<PhaseSnapshot[]> => {
        const response = await apiClient.get<PhaseSnapshot[]>(`/designspace/${dsId}/phase-snapshots`);
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
        manifestation_condition?: string;
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
    getAsisCoverage: async (dsId: string): Promise<{ claim_id: string; coverage: 'Full' | 'Partial' | 'None' }[]> => {
        const response = await apiClient.get(`/designspace/${dsId}/coverage`);
        return response.data;
    },

    getConditionCoverage: async (dsId: string, altId: string): Promise<{ claim_id: string; coverage: 'Full' | 'Partial' | 'None' }[]> => {
        const response = await apiClient.get(`/designspace/${dsId}/alternative/${altId}/coverage`);
        return response.data;
    },

    createClaimCoverageAssessment: async (dsId: string, altId: string): Promise<{ assessment_id: string; assessment_uri: string; outcome: string }> => {
        const response = await apiClient.post(`/designspace/${dsId}/alternative/${altId}/assessment/coverage`);
        return response.data;
    },

    getProvenance: async (dsId: string): Promise<{ activity_uri: string; operation_type: string; attributed_to: string; started_at: string; generated?: string; used: string[] }[]> => {
        const response = await apiClient.get(`/designspace/${dsId}/provenance`);
        return response.data;
    },

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

    getSociaOntology: async (): Promise<SociaOntology> => {
        const response = await apiClient.get<SociaOntology>('/ontology/socia');
        return response.data;
    },

    getAxiaSchema: async (): Promise<AxiaSchema> => {
        const response = await apiClient.get<AxiaSchema>('/ontology/axia');
        return response.data;
    },

    // Entity Registry
    searchEntities: async (q: string, entityType?: string, limit = 20): Promise<EntityRegistryEntry[]> => {
        const params: Record<string, string | number> = { q, limit };
        if (entityType) params.type = entityType;
        const response = await apiClient.get<EntityRegistryEntry[]>('/entities/search', { params });
        return response.data;
    },

    createEntity: async (data: { entity_type: string; label: string; properties?: Record<string, string>; identifier?: string }): Promise<EntityRegistryEntry> => {
        const response = await apiClient.post<EntityRegistryEntry>('/entities/', data);
        return response.data;
    },

    assignSociaRole: async (dsId: string, entityUri: string, roleUri: string): Promise<void> => {
        await apiClient.post(`/designspace/${dsId}/socia/roles`, null, {
            params: { entity_uri: entityUri, role_uri: roleUri },
        });
    },

    getStakeholderMap: async (dsId: string): Promise<StakeholderMap> => {
        const response = await apiClient.get<StakeholderMap>(`/designspace/${dsId}/stakeholder-map`);
        return response.data;
    },

    createActor: async (dsId: string, data: CreateActorRequest): Promise<CreateActorResponse> => {
        const response = await apiClient.post<CreateActorResponse>(`/designspace/${dsId}/actor`, data);
        return response.data;
    },

    updateActor: async (dsId: string, actorUri: string, data: UpdateActorRequest): Promise<void> => {
        await apiClient.patch(`/designspace/${dsId}/actor/${encodeURIComponent(actorUri)}`, data);
    },

    deleteActor: async (dsId: string, actorUri: string): Promise<void> => {
        await apiClient.delete(`/designspace/${dsId}/actor/${encodeURIComponent(actorUri)}`);
    },

    createStakeholderClaim: async (
        dsId: string,
        data: CreateStakeholderClaimRequest,
    ): Promise<StakeholderClaimResponse> => {
        const response = await apiClient.post<StakeholderClaimResponse>(
            `/designspace/${dsId}/stakeholder-claims`,
            data,
        );
        return response.data;
    },

    // EcosystemAgents (US-6.4)
    createEcosystemAgent: async (
        dsId: string,
        data: CreateEcosystemAgentRequest,
    ): Promise<CreateEcosystemAgentResponse> => {
        const response = await apiClient.post<CreateEcosystemAgentResponse>(
            `/designspace/${dsId}/ecosystem-agent`,
            data,
        );
        return response.data;
    },

    getEcosystemAgents: async (dsId: string): Promise<EcosystemAgent[]> => {
        const response = await apiClient.get<EcosystemAgent[]>(`/designspace/${dsId}/ecosystem-agents`);
        return response.data;
    },

    // StakeholderGroepen (US-6.5)
    createStakeholderGroup: async (
        dsId: string,
        data: CreateStakeholderGroupRequest,
    ): Promise<CreateStakeholderGroupResponse> => {
        const response = await apiClient.post<CreateStakeholderGroupResponse>(
            `/designspace/${dsId}/stakeholder-group`,
            data,
        );
        return response.data;
    },

    getStakeholderGroups: async (dsId: string): Promise<StakeholderGroup[]> => {
        const response = await apiClient.get<StakeholderGroup[]>(`/designspace/${dsId}/stakeholder-groups`);
        return response.data;
    },

    getHighInterestGroups: async (dsId: string): Promise<StakeholderGroup[]> => {
        const response = await apiClient.get<StakeholderGroup[]>(`/designspace/${dsId}/stakeholder-groups/high-interest`);
        return response.data;
    },

    // Threads (Fuseki-backed disc endpoints, Epic 16)
    getDesignSpaceMembers: async (dsId: string): Promise<{ id: string; name: string; email: string; role: string }[]> => {
        const response = await apiClient.get(`/designspace/${dsId}/members`);
        return response.data;
    },

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

    // DecisionTimeline (US-5.4)
    getDecisionTimeline: async (dsId: string): Promise<DecisionEpisodeRaw[]> => {
        const query = `
PREFIX valor: <https://valor-ecosystem.nl/ontology/>
PREFIX prov: <https://www.w3.org/ns/prov#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?episode ?type ?phase ?startedAt ?startedBy ?vote ?voteType ?castBy ?onTessera WHERE {
  ?episode a ?type .
  FILTER(?type IN (valor:DecisionEpisode, valor:PhaseTransition))
  OPTIONAL { ?episode valor:forPhase ?phase }
  OPTIONAL { ?episode prov:startedAtTime ?startedAt }
  OPTIONAL { ?episode prov:wasStartedBy ?startedBy }
  OPTIONAL {
    ?episode valor:hasVote ?vote .
    ?vote valor:voteType ?voteType ;
          valor:castBy ?castBy .
    OPTIONAL { ?vote valor:onTessera ?onTessera }
  }
}
ORDER BY DESC(?startedAt)`.trim();
        const response = await apiClient.get<DecisionTimelineRaw>(
            `/designspace/${dsId}/sparql`,
            { params: { query } }
        );
        return parseDecisionTimeline(response.data);
    },

    // Argue-relatietypes uit de ontologie — US-5.1
    getArgueTypes: async (): Promise<ArgueType[]> => {
        const response = await apiClient.get<ArgueType[]>('/tessera/argue-types');
        return response.data;
    },

    // Alle Factor-tesserae in een DesignSpace (zonder CausalClaims) — US-5.1
    getDesignSpaceTesserae: async (dsId: string): Promise<TesseraNode[]> => {
        const VALOR_NS = 'https://valor-ecosystem.nl/ontology/';
        const query = `
PREFIX valor: <${VALOR_NS}>
SELECT ?node ?content ?status ?type WHERE {
  ?node a valor:Tessera ;
        valor:claimContent ?content ;
        valor:epistemicStatus ?status .
  OPTIONAL { ?node valor:claimType ?type . }
  FILTER NOT EXISTS { ?node valor:fromFactor ?any }
}`.trim();
        const response = await apiClient.get<{ results: { bindings: Array<{ node: { value: string }; content: { value: string }; status: { value: string }; type?: { value: string } }> } }>(
            `/designspace/${dsId}/sparql`,
            { params: { query } }
        );
        return response.data.results.bindings.map(b => {
            const uri = b.node.value;
            const id = uri.split(':').pop() ?? uri;
            return {
                id,
                uri,
                claimContent: b.content.value,
                epistemicStatus: b.status.value.split('/').pop()?.split('#').pop() ?? b.status.value,
                claimType: b.type ? (b.type.value.split('/').pop() ?? 'AsIs') : 'AsIs',
            };
        });
    },

    // Argumentatiediagram — CAUSA: Factors als nodes, CausalClaims als edges — US-5.1
    // Structuur conform VALOR-O 00h-causa.trig:
    //   causa:CausalClaim subclasseert valor:Tessera en heeft valor:fromFactor / valor:toFactor / valor:polarity.
    //   Elke perspectief-module heeft eigen domein-predicaten; dit patroon geldt voor CAUSA.
    //   De valor:supports/undermines/qualifies/presupposes predicaten (00j-tessera §E) zijn de
    //   cross-perspectief epistemische overlay — een apart laag bovenop de domeinstructuur.
    getArgumentationNetwork: async (dsId: string): Promise<ArgumentationNetwork> => {
        const VALOR_NS = 'https://valor-ecosystem.nl/ontology/';
        const query = `
PREFIX valor: <${VALOR_NS}>
SELECT ?claim ?claimContent ?claimStatus ?polarity ?source ?sourceContent ?sourceStatus ?target ?targetContent ?targetStatus
WHERE {
  ?claim a valor:Tessera ;
         valor:claimContent ?claimContent ;
         valor:epistemicStatus ?claimStatus ;
         valor:fromFactor ?source ;
         valor:toFactor ?target ;
         valor:polarity ?polarity .
  ?source a valor:Tessera ;
          valor:claimContent ?sourceContent ;
          valor:epistemicStatus ?sourceStatus .
  ?target a valor:Tessera ;
          valor:claimContent ?targetContent ;
          valor:epistemicStatus ?targetStatus .
}`.trim();
        const response = await apiClient.get<CausalNetworkRaw>(
            `/designspace/${dsId}/sparql`,
            { params: { query } }
        );
        return parseCausalNetwork(response.data);
    },

    advanceSession: async (sessionId: string) => {
        const response = await apiClient.post(`/sessions/${sessionId}/advance`);
        return response.data;
    },

    completePhase: async (sessionId: string, phase: 'refine' | 'ranking' | 'consent') => {
        const response = await apiClient.post(`/sessions/${sessionId}/complete-phase`, { phase });
        return response.data;
    },

    // Axia
    getValueClaims: async (dsId: string): Promise<ValueCanvasResponse> => {
        const response = await apiClient.get<ValueCanvasResponse>(`/designspace/${dsId}/value-claims`);
        return response.data;
    },

    createValueClaim: async (dsId: string, payload: CreateValueClaimPayload): Promise<ValueClaimCreatedResponse> => {
        const response = await apiClient.post<ValueClaimCreatedResponse>(`/designspace/${dsId}/value-claim`, payload);
        return response.data;
    },

    updateValueClaim: async (dsId: string, tesseraUri: string, payload: UpdateValueClaimPayload): Promise<void> => {
        await apiClient.patch(`/designspace/${dsId}/value-claim/${encodeURIComponent(tesseraUri)}`, payload);
    },

    deleteValueClaim: async (dsId: string, tesseraUri: string): Promise<void> => {
        await apiClient.delete(`/designspace/${dsId}/value-claim/${encodeURIComponent(tesseraUri)}`);
    },

    updateValueClaimPosition: async (dsId: string, tesseraUri: string, canvas_x: number, canvas_y: number): Promise<void> => {
        await apiClient.patch(`/designspace/${dsId}/value-claim/${encodeURIComponent(tesseraUri)}/position`, { canvas_x, canvas_y });
    },

    createValueTension: async (dsId: string, payload: CreateValueTensionPayload): Promise<ValueTensionResponse> => {
        const response = await apiClient.post<ValueTensionResponse>(`/designspace/${dsId}/value-tension`, payload);
        return response.data;
    },

    getValueImplications: async (dsId: string): Promise<DesignImplicationCount[]> => {
        const response = await apiClient.get<DesignImplicationCount[]>(`/designspace/${dsId}/value-implications`);
        return response.data;
    },

    createValueCriterion: async (dsId: string, payload: CreateValueCriterionPayload): Promise<ValueCriterionResponse> => {
        const response = await apiClient.post<ValueCriterionResponse>(`/designspace/${dsId}/value-criterion`, payload);
        return response.data;
    },

    createValueBasedDesignRequirement: async (dsId: string, payload: CreateValueBasedDesignRequirementPayload): Promise<ValueBasedDesignRequirementResponse> => {
        const response = await apiClient.post<ValueBasedDesignRequirementResponse>(`/designspace/${dsId}/value-based-design-requirement`, payload);
        return response.data;
    },

    getValueChain: async (dsId: string): Promise<ValueChainResponse> => {
        const response = await apiClient.get<ValueChainResponse>(`/designspace/${dsId}/value-chain`);
        return response.data;
    },

    patchValueRequirementStatus: async (dsId: string, reqUri: string, newStatus: string): Promise<PatchValueRequirementStatusResponse> => {
        const response = await apiClient.patch<PatchValueRequirementStatusResponse>(
            `/designspace/${dsId}/value-requirement/${encodeURIComponent(reqUri)}/status`,
            { new_status: newStatus },
        );
        return response.data;
    },

    getCapabilityRequirements: async (dsId: string): Promise<CapabilityRequirementItem[]> => {
        const response = await apiClient.get<CapabilityRequirementItem[]>(`/designspace/${dsId}/capability-requirements`);
        return response.data;
    },
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

// Argumentatiediagram types (US-5.1)
export type ArgueRelationType = string;

export interface ArgueType {
    uri: string;
    label_en: string;
    label_nl: string;
}

export interface TesseraNode {
    id: string;
    uri: string;
    claimContent: string;
    epistemicStatus: string;
    claimType: string;
}

export interface ArgumentEdge {
    sourceId: string;
    targetId: string;
    relationType: ArgueRelationType;
    relationUri: string;
    relationLabel: string;
}

export interface ArgumentationNetwork {
    nodes: TesseraNode[];
    edges: ArgumentEdge[];
}

interface SparqlBinding {
    type: string;
    value: string;
    'xml:lang'?: string;
}

// CAUSA-specifiek: CausalClaim-Tesserae als edges tussen Factor-Tesserae
interface CausalNetworkRaw {
    results: {
        bindings: Array<{
            claim: SparqlBinding;
            claimContent: SparqlBinding;
            claimStatus: SparqlBinding;
            polarity: SparqlBinding;
            source: SparqlBinding;
            sourceContent: SparqlBinding;
            sourceStatus: SparqlBinding;
            target: SparqlBinding;
            targetContent: SparqlBinding;
            targetStatus: SparqlBinding;
        }>;
    };
}

function parseCausalNetwork(raw: CausalNetworkRaw): ArgumentationNetwork {
    const nodesMap = new Map<string, TesseraNode>();
    const edges: ArgumentEdge[] = [];

    for (const b of raw.results.bindings) {
        const sourceUri = b.source.value;
        const sourceId = sourceUri.split(':').pop() ?? sourceUri;
        const targetUri = b.target.value;
        const targetId = targetUri.split(':').pop() ?? targetUri;

        if (!nodesMap.has(sourceId)) {
            nodesMap.set(sourceId, {
                id: sourceId,
                uri: sourceUri,
                claimContent: b.sourceContent.value,
                epistemicStatus: b.sourceStatus.value.split('/').pop()?.split('#').pop() ?? b.sourceStatus.value,
                claimType: 'AsIs',
            });
        }
        if (!nodesMap.has(targetId)) {
            nodesMap.set(targetId, {
                id: targetId,
                uri: targetUri,
                claimContent: b.targetContent.value,
                epistemicStatus: b.targetStatus.value.split('/').pop()?.split('#').pop() ?? b.targetStatus.value,
                claimType: 'AsIs',
            });
        }

        const polarity = b.polarity.value;
        const label = b.claimContent.value.length > 45
            ? b.claimContent.value.slice(0, 45) + '…'
            : b.claimContent.value;

        edges.push({
            sourceId,
            targetId,
            relationType: polarity,
            relationUri: polarity,
            relationLabel: label,
        });
    }

    return { nodes: Array.from(nodesMap.values()), edges };
}

// PhaseSnapshot types
export interface PhaseSnapshot {
    session_id: string;
    graph_uri: string;
    created_at: string;
    accepted_count: number;
    rejected_count: number;
}

// DecisionTimeline types (US-5.4)
export interface DecisionVote {
    voteUri: string;
    voteType: string;
    castBy: string;
    onTessera: string | null;
}

export interface DecisionEpisodeRaw {
    episodeUri: string;
    type: 'DecisionEpisode' | 'PhaseTransition';
    phase: string | null;
    startedAt: string | null;
    startedBy: string | null;
    votes: DecisionVote[];
}

interface DecisionTimelineSparqlBinding {
    episode: SparqlBinding;
    type: SparqlBinding;
    phase?: SparqlBinding;
    startedAt?: SparqlBinding;
    startedBy?: SparqlBinding;
    vote?: SparqlBinding;
    voteType?: SparqlBinding;
    castBy?: SparqlBinding;
    onTessera?: SparqlBinding;
}

interface DecisionTimelineRaw {
    results: {
        bindings: DecisionTimelineSparqlBinding[];
    };
}

function parseDecisionTimeline(raw: DecisionTimelineRaw): DecisionEpisodeRaw[] {
    const episodesMap = new Map<string, DecisionEpisodeRaw>();

    for (const b of raw.results.bindings) {
        const episodeUri = b.episode.value;
        const typeFragment = b.type.value.split('/').pop()?.split('#').pop() ?? 'DecisionEpisode';
        const episodeType: 'DecisionEpisode' | 'PhaseTransition' =
            typeFragment === 'PhaseTransition' ? 'PhaseTransition' : 'DecisionEpisode';

        if (!episodesMap.has(episodeUri)) {
            episodesMap.set(episodeUri, {
                episodeUri,
                type: episodeType,
                phase: b.phase ? (b.phase.value.split('/').pop() ?? b.phase.value) : null,
                startedAt: b.startedAt?.value ?? null,
                startedBy: b.startedBy?.value ?? null,
                votes: [],
            });
        }

        const episode = episodesMap.get(episodeUri)!;
        if (b.vote && b.voteType && b.castBy) {
            const voteUri = b.vote.value;
            const alreadyAdded = episode.votes.some(v => v.voteUri === voteUri);
            if (!alreadyAdded) {
                episode.votes.push({
                    voteUri,
                    voteType: b.voteType.value.split('/').pop() ?? b.voteType.value,
                    castBy: b.castBy.value,
                    onTessera: b.onTessera?.value ?? null,
                });
            }
        }
    }

    return Array.from(episodesMap.values());
}

// Axia interfaces
export interface ValueClaimItem {
    tessera_uri: string;
    tessera_id: string;
    claim_content: string;
    value_type_uri: string;
    value_type_label: string;
    polarity_uri?: string;
    polarity_label?: string;
    epistemic_status?: string;
    canvas_x?: number;
    canvas_y?: number;
    claimed_by: string;
    claimed_at: string;
}

export interface ValueCanvasResponse {
    design_space_id: string;
    groups: Record<string, ValueClaimItem[]>;
}

export interface CreateValueTensionPayload {
    value_type_a_uri: string;
    value_type_b_uri: string;
    description: string;
}

export interface ValueTensionResponse {
    tessera_uri: string;
    tessera_id: string;
    value_type_a_uri: string;
    value_type_b_uri: string;
    description: string;
    created_by: string;
    created_at: string;
}

export interface DesignImplicationCount {
    factor_uri: string;
    implication_count: number;
}

export interface CreateValueClaimPayload {
    claim_content: string;
    value_type_uri?: string;
    claim_polarity_uri?: string;
}

export interface ValueClaimCreatedResponse {
    tessera_uri: string;
    tessera_id: string;
    claim_content: string;
    value_type_uri: string | null;
    claimed_by: string;
    claimed_at: string;
}

export interface UpdateValueClaimPayload {
    claim_content?: string;
    value_type_uri?: string;
}

export interface CreateValueCriterionPayload {
    label: string;
    value_type_uri: string;
    grounded_in_norm_uri?: string;
}

export interface ValueCriterionResponse {
    tessera_uri: string;
    tessera_id: string;
    label: string;
    value_type_uri: string;
    grounded_in_norm_uri: string | null;
    created_by: string;
    created_at: string;
}

export interface CreateValueBasedDesignRequirementPayload {
    label: string;
    criterion_uri: string;
}

export interface ValueBasedDesignRequirementResponse {
    tessera_uri: string;
    tessera_id: string;
    label: string;
    criterion_uri: string;
    created_by: string;
    created_at: string;
}

export interface ValueChainRequirementItem {
    tessera_uri: string;
    tessera_id: string;
    label: string;
    epistemic_status?: string;
    capability_requirement_uri?: string;
}

export interface ValueChainCriterionItem {
    tessera_uri: string;
    tessera_id: string;
    label: string;
    requirements: ValueChainRequirementItem[];
}

export interface ValueChainTypeItem {
    value_type_uri: string;
    value_type_label: string;
    criteria: ValueChainCriterionItem[];
}

export interface ValueChainResponse {
    design_space_id: string;
    chain: ValueChainTypeItem[];
}

export interface CapabilityRequirementItem {
    tessera_uri: string;
    tessera_id: string;
    label: string;
    generated_from: string;
    epistemic_status: string;
    created_by: string;
    created_at: string;
}

export interface PatchValueRequirementStatusResponse {
    tessera_uri: string;
    tessera_id: string;
    previous_status: string;
    new_status: string;
    capability_requirement: CapabilityRequirementItem | null;
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
