import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { CausaShell } from '../../perspectives/causa';
import { api, type Claim } from '../../services/api';
import { Maximize2, Minimize2, ArrowLeft, Settings } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useSearchParams } from 'react-router-dom';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import type { ConversationContext } from '../../types/conversation';
import { ConversationPane } from '../shell/ConversationPane';
import { MemberManagement } from '../Settings/MemberManagement';

interface ValorWorkspaceProps {
    projectId: string;
    projectName: string;
    dsId: string;
    themeName: string;
    onBack: () => void;
}

type AgentType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

import { useWebSocket } from '../../hooks/useWebSocket';

// ... imports
import { useDesignSpace } from '../../context/DesignSpaceContext';
import { ThemeContextPanel } from '../Theme/ThemeContextPanel';
import { PhaseSelector } from '../deliberation/PhaseSelector';

export const ValorWorkspace: React.FC<ValorWorkspaceProps> = ({ projectId, dsId, projectName, themeName, onBack }) => {
    const [searchParams, setSearchParams] = useSearchParams();
    const mode = searchParams.get('mode') as AgentType | null;

    const [activeAgent, setActiveAgent] = useState<AgentType>(mode || 'CAUSA');

    // WebSocket Integration
    const { lastMessage, sendMessage } = useWebSocket(projectId);
    const websocketContext = useMemo(() => ({ lastMessage, sendMessage }), [lastMessage, sendMessage]);
    const [currentUser, setCurrentUser] = useState<any>(null);

    // Context Integration
    const { currentViewedVersion, isReadOnly, setActiveVotingSession, phaseSnapshots, activePhaseId, setActivePhaseId } = useDesignSpace();

    // dsId IS de ds_id — direct gebruiken, geen lookup nodig
    const activeDesignSpaceId = dsId;
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

    // Fetch user on mount for identity
    useEffect(() => {
        // Simple fetch or use context
        // We can decode the session token or use API
        // For now, let's use the local storage session or API
        // Better: supabase.auth.getUser()
        const fetchUser = async () => {
            try {
                // Ensure auth session exists first (handled by AuthContext generally, but safe to check)
                const { data: { session } } = await import('../../lib/supabase').then(m => m.supabase.auth.getSession());

                if (session) {
                    const profile = await api.getProfile();
                    // Use Username if available, fallback to name, then email
                    const displayName = profile.username || profile.name || profile.email;
                    setCurrentUser({ ...profile, displayName });
                }
            } catch (err) {
                console.error("Failed to fetch user profile", err);
            }
        };
        fetchUser();
    }, []);

    // Sync state to URL if changed via UI
    useEffect(() => {
        if (activeAgent) {
            setSearchParams(prev => {
                prev.set('mode', activeAgent);
                return prev;
            });
        }
    }, [activeAgent, setSearchParams]);
    // const [factors, setFactors] = useState<any[]>([]); // Cleaned up unused state
    const [activeConversation, setActiveConversation] = useState<ConversationContext | null>(null);
    const [focusMode, setFocusMode] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    const refreshData = useCallback(async () => {
        if (!currentViewedVersion) return;

        try {
            // Fetch data specific to the CURRENTLY VIEWED version
            // For historical versions, this fetches historical data.
            // For active version, this fetches current data (which is conceptually 'active version data')

            // NOTE: CausaShell likely fetches its own data or needs props. 
            // Currently CausaShell fetches data via api calls internally or we pass it? 
            // Checking CausaShell props: it takes themeId. 
            // We need to pass the versionId to CausaShell so IT can fetch the right data!
            // OR we fetch here and pass data down.
            // CausaShell usually handles the graph.

            // For now, we just ensure we can fetch. 
            // The CausaShell component needs to be updated to accept `versionId` and `isReadOnly`.
            console.log('Refreshing data for version:', currentViewedVersion.id);

        } catch (error) {
            console.error('Failed to fetch theme data:', error);
        }
    }, [currentViewedVersion]); // Depend on the viewed version

    // Fetch data when viewed version changes
    useEffect(() => {
        refreshData();
    }, [refreshData]);

    const handleOpenConversation = useCallback((context: ConversationContext) => {
        setActiveConversation(context);
    }, []);

    const handleCloseConversation = () => {
        setActiveConversation(null);
    };

    const handleClaimsUpdate = async (_newClaims: Claim[]) => {
        await refreshData();
    };

    return (
        <div className="flex flex-col h-screen bg-background overflow-hidden relative">
            <header className="h-14 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-4 shrink-0 z-30">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={onBack} title="Terug">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                    <div className="flex flex-col">
                        <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold leading-none mb-1">{projectName}</span>
                        <span className="text-sm font-bold leading-none">{themeName}</span>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <ToggleGroup
                        type="single"
                        value={activeAgent}
                        onValueChange={(val) => val && setActiveAgent(val as AgentType)}
                    >
                        <ToggleGroupItem value="CAUSA" aria-label="Toggle CAUSA">CAUSA</ToggleGroupItem>
                        <ToggleGroupItem value="AXIA" disabled aria-label="Toggle AXIA">
                            AXIA <span className="ml-1.5 text-[9px] opacity-70">SOON</span>
                        </ToggleGroupItem>
                        <ToggleGroupItem value="ACTOR" disabled aria-label="Toggle ACTOR">
                            ACTOR <span className="ml-1.5 text-[9px] opacity-70">SOON</span>
                        </ToggleGroupItem>
                        <ToggleGroupItem value="PRAXIS" disabled aria-label="Toggle PRAXIS">
                            PRAXIS <span className="ml-1.5 text-[9px] opacity-70">SOON</span>
                        </ToggleGroupItem>
                    </ToggleGroup>
                </div>

                <div className="flex items-center gap-2">
                    <PhaseSelector
                        snapshots={phaseSnapshots}
                        activePhaseId={activePhaseId}
                        onSelect={setActivePhaseId}
                    />
                    {/* Theme Context Panel (Version Switcher) */}
                    <ThemeContextPanel />

                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setIsSettingsOpen(true)}
                        title="Thema Instellingen & Leden"
                    >
                        <Settings size={18} />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setFocusMode(!focusMode)}
                        title={focusMode ? "Exit Focus Mode" : "Enter Focus Mode"}
                        className={focusMode ? 'text-primary bg-primary/10' : ''}
                    >
                        {focusMode ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                    </Button>
                </div>
            </header>

            <main className="flex-1 flex overflow-hidden relative">
                {activeAgent === 'CAUSA' ? (
                    <div className="flex-1 flex overflow-hidden">
                        <div className="flex-1 bg-muted/30 h-full relative overflow-hidden">
                            {/* Pass version context to CausaShell */}
                            <CausaShell
                                themeId={dsId}
                                projectId={projectId}
                                onOpenConversation={handleOpenConversation}
                                websocket={websocketContext}
                                currentUserId={currentUser?.id || null}
                                versionId={currentViewedVersion?.id}
                                isReadOnly={isReadOnly}
                                designSpaceId={activeDesignSpaceId}
                                canResolveThread={userCanResolve}
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
            </main>

            <ConversationPane
                isOpen={!!activeConversation}
                onClose={handleCloseConversation}
                context={activeConversation}
                topicId={dsId}
                topicLabel={themeName}
                onClaimsUpdate={handleClaimsUpdate}
                isReadOnly={isReadOnly}
            />

            <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
                <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto" aria-describedby={undefined}>
                    <DialogHeader>
                        <DialogTitle>Thema Instellingen: {themeName}</DialogTitle>
                    </DialogHeader>
                    <div className="py-4">
                        <MemberManagement entityId={dsId} entityType="theme" />
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};
