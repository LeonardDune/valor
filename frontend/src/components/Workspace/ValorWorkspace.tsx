import React, { useState, useEffect, useCallback } from 'react';
import { CausaShell } from '../../perspectives/causa';
import { api, type Claim, type Space } from '../../services/api';
import { Maximize2, Minimize2, ArrowLeft, Settings } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useSearchParams, useNavigate } from 'react-router-dom';
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
    themeId: string;
    themeName: string;
    onBack: () => void;
}

type AgentType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

import { useWebSocket } from '../../hooks/useWebSocket';

export const ValorWorkspace: React.FC<ValorWorkspaceProps> = ({ projectId, themeId, projectName, themeName, onBack }) => {
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();
    const mode = searchParams.get('mode') as AgentType | null;

    const [activeAgent, setActiveAgent] = useState<AgentType>(mode || 'CAUSA');

    // WebSocket Integration
    const { lastMessage, sendMessage } = useWebSocket(projectId);
    const [currentUser, setCurrentUser] = useState<any>(null);

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
                    // Spread profile first, then override specific fields if needed
                    setCurrentUser({ ...profile, id: displayName, email: profile.email });
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
    const [isSpacesOpen, setIsSpacesOpen] = useState(false);
    const [spaces, setSpaces] = useState<Space[]>([]);

    const refreshData = useCallback(async () => {
        try {
            const [existingClaims, themeFactors, themeSpaces] = await Promise.all([
                api.getThemeClaims(themeId),
                api.getThemeFactors(themeId),
                api.getThemeSpaces(themeId)
            ]);
            setSpaces(themeSpaces);
            console.log('WS: Refreshed Data', { claims: existingClaims.length, factors: themeFactors.length, spaces: themeSpaces.length });

        } catch (error) {
            console.error('Failed to fetch theme data:', error);
        }
    }, [themeId]);

    // Fetch data on mount
    useEffect(() => {
        refreshData();
    }, [refreshData]);

    const handleOpenConversation = (context: ConversationContext) => {
        setActiveConversation(context);
    };

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
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsSpacesOpen(true)}
                        className="mr-2"
                    >
                        Spaces ({spaces.length})
                    </Button>
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
                            <CausaShell
                                themeId={themeId}
                                projectId={projectId}
                                onOpenConversation={handleOpenConversation}
                                websocket={{ lastMessage, sendMessage }}
                                currentUserId={currentUser?.email || 'anon'}
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
                topicId={themeId}
                topicLabel={themeName}
                onClaimsUpdate={handleClaimsUpdate}
            />

            <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
                <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Thema Instellingen: {themeName}</DialogTitle>
                    </DialogHeader>
                    <div className="py-4">
                        <MemberManagement entityId={themeId} entityType="theme" />
                    </div>
                </DialogContent>
            </Dialog>

            <Dialog open={isSpacesOpen} onOpenChange={setIsSpacesOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Conversation Spaces</DialogTitle>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        {spaces.length === 0 ? (
                            <p className="text-muted-foreground text-center py-8">No spaces found in this theme.</p>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {spaces.map(space => (
                                    <div
                                        key={space.id}
                                        className="border rounded-lg p-4 hover:bg-muted/50 cursor-pointer transition-colors"
                                        onClick={() => {
                                            setIsSpacesOpen(false);
                                            navigate(`/spaces/${space.id}`);
                                        }}
                                    >
                                        <h3 className="font-semibold">{space.name}</h3>
                                        <p className="text-sm text-muted-foreground line-clamp-2">{space.description}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                        <Button className="w-full" disabled>Create New Space (Coming Soon)</Button>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};
