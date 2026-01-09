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
    }
};
