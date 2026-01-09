import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Claim {
    id: string;
    statement: string;
    confidence: number;
    source_node: string;
    target_node: string;
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

    // Manual Editing
    createFactor: async (name: string, description?: string) => {
        const response = await axios.post(`${API_URL}/factors`, { name, description });
        return response.data;
    },

    updateFactor: async (id: string, name?: string, description?: string) => {
        const response = await axios.patch(`${API_URL}/factors/${id}`, { name, description });
        return response.data;
    },

    createClaimManual: async (data: {
        conversation_id: string;
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
    }) => {
        const response = await axios.patch(`${API_URL}/claims/${id}`, data);
        return response.data;
    },

    deleteClaim: async (id: string) => {
        const response = await axios.delete(`${API_URL}/claims/${id}`);
        return response.data;
    }
};
