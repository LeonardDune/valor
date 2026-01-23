import { useEffect, useMemo, useState, useRef } from 'react';
// ToggleGroup moved to PerspectiveToolbar component
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { PerspectiveToolbar } from '@/components/shell/PerspectiveToolbar';
import { CLDView } from './views/CLDView';
import { useCausaData } from './hooks/useCausaData';
import { LayoutSession } from './layout/session';
import { ForceRunner } from './layout/runners/force';
import { RailRunner } from './layout/runners/rail';
// import { FactorModal } from '../../components/Graph/FactorModal';
import { CreateFactorModal } from './views/modals/CreateFactorModal';
import { EditFactorDetailModal } from './views/modals/EditFactorDetailModal';
import { api } from '../../services/api';
import type { ConversationContext } from '@/types/conversation';
import { PresenceLayer } from '@/components/graph/PresenceLayer';

export interface CausaShellProps {
    themeId: string;
    projectId: string;
    websocket: {
        lastMessage: any;
        sendMessage: (type: string, payload: any) => void;
    };
    currentUserId?: string; // Add Identity Prop
    // We keep onSelect prop for backward compatibility but Shell handles the interaction
    onSelect?: (selection: { type: 'node' | 'link'; data: any } | null) => void;
    selection?: { type: 'node' | 'link'; data: any } | null;
    onOpenConversation: (context: ConversationContext) => void;
}

export const CausaShell = ({ themeId, projectId, websocket, currentUserId, onSelect: _onSelect, onOpenConversation }: CausaShellProps) => {
    // A. Local UI State
    const [localSelection, setLocalSelection] = useState<{ type: 'node' | 'link'; data: any } | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [layoutMode, setLayoutMode] = useState<'free' | 'system'>('free');
    const containerRef = useRef<HTMLDivElement>(null);

    // Cache for layout positions per mode (Persists across renders, does not trigger render)
    // Stores { [nodeId]: {x, y} } for each mode
    const layoutCache = useRef<{
        free: Map<string, { x: number, y: number }>;
        system: Map<string, { x: number, y: number }>;
    }>({
        free: new Map(),
        system: new Map()
    });

    // B. Fetch Data
    const { nodes, links, factors, refresh, loading } = useCausaData(themeId);

    // C. Initialize Session
    // Re-create session ONLY when layoutMode changes
    // This ensures we start fresh (or from cache) and don't leak state from previous runner
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
        if (!websocket.lastMessage) return;
        const msg = websocket.lastMessage;
        // Check for data updates types
        if (['FACTOR_CREATED', 'FACTOR_UPDATED', 'FACTOR_DELETED', 'CLAIM_CREATED', 'CLAIM_UPDATED', 'CLAIM_DELETED'].includes(msg.type)) {
            // Basic refresh for now. 
            // Ideally we shouldn't re-fetch everything but update local cache.
            // Given MVP and useCausaData structure, calling refresh() is safest.
            console.log('WS: Received update, refreshing graph...', msg.type);
            refresh();
        }
    }, [websocket.lastMessage, refresh]);

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

        // Broadcast Focus
        if (websocket.sendMessage) {
            if (sel?.type === 'node' && sel.data?.id) {
                websocket.sendMessage('NODE_FOCUS', { nodeId: sel.data.id });
            } else {
                // Explicitly clear focus if deselected or selecting a link
                websocket.sendMessage('NODE_FOCUS', { nodeId: null });
            }
        }
    };

    const handleEdit = (sel: { type: 'node' | 'link'; data: any }) => {
        setLocalSelection(sel); // Ensure it is selected
        setIsEditModalOpen(true);
    };

    const handleCreateFactor = async (name: string, type: any, description: string) => {
        try {
            await api.createFactor(themeId, name, description, type);
            refresh();
        } catch (error) {
            console.error('Failed to create factor', error);
        }
    };

    // Viewport State for Presence Sync
    const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 1 });

    if (!themeId) return <div className="p-10 text-muted-foreground italic">Geen thema geactiveerd.</div>;

    return (
        <div ref={containerRef} className="w-full h-full bg-background relative">
            {/* Header / Toolbar Overlay */}
            {/* Standardized Toolbar */}
            <PerspectiveToolbar
                layoutMode={layoutMode}
                onLayoutChange={(mode) => switchMode(mode)}
                onOpenGlobalConversation={() => onOpenConversation({
                    scope: 'view',
                    perspective: 'CAUSA',
                    contextId: 'main-view',
                    label: 'Causa Assistant'
                })}
            >
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
                onOpenConversation={onOpenConversation}
                onEdit={handleEdit}
                onViewportChange={setViewport}
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
                themeId={themeId}
                factors={factors}
                onRefresh={refresh}
            />
            {/* Presence Overlay */}
            <div className="absolute inset-0 pointer-events-none z-50">
                <PresenceLayer
                    projectId={projectId}
                    websocket={websocket}
                    containerRef={containerRef}
                    nodes={session.getNodes()}
                    currentUserId={currentUserId}
                    viewport={viewport}
                />
            </div>
        </div>
    );
};
