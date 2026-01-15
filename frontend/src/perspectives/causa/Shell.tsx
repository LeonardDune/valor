import { useEffect, useMemo } from 'react';
import { CLDView } from './views/CLDView';
import { useCausaData } from './hooks/useCausaData';
import { LayoutSession } from './layout/session';
import { BasicRunner } from './layout/runners/basic';

// Note: We might need to receive props or context here in the future.
// For now, we assume the parent renders this with a 'themeId' prop 
// OR we default to a test ID if not provided (though that's dangerous).
// Actually, Perspective definition says Shell: () => ReactNode.
// So we need a way to get the Theme ID.
// Ideally, the Workspace renders <Shell themeId={...} /> if we change the type,
// or we use a React Context.
// Since I cannot change Workspace right now easily, I'll export CausaShell
// and assume we will update the Perspective Type / Workspace later or use a Context hack.

// For Verification: I will allow this component to take props.
export interface CausaShellProps {
    themeId: string;
    onSelect?: (selection: { type: 'node' | 'link'; data: any } | null) => void;
    selection?: { type: 'node' | 'link'; data: any } | null;
}

export const CausaShell = ({ themeId, onSelect, selection }: CausaShellProps) => {
    // 1. Fetch Data (Mapped to Causal Types)
    const { nodes, links, loading } = useCausaData(themeId);

    // 2. Initialize Session (Single Instance)
    const session = useMemo(() => {
        return new LayoutSession([], [], {
            width: 1000,
            height: 800,
            alphaDecay: 0.0228,
            velocityDecay: 0.4
        });
    }, []);

    // 3. Sync Data to Session (Hydration)
    useEffect(() => {
        if (!loading) {
            console.log("Hydrating Session:", nodes.length, "nodes");
            session.syncGraph(nodes, links);
        }
    }, [session, nodes, links, loading]);

    // 4. Initialize Runner
    const runner = useMemo(() => new BasicRunner(session), [session]);

    if (!themeId) return <div className="p-10 text-slate-400">No Theme Context</div>;

    return (
        <div className="w-full h-full bg-slate-50 relative">
            <div className="absolute top-4 right-4 z-10 text-xs text-slate-400 bg-white/50 px-2 rounded">
                CAUSA Strict Renderer
            </div>
            <CLDView nodes={nodes} links={links} session={session} runner={runner} onSelect={onSelect} selection={selection} />
        </div>
    );
};
