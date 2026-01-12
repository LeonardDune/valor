import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

export const api = {
    healthCheck: async () => {
        const response = await axios.get(`${API_URL}/health`);
        return response.data;
    },

    chat: async (message: string, conversationId?: string, topic?: string) => {
        const response = await axios.post<ConversationResponse>(`${API_URL}/chat`, {
            message,
            conversation_id: conversationId,
            topic
        });
        return response.data;
    },

    getThemeClaims: async (themeId: string) => {
        const response = await axios.get<Claim[]>(`${API_URL}/themes/${themeId}/claims`);
        return response.data;
    },

    getThemeFactors: async (themeId: string) => {
        const response = await axios.get<Factor[]>(`${API_URL}/themes/${themeId}/factors`);
        return response.data;
    },

    // Manual Editing
    createFactor: async (themeId: string, name: string, description?: string, type: FactorType = 'systeemelement') => {
        const response = await axios.post(`${API_URL}/factors`, { theme_id: themeId, name, description, type });
        return response.data;
    },

    updateFactor: async (id: string, name?: string, description?: string, type?: FactorType, themeId?: string) => {
        const response = await axios.patch(`${API_URL}/factors/${id}`, { name, description, type, theme_id: themeId });
        return response.data;
    },

    deleteFactor: async (id: string) => {
        const response = await axios.delete(`${API_URL}/factors/${id}`);
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
        const response = await axios.post(`${API_URL}/claims_manual`, data);
        return response.data;
    },

    updateClaim: async (id: string, data: {
        statement?: string;
        polarity?: string;
        confidence?: number;
        source_id?: string;
        target_id?: string;
    }) => {
        const response = await axios.patch(`${API_URL}/claims/${id}`, data);
        return response.data;
    },

    deleteClaim: async (id: string) => {
        const response = await axios.delete(`${API_URL}/claims/${id}`);
        return response.data;
    }
};
