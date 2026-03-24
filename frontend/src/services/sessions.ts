import { apiClient } from './api';
import type { VotingSession, VotingSessionConfig } from '../types/session';
import type { Claim, ShortlistClaim, ConsentVotePayload, ValidationResult } from './api';

export interface SessionService {
    startSession(themeVersionId: string, config: VotingSessionConfig): Promise<VotingSession>;
    updateSession(sessionId: string, status: 'closed'): Promise<void>;
    getActiveSession(themeVersionId: string): Promise<VotingSession | null>;
    submitFeedback(sessionId: string, claimVersionId: string, color: string, motivation?: string): Promise<void>;
    updateStage(sessionId: string, stage: string): Promise<void>;
    getFeedback(sessionId: string): Promise<any[]>;
    submitRanking(sessionId: string, claimVersionId: string, category: string): Promise<void>;
    getRankings(sessionId: string): Promise<any[]>;
    getEligibleClaims(sessionId: string): Promise<Claim[]>;
    getConsentShortlist(sessionId: string): Promise<ShortlistClaim[]>;
    submitConsentVote(sessionId: string, payload: ConsentVotePayload): Promise<void>;
    getSessionParticipation(sessionId: string): Promise<any[]>;
    finalizeDeliberation(sessionId: string): Promise<any>;
    getManagedSessions(): Promise<any[]>;
    getTransitionValidation(sessionId: string, targetStage: string): Promise<ValidationResult>;
}

export const sessionService: SessionService = {
    async startSession(themeVersionId: string, config: VotingSessionConfig): Promise<VotingSession> {
        const response = await apiClient.post<VotingSession>('/sessions', {
            theme_version_id: themeVersionId,
            config
        });
        return response.data;
    },

    async updateSession(sessionId: string, status: 'closed'): Promise<void> {
        await apiClient.patch(`/sessions/${sessionId}`, { status });
    },

    async getActiveSession(themeVersionId: string): Promise<VotingSession | null> {
        try {
            const response = await apiClient.get<VotingSession>(`/sessions/active`, {
                params: { theme_version_id: themeVersionId }
            });
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) return null;
            throw error;
        }
    },

    async submitFeedback(sessionId: string, claimVersionId: string, color: string, motivation?: string): Promise<void> {
        await apiClient.post('/deliberation/feedback', {
            session_id: sessionId,
            tessera_base_id: claimVersionId,
            color,
            motivation
        });
    },

    async updateStage(sessionId: string, stage: string): Promise<void> {
        await apiClient.patch(`/deliberation/session/${sessionId}/stage`, { stage });
    },

    async getFeedback(sessionId: string): Promise<any[]> {
        const response = await apiClient.get<any[]>(`/deliberation/feedback/${sessionId}`);
        return response.data;
    },

    async submitRanking(sessionId: string, claimVersionId: string, category: string): Promise<void> {
        await apiClient.post('/deliberation/rank', {
            session_id: sessionId,
            tessera_base_id: claimVersionId,
            category
        });
    },

    async getRankings(sessionId: string): Promise<any[]> {
        const response = await apiClient.get<any[]>(`/deliberation/rankings/${sessionId}`);
        return response.data;
    },

    async finalizeDeliberation(sessionId: string): Promise<any> {
        const response = await apiClient.post(`/deliberation/session/${sessionId}/finalize`);
        return response.data;
    },

    async getManagedSessions(): Promise<any[]> {
        const response = await apiClient.get('/deliberation/moderator/sessions');
        return response.data;
    },

    async getSessionParticipation(sessionId: string): Promise<any[]> {
        const response = await apiClient.get(`/deliberation/session/${sessionId}/participation`);
        return response.data;
    },

    async getEligibleClaims(sessionId: string): Promise<Claim[]> {
        const response = await apiClient.get<Claim[]>(`/deliberation/session/${sessionId}/eligible-claims`);
        return response.data;
    },

    async getConsentShortlist(sessionId: string): Promise<ShortlistClaim[]> {
        const response = await apiClient.get<ShortlistClaim[]>(`/deliberation/session/${sessionId}/consent-shortlist`);
        return response.data;
    },

    async submitConsentVote(sessionId: string, payload: ConsentVotePayload): Promise<void> {
        await apiClient.post(`/deliberation/session/${sessionId}/consent-vote`, payload);
    },

    async getTransitionValidation(sessionId: string, targetStage: string): Promise<ValidationResult> {
        const response = await apiClient.get<ValidationResult>(`/deliberation/session/${sessionId}/transition-validation`, {
            params: { target_stage: targetStage }
        });
        return response.data;
    }
};
