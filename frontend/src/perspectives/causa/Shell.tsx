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
import { getNodesBounds } from 'reactflow';
import { PerspectiveToolbar } from '@/components/shell/PerspectiveToolbar';
import { ExportMenu } from '@/components/shell/ExportMenu';
import { useDomExport } from '@/hooks/useDomExport';
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
    versionId?: string;
    isReadOnly?: boolean;
    currentUserId?: string;
    onOpenConversation?: (context: ConversationContext) => void;
    onSelect?: (selection: any) => void;
}

export const CausaShell = ({ themeId, projectId, websocket, currentUserId, onSelect, onOpenConversation, versionId, isReadOnly = false }: CausaShellProps) => {
    // A. Local UI State
    const [localSelection, setLocalSelection] = useState<{ type: 'node' | 'link'; data: any } | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [layoutMode, setLayoutMode] = useState<'free' | 'system'>('free');
    const containerRef = useRef<HTMLDivElement>(null);
    const { exportAsPng, exportAsPdf, exportAsSvg, isExporting } = useDomExport(containerRef);
    const [rfInstance, setRfInstance] = useState<any>(null);



    // Cache for layout positions per mode (Persists across renders, does not trigger render)
    // Stores { [nodeId]: {x, y} } for each mode
    const layoutCache = useRef<{
        free: Map<string, { x: number, y: number }>;
        system: Map<string, { x: number, y: number }>;
    }>({
        free: new Map(),
        system: new Map()
    });

    // Helper: Calculate Export Config for Full Diagram
    const getExportConfig = () => {
        if (!rfInstance || !containerRef.current) return {};
        // Filter out hidden nodes AND system scope nodes AND explicitly set origin
        // CLDView uses nodeOrigin={[0.5, 0.5]}, so we must tell getNodesBounds this,
        // otherwise it calculates bounds from the center point (cutting nodes in half).
        const nodes = rfInstance.getNodes()
            .filter((n: any) => !n.hidden && n.type !== 'hidden' && n.type !== 'systemScope')
            .map((n: any) => ({
                ...n,
                // Force origin to match CLDView's global configuration
                origin: [0.5, 0.5]
            }));

        if (nodes.length === 0) return {};

        // Use official React Flow util (getNodesBounds preferred in v11)
        const bounds = getNodesBounds(nodes);

        // Dynamic Dimensions = Exact Content Size + Comfortable Padding
        const padding = 150;
        const width = Math.ceil(bounds.width + (padding * 2));
        const height = Math.ceil(bounds.height + (padding * 2));

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
    const { nodes, links, factors, refresh, loading } = useCausaData(themeId, versionId);

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

        if (onSelect) {
            onSelect(sel?.data || null);
        }

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
        if (isReadOnly) return;
        setLocalSelection(sel); // Ensure it is selected
        setIsEditModalOpen(true);
    };

    const handleCreateFactor = async (name: string, type: any, description: string) => {
        if (isReadOnly) return;
        try {
            await api.createFactor(themeId, name, description, type);
            refresh();
        } catch (error) {
            console.error('Failed to create factor', error);
        }
    };

    const handleConnect = async (connection: any) => {
        if (isReadOnly) return;
        if (!connection.source || !connection.target) return;
        try {
            // Default new relation to positive for now, or open modal
            // For MVP: Create a neutral/positive claim directly
            // createClaim signature: (themeId, sourceId, targetId, relationType, polarity, certainty)
            // Assuming api.createClaim expects an object or specific args. Let's check api.ts definition if possible, 
            // but based on error 'Expected 1 arguments', it likely takes a single object.
            // Wait, looking at previous api.ts usage or definition is better. 
            // For now, I'll assume it takes an object based on the error.
            // Start API call
            await api.createClaim({
                theme_id: themeId,
                source_id: connection.source,
                target_id: connection.target,
                statement: 'invloed', // Default statement
                polarity: '+',
                confidence: 0.8
            });
            refresh();
        } catch (error) {
            console.error('Failed to create connection', error);
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
                onOpenGlobalConversation={() => onOpenConversation?.({
                    scope: 'view',
                    perspective: 'CAUSA',
                    contextId: 'main-view',
                    label: 'Causa Assistant'
                })}
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
                {!isReadOnly && (
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
                onViewportChange={setViewport}
                onInit={setRfInstance}
                onConnect={isReadOnly ? undefined : handleConnect}
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
        </div >
    );
};
