import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { CausaShell } from '../../perspectives/causa';
import { api, type Claim } from '../../services/api';
import { useSearchParams } from 'react-router-dom';
import type { ConversationContext } from '../../types/conversation';
import { ConversationPane } from '../shell/ConversationPane';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useDesignSpace } from '../../context/DesignSpaceContext';

type AgentType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

interface ValorWorkspaceProps {
    projectId: string;
    dsId: string;
    themeName: string;
}

export const ValorWorkspace: React.FC<ValorWorkspaceProps> = ({ projectId, dsId, themeName }) => {
    const [searchParams] = useSearchParams();
    const activeAgent = (searchParams.get('mode') as AgentType) || 'CAUSA';

    const { lastMessage, sendMessage } = useWebSocket(projectId);
    const websocketContext = useMemo(() => ({ lastMessage, sendMessage }), [lastMessage, sendMessage]);
    const [currentUser, setCurrentUser] = useState<any>(null);

    const { currentViewedVersion, isReadOnly, setActiveVotingSession, activePhaseId } = useDesignSpace();

    const [userCanResolve, setUserCanResolve] = useState(false);

    useEffect(() => {
        api.getCanResolveThread(dsId)
            .then(r => setUserCanResolve(r.can_resolve))
            .catch(() => setUserCanResolve(false));
    }, [dsId]);

    // WS to Context Sync
    useEffect(() => {
        if (!lastMessage) return;
        const msg = lastMessage;

        if (msg.type === 'SESSION_STARTED') {
            setActiveVotingSession(msg.payload);
        }
        if (msg.type === 'STAGE_UPDATED') {
            setActiveVotingSession(prev => prev ? { ...prev, stage: msg.payload.stage } : null);
        }
        if (msg.type === 'SESSION_CLOSED') {
            setActiveVotingSession(null);
        }
    }, [lastMessage, setActiveVotingSession]);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const { data: { session } } = await import('../../lib/supabase').then(m => m.supabase.auth.getSession());
                if (session) {
                    const profile = await api.getProfile();
                    const displayName = profile.username || profile.name || profile.email;
                    setCurrentUser({ ...profile, displayName });
                }
            } catch (err) {
                console.error('Failed to fetch user profile', err);
            }
        };
        fetchUser();
    }, []);

    const refreshData = useCallback(async () => {
        if (!currentViewedVersion) return;
        console.log('Refreshing data for version:', currentViewedVersion.id);
    }, [currentViewedVersion]);

    useEffect(() => {
        refreshData();
    }, [refreshData]);

    const [activeConversation, setActiveConversation] = useState<ConversationContext | null>(null);

    const handleOpenConversation = useCallback((context: ConversationContext) => {
        setActiveConversation(context);
    }, []);

    const handleClaimsUpdate = async (_newClaims: Claim[]) => {
        await refreshData();
    };

    return (
        <div className="flex h-full bg-background overflow-hidden relative">
            {activeAgent === 'CAUSA' ? (
                <div className="flex-1 flex overflow-hidden">
                    <div className="flex-1 bg-muted/30 h-full relative overflow-hidden">
                        <CausaShell
                            themeId={dsId}
                            projectId={projectId}
                            onOpenConversation={handleOpenConversation}
                            websocket={websocketContext}
                            currentUserId={currentUser?.id || null}
                            versionId={currentViewedVersion?.id}
                            isReadOnly={isReadOnly}
                            designSpaceId={dsId}
                            canResolveThread={userCanResolve && !activePhaseId}
                        />
                    </div>
                </div>
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center bg-muted/10 text-muted-foreground">
                    <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4 text-muted-foreground/50">
                        ?
                    </div>
                    <p className="font-medium">Module {activeAgent} is nog in ontwikkeling.</p>
                    <p className="text-sm">We werken hard aan de volgende stap in de analyse.</p>
                </div>
            )}

            <ConversationPane
                isOpen={!!activeConversation}
                onClose={() => setActiveConversation(null)}
                context={activeConversation}
                topicId={dsId}
                topicLabel={themeName}
                onClaimsUpdate={handleClaimsUpdate}
                isReadOnly={isReadOnly}
            />
        </div>
    );
};
