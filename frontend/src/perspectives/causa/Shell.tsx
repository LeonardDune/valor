import { useEffect, useMemo, useState } from 'react';
import { CLDView } from './views/CLDView';
import { useCausaData } from './hooks/useCausaData';
import { LayoutSession } from './layout/session';
import { BasicRunner } from './layout/runners/basic';
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

    // B. Fetch Data
    const { nodes, links, factors, refresh, loading } = useCausaData(themeId);

    // C. Initialize Session
    const session = useMemo(() => {
        // Initialize with default 'System' friendly size, though layout strategy sets this later
        return new LayoutSession([], [], {
            width: 1000,
            height: 800,
            alphaDecay: 0.0228,
            velocityDecay: 0.4
        });
    }, []);

    // D. Sync Data
    useEffect(() => {
        if (!loading) {
            session.syncGraph(nodes, links);
        }
    }, [session, nodes, links, loading]);

    const runner = useMemo(() => new BasicRunner(session), [session]);

    // E. Interactions
    const handleSelect = (sel: { type: 'node' | 'link'; data: any } | null) => {
        setLocalSelection(sel);
        if (sel) {
            setIsEditModalOpen(true);
        }
        // We do NOT propagate to parent Workspace to avoid opening the old InspectorSidebar
        // if (onSelect) onSelect(sel);
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
        <div className="w-full h-full bg-slate-50 relative">
            {/* Header / Toolbar Overlay */}
            <div className="absolute top-4 right-4 z-10 flex gap-2">
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-xs font-bold shadow-sm transition-all"
                >
                    + Nieuw
                </button>
            </div>

            {/* View */}
            <CLDView
                nodes={nodes}
                links={links}
                session={session}
                runner={runner}
                onSelect={handleSelect}
                selection={localSelection}
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
