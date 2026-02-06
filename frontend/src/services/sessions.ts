import { supabase } from '../lib/supabase';
import type { VotingSession, VotingSessionConfig } from '../types/session';

const API_base = import.meta.env.VITE_API_URL || '/api';

export const sessionService = {
    async startSession(themeVersionId: string, config: VotingSessionConfig): Promise<VotingSession> {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;

        if (!token) throw new Error('No active session');

        const response = await fetch(`${API_base}/sessions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                theme_version_id: themeVersionId,
                config
            })
        });

        if (!response.ok) {
            throw new Error('Failed to start session');
        }

        return await response.json();
    },

    async updateSession(sessionId: string, status: 'closed'): Promise<void> {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;

        if (!token) throw new Error('No active session');

        const response = await fetch(`${API_base}/sessions/${sessionId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ status })
        });

        if (!response.ok) {
            throw new Error('Failed to update session');
        }
    },

    async getActiveSession(themeVersionId: string): Promise<VotingSession | null> {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;

        const response = await fetch(`${API_base}/sessions/active?theme_version_id=${themeVersionId}`, {
            headers: {
                'Authorization': token ? `Bearer ${token}` : ''
            }
        });

        if (response.status === 404) return null;
        if (!response.ok) throw new Error('Failed to fetch active session');

        return await response.json();
    }
};
