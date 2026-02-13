export type SessionStatus = 'active' | 'closed';
export type DeliberationStage = 'refine' | 'ranking' | 'consent' | 'closed';

export interface VotingSessionConfig {
    dots_per_user: number;
    time_limit?: number | null; // in minutes
}

export interface VotingSession {
    id: string;
    theme_version_id: string;
    status: SessionStatus;
    stage: DeliberationStage;
    config: VotingSessionConfig;
    created_by: string;
    created_at: string; // ISO Date string
}

export interface SessionContext {
    session: VotingSession | null;
    hasActiveSession: boolean;
    canStartSession: boolean; // based on permissions
}
export interface Feedback {
    id: string;
    session_id: string;
    claim_version_id: string;
    user_id: string;
    color: 'green' | 'amber' | 'red';
    motivation?: string;
    created_at: string;
}

export interface Ranking {
    claim_version_id: string;
    category: 'high' | 'medium' | 'backlog' | 'discard';
    count: number;
}
