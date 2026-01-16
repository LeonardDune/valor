import { useEffect, useMemo, useState, useRef } from 'react';
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Button } from "@/components/ui/button";
import { LayoutGrid, Network, Plus } from "lucide-react";
import { CLDView } from './views/CLDView';
import { useCausaData } from './hooks/useCausaData';
import { LayoutSession } from './layout/session';
import { ForceRunner } from './layout/runners/force';
import { RailRunner } from './layout/runners/rail';
import { FactorModal } from '../../components/Graph/FactorModal';
import { EditFactorDetailModal } from './views/modals/EditFactorDetailModal';
import { api } from '../../services/api';

export interface CausaShellProps {
    themeId: string;
    // We keep onSelect prop for backward compatibility but Shell handles the interaction
    onSelect?: (selection: { type: 'node' | 'link'; data: any } | null) => void;
    selection?: { type: 'node' | 'link'; data: any } | null;
}

export const CausaShell = ({ themeId, onSelect: _onSelect }: CausaShellProps) => {
    // A. Local UI State
    const [localSelection, setLocalSelection] = useState<{ type: 'node' | 'link'; data: any } | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [layoutMode, setLayoutMode] = useState<'free' | 'system'>('free');

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
    }, [layoutMode]); // Re-run when mode changes (Critical for isolation)

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
            if (runner.updateData) {
                runner.updateData(session.getNodes(), session.getLinks());
            }
        }
    }, [session, nodes, links, loading, runner]);

    // ...

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
        if (sel) {
            setIsEditModalOpen(true);
        }
    };

    const handleCreateFactor = async (name: string, type: any, description: string) => {
        try {
            await api.createFactor(themeId, name, description, type);
            refresh();
        } catch (error) {
            console.error('Failed to create factor', error);
        }
    };

    if (!themeId) return <div className="p-10 text-slate-400">No Theme Context</div>;

    return (
        <div className="w-full h-full bg-background relative">
            {/* Header / Toolbar Overlay */}
            <div className="absolute top-4 right-4 z-10 flex gap-2 items-center">
                {/* Layout Toggle */}
                <div className="bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 rounded-md shadow-sm border p-0.5">
                    <ToggleGroup
                        type="single"
                        value={layoutMode}
                        onValueChange={(value) => value && switchMode(value as 'free' | 'system')}
                    >
                        <ToggleGroupItem value="free" size="sm" aria-label="Free Layout">
                            <Network className="h-4 w-4 mr-2" />
                            Vrij
                        </ToggleGroupItem>
                        <ToggleGroupItem value="system" size="sm" aria-label="System Layout">
                            <LayoutGrid className="h-4 w-4 mr-2" />
                            Systeem
                        </ToggleGroupItem>
                    </ToggleGroup>
                </div>

                <Button
                    size="sm"
                    onClick={() => setIsCreateModalOpen(true)}
                    className="shadow-sm gap-1"
                >
                    <Plus className="h-4 w-4" />
                    Nieuw
                </Button>
            </div>

            {/* View */}
            <CLDView
                nodes={nodes}
                links={links}
                session={session}
                runner={runner}
                onSelect={handleSelect}
                selection={localSelection}
                layoutMode={layoutMode}
            />

            {/* Modals */}
            <FactorModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
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
        </div>
    );
};
