export type SessionStatus = 'active' | 'closed';

export interface VotingSessionConfig {
    dots_per_user: number;
    time_limit?: number | null; // in minutes
}

export interface VotingSession {
    id: string;
    theme_version_id: string;
    status: SessionStatus;
    config: VotingSessionConfig;
    created_by: string;
    created_at: string; // ISO Date string
}

export interface SessionContext {
    session: VotingSession | null;
    hasActiveSession: boolean;
    canStartSession: boolean; // based on permissions
}
