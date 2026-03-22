import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { useEffect, useMemo, useState, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getNodesBounds } from 'reactflow';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { PerspectiveToolbar } from '@/components/shell/PerspectiveToolbar';
import { ExportMenu } from '@/components/shell/ExportMenu';
import { useDomExport } from '@/hooks/useDomExport';
import { CLDView } from './views/CLDView';
import { useCausaData } from './hooks/useCausaData';
import { LayoutSession } from './layout/session';
import { ForceRunner } from './layout/runners/force';
import { RailRunner } from './layout/runners/rail';
import { CreateFactorModal } from './views/modals/CreateFactorModal';
import { EditFactorDetailModal } from './views/modals/EditFactorDetailModal';
import { ParticipantDashboard } from '@/components/deliberation/ParticipantDashboard';
import { ModeratorDashboard } from '@/components/deliberation/ModeratorDashboard';
import { useDesignSpace } from '@/context/DesignSpaceContext';
// RankingBoard, ConsentBoard, RefinementBoard removed
import { api } from '@/services/api';
import { sessionService } from '@/services/sessions';
import type { VotingSessionConfig } from '@/types/session';
import type { ConversationContext } from '@/types/conversation';


export interface CausaShellProps {
    themeId: string;
    projectId?: string;
    websocket?: any;
    currentUserId?: string;
    onSelect?: (nodeId: string | null) => void;
    onOpenConversation?: (context: ConversationContext) => void;
    versionId?: string;
    isReadOnly?: boolean;
    designSpaceId?: string;
    canResolveThread?: boolean;
}

export const CausaShell = ({ themeId, websocket, currentUserId, onSelect, onOpenConversation, versionId, isReadOnly = false, designSpaceId, canResolveThread = false }: CausaShellProps) => {
    const queryClient = useQueryClient();
    const themeState = useDesignSpace();

    // A. Local UI State
    const [localSelection, setLocalSelection] = useState<{ type: 'node' | 'link'; data: any } | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [layoutMode, setLayoutMode] = useState<'free' | 'system'>('free');

    // Derived state
    const { activeVersion, activeVotingSession } = themeState;
    // TODO: Verify if activeVersion has role. Use role 'moderator' check if available, or fallback.
    // Ideally user role should be joined. For now assuming activeVersion carries role context or we check activeVersion.role
    const isModerator = (activeVersion as any)?.role === 'moderator' || (activeVersion as any)?.role === 'admin';

    // const [showDeliberation, setShowDeliberation] = useState(false); // Removed
    const [showModeratorDashboard, setShowModeratorDashboard] = useState(false);
    const [showParticipantDashboard, setShowParticipantDashboard] = useState(false);
    // const [isFullscreen, setIsFullscreen] = useState(false); // Unused
    const containerRef = useRef<HTMLDivElement>(null);
    const { exportAsPng, exportAsPdf, exportAsSvg, isExporting } = useDomExport(containerRef);
    const [rfInstance, setRfInstance] = useState<any>(null);

    // Is Effective Read Only?
    // If we are in a specific version (history) -> Read Only
    // If explicit prop isReadOnly -> Read Only
    // If versionId is provided AND it is NOT the active version -> Read Only
    const effectiveIsReadOnly = isReadOnly || (!!versionId && versionId !== activeVersion?.id);

    // Persist layout mode preference across re-renders/sessions if needed?
    // For now, we prefer to keep it in state. 
    // But we might want to Cache positions when switching.
    const layoutCache = useRef<{ [key: string]: Map<string, { x: number, y: number }> }>({
        free: new Map(),
        system: new Map()
    });

    const [isStartingSession, setIsStartingSession] = useState(false);

    // Helpers for Export
    const getExportConfig = () => {
        if (!rfInstance || !containerRef.current) return {};
        const getNodes = rfInstance.getNodes;
        if (!getNodes) return {};

        const nodes = getNodes();
        if (nodes.length === 0) return {};

        const bounds = getNodesBounds(nodes);
        const padding = 50;
        const width = bounds.width + (padding * 2);
        const height = bounds.height + (padding * 2);

        // CRITICAL FIX: Do NOT use getViewportForBounds. 
        // We want 1:1 scale (zoom=1). We just need to shift (translate) the viewport
        // so that the top-left of the graph (bounds.x, bounds.y) aligns with (0,0) of our image.
        const x = -bounds.x + padding;
        const y = -bounds.y + padding;
        const zoom = 1;

        // Find the viewport element to export directly
        const viewportParams = {
            element: containerRef.current.querySelector('.react-flow__viewport') as HTMLElement,
            width,
            height,
            style: {
                width: `${width}px`,
                height: `${height}px`,
                transform: `translate(${x}px, ${y}px) scale(${zoom})`,
                transformOrigin: '0 0',
                margin: 0,
                padding: 0
            }
        };

        return viewportParams;
    };

    // B. Fetch Data
    // console.log('[CausaShell] Props:', { themeId, versionId, activeVersionId: themeState.activeVersion?.id });
    const { nodes, links, factors, refresh, loading, cycleNodeIds } = useCausaData(themeId, versionId || themeState.activeVersion?.id);

    // C. Initialize Session
    // Re-create session ONLY when layoutMode changes
    // This ensures we start fresh (or from cache) and don't leak state from previous runner
    // We also re-create session if nodes change significantly? No, syncGraph handles that. 
    // But if we switch version, nodes change completely. session.syncGraph should handle it.
    const session = useMemo(() => {
        // Load initial positions from cache if available
        const cachedPositions = layoutCache.current[layoutMode];

        // Note: LayoutSession constructor handles mixing existing cached positions with new nodes (random/jitter)
        return new LayoutSession(nodes, links, {
            width: 1000,
            height: 800,
            alphaDecay: 0.0228,
            velocityDecay: 0.4
        }, cachedPositions);
    }, [layoutMode, loading, nodes, links]); // Dependencies updated to include data

    // Switch Runner based on Mode
    const runner = useMemo(() => {
        if (layoutMode === 'system') {
            return new RailRunner(session);
        }
        return new ForceRunner(session);
    }, [session, layoutMode]);

    // D. Sync Data & Notify Runner
    useEffect(() => {
        if (!loading && nodes.length > 0) {
            session.syncGraph(nodes, links);

            // Critical Fix for Initial Load & Hydration
            // Notify runner of updated data. 
            // Since session is fresh on mode swap, this ensures runner gets the initial data.
            // Check if updateData exists (it does on ForceRunner, maybe not RailRunner base?)
            if ('updateData' in runner) {
                (runner as any).updateData(session.getNodes(), session.getLinks());
            }
        }
    }, [session, nodes, links, loading, runner]);

    // WebSocket Data Sync
    useEffect(() => {
        if (!websocket?.lastMessage) return;
        const msg = websocket.lastMessage;
        // Check for data updates types
        if (['FACTOR_CREATED', 'FACTOR_UPDATED', 'FACTOR_DELETED', 'CLAIM_CREATED', 'CLAIM_UPDATED', 'CLAIM_DELETED'].includes(msg.type)) {
            console.log('WS: Received update, refreshing graph...', msg.type);
            refresh(true);
        }
    }, [websocket?.lastMessage, refresh]);

    // Auto-show deliberation removed -> Manual trigger via Toolbar

    // Helper to switch mode safely
    const switchMode = (newMode: 'free' | 'system') => {
        if (newMode === layoutMode) return;

        // 1. Save current positions to cache for the OLD mode
        const currentPositions = new Map<string, { x: number, y: number }>();
        session.getNodes().forEach(n => {
            currentPositions.set(n.id, { x: n.x, y: n.y });
        });
        layoutCache.current[layoutMode] = currentPositions;

        // 2. Set new mode (triggers Session recreation via useMemo)
        setLayoutMode(newMode);
    };

    // E. Interactions
    const handleSelect = (sel: { type: 'node' | 'link'; data: any } | null) => {
        setLocalSelection(sel);

        if (onSelect) {
            onSelect(sel?.data?.id || null);
        }

        // Broadcast Focus
        if (websocket?.sendMessage) {
            if (sel?.type === 'node' && sel.data?.id) {
                websocket.sendMessage('NODE_FOCUS', { nodeId: sel.data.id });
            } else {
                // Explicitly clear focus if deselected or selecting a link
                websocket.sendMessage('NODE_FOCUS', { nodeId: null });
            }
        }
    };

    const handleEdit = (sel: { type: 'node' | 'link'; data: any }) => {
        // Allow opening modal even in read-only mode (modal itself handles read-only state)
        setLocalSelection(sel); // Ensure it is selected
        setIsEditModalOpen(true);
    };

    const handleCreateFactor = async (name: string, type: any, description: string) => {
        if (effectiveIsReadOnly) return;
        try {
            await api.createFactor(themeId, name, description, type);
            // Force refresh to bypass cache check and show new factor immediately
            await refresh(true);
        } catch (error) {
            console.error('Failed to create factor', error);
        }
    };

    const handleConnect = async (connection: any) => {
        if (effectiveIsReadOnly) return;
        if (!connection.source || !connection.target) return;
        try {
            await api.createClaim({
                ds_id: themeId,
                source_id: connection.source,
                target_id: connection.target,
                statement: 'invloed', // Default statement
                polarity: '+',
                confidence: 0.8
            });
            // Force refresh to show new connection immediately
            await refresh(true);
        } catch (error) {
            console.error('Failed to create connection', error);
        }
    };

    const handleStartVoting = async (config: VotingSessionConfig) => {
        if (!versionId && !themeState.activeVersion?.id) return;
        const targetVersionId = versionId || themeState.activeVersion?.id;
        if (!targetVersionId) return;

        setIsStartingSession(true);
        try {
            await sessionService.startSession(targetVersionId, config);

            // Force UI update by invalidating session queries
            // This triggers useActiveSession (in ThemeContext) to refetch
            await queryClient.invalidateQueries({ queryKey: ['sessions'] });

            // Note: ModeratorDashboard will auto-switch tab via its own effect
        } catch (error) {
            console.error('Failed to start voting session', error);
            setIsStartingSession(false);
        }
    };

    // Calculate viewMode primarily for toolbar state
    // const viewMode = (showDeliberation && activeVotingSession) ? 'deliberation' : 'graph'; 

    if (!themeId) return <div className="p-10 text-muted-foreground italic">Geen thema geactiveerd.</div>;

    return (
        <div ref={containerRef} className="w-full h-full bg-background relative">
            {/* Header / Toolbar Overlay */}
            {/* Standardized Toolbar */}
            <PerspectiveToolbar
                layoutMode={layoutMode}
                onLayoutChange={switchMode}
                isModerator={!!isModerator}
                onOpenModeratorDashboard={() => setShowModeratorDashboard(true)}
                onResumeDeliberation={activeVotingSession ? () => setShowParticipantDashboard(true) : undefined}
                exportActions={
                    <>
                        <ExportMenu
                            onExportPng={() => exportAsPng(`Causa_Snapshot_${themeId}_${new Date().toISOString().slice(0, 10)}`, getExportConfig())}
                            onExportPdf={() => exportAsPdf(`Causa_Snapshot_${themeId}_${new Date().toISOString().slice(0, 10)}`, getExportConfig())}
                            onExportSvg={() => exportAsSvg(`Causa_Snapshot_${themeId}_${new Date().toISOString().slice(0, 10)}`, getExportConfig())}
                            isExporting={isExporting}
                        />
                    </>
                }
            >
                {!effectiveIsReadOnly && (
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    size="sm"
                                    onClick={() => setIsCreateModalOpen(true)}
                                    variant="ghost"
                                    className="h-8 w-8 p-0"
                                >
                                    <Plus className="h-4 w-4" />
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>Nieuwe Factor</TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                )}


            </PerspectiveToolbar>

            {/* View */}
            <CLDView
                nodes={nodes}
                links={links}
                session={session}
                runner={runner}
                onSelect={handleSelect}
                selection={localSelection}
                layoutMode={layoutMode}
                onOpenConversation={onOpenConversation || (() => { })}
                onEdit={handleEdit}
                onViewportChange={() => { }}
                onInit={setRfInstance}
                onConnect={effectiveIsReadOnly ? undefined : handleConnect}
                isReadOnly={effectiveIsReadOnly}
                designSpaceId={designSpaceId}
                canResolveThread={canResolveThread}
                cycleNodeIds={cycleNodeIds}
            />

            {/* Modals */}
            <CreateFactorModal
                open={isCreateModalOpen}
                onOpenChange={setIsCreateModalOpen}
                onSave={handleCreateFactor}
            />

            <EditFactorDetailModal
                open={isEditModalOpen}
                onOpenChange={setIsEditModalOpen}
                selection={localSelection}
                onRefresh={() => refresh(true)}
                factors={factors}
                themeId={themeId}
                readOnly={effectiveIsReadOnly}
            />

            {/* Moderator Dashboard Sidebar */}
            {showModeratorDashboard && (
                <div className="absolute top-0 right-0 h-full w-[600px] bg-background border-l shadow-2xl z-50 overflow-hidden flex flex-col transition-transform duration-300 ease-in-out transform translate-x-0">
                    <ModeratorDashboard
                        sessionId={activeVotingSession?.id}
                        stage={activeVotingSession?.stage}
                        onClose={() => setShowModeratorDashboard(false)}
                        onStartSession={handleStartVoting}
                        isStartingSession={isStartingSession}
                    />
                </div>
            )}

            {/* Participant Dashboard Sidebar (Voting) */}
            {showParticipantDashboard && activeVotingSession && (
                <div className="absolute top-0 right-0 h-full w-full md:w-[800px] bg-background border-l shadow-2xl z-50 overflow-hidden flex flex-col transition-transform duration-300 ease-in-out transform translate-x-0">
                    <ParticipantDashboard
                        sessionId={activeVotingSession.id}
                        versionId={versionId || themeState.activeVersion?.id || ''}
                        stage={activeVotingSession.stage}
                        onClose={() => setShowParticipantDashboard(false)}
                        currentUserId={currentUserId}
                        factors={factors}
                    />
                </div>
            )}

        </div >
    );
};
