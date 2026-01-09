import React, { useState } from 'react';
import ChatInterface from '../Chat/ChatInterface';
import CausalGraph from '../Graph/CausalGraph';
import type { Claim } from '../../services/api';

interface ValorWorkspaceProps {
    projectId: string;
    projectName: string;
    themeId: string;
    themeName: string;
    onBack: () => void;
}

type AgentType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

export const ValorWorkspace: React.FC<ValorWorkspaceProps> = ({ projectName, themeName, onBack }) => {
    const [activeAgent, setActiveAgent] = useState<AgentType>('CAUSA');
    const [claims, setClaims] = useState<Claim[]>([]);

    // TODO: Fetch claims for this specific theme/session on mount

    const handleClaimsUpdate = (newClaims: Claim[]) => {
        // Deduplicate and merge logic (reused from App.tsx)
        setClaims(prev => {
            const prevIds = prev.map(c => c.id);
            const existingIds = new Set(prevIds);
            const filteredNew = newClaims.filter(c => !existingIds.has(c.id));
            return [...prev, ...filteredNew];
        });
    };

    return (
        <div className="flex flex-col h-screen bg-white overflow-hidden">
            {/* Top Navigation Bar */}
            <header className="h-14 border-b border-slate-200 flex items-center justify-between px-4 bg-white shrink-0 z-10">
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg text-slate-500">
                        ←
                    </button>
                    <div className="flex flex-col">
                        <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">{projectName}</span>
                        <span className="text-sm font-bold text-slate-900">{themeName}</span>
                    </div>
                </div>

                {/* Agent/Module Selector */}
                <div className="flex bg-slate-100 p-1 rounded-lg">
                    <AgentButton
                        label="CAUSA (Oorzaken)"
                        isActive={activeAgent === 'CAUSA'}
                        onClick={() => setActiveAgent('CAUSA')}
                    />
                    <AgentButton
                        label="AXIA (Waarden)"
                        isActive={activeAgent === 'AXIA'}
                        onClick={() => setActiveAgent('AXIA')}
                        isDisabled={true}
                    />
                    <AgentButton
                        label="ACTOR (Belangen)"
                        isActive={activeAgent === 'ACTOR'}
                        onClick={() => setActiveAgent('ACTOR')}
                        isDisabled={true}
                    />
                    <AgentButton
                        label="PRAXIS (Oplossingen)"
                        isActive={activeAgent === 'PRAXIS'}
                        onClick={() => setActiveAgent('PRAXIS')}
                        isDisabled={true}
                    />
                </div>

                <div className="w-24"></div> {/* Spacer for balance */}
            </header>

            {/* Main Workspace Content */}
            <div className="flex-1 flex overflow-hidden relative">

                {activeAgent === 'CAUSA' && (
                    <>
                        {/* Left: Chat Interface */}
                        <div className="w-[400px] border-r border-slate-200 bg-white flex flex-col h-full shrink-0">
                            <ChatInterface topic={themeName} onClaimsUpdate={handleClaimsUpdate} />
                        </div>

                        {/* Right: Causal Graph */}
                        <div className="flex-1 bg-slate-50 h-full relative">
                            <div className="absolute top-4 left-4 z-10 bg-white/80 backdrop-blur border border-slate-200 px-3 py-1 rounded-full text-xs font-medium text-slate-600 shadow-sm">
                                Causaal Model
                            </div>
                            <CausalGraph claims={claims} />
                        </div>
                    </>
                )}

                {/* Future Agent Placeholders */}
                {activeAgent !== 'CAUSA' && (
                    <div className="flex-1 flex items-center justify-center bg-slate-50 text-slate-400">
                        Module {activeAgent} is nog in ontwikkeling.
                    </div>
                )}

            </div>
        </div>
    );
};

const AgentButton = ({ label, isActive, onClick, isDisabled = false }: any) => (
    <button
        onClick={onClick}
        disabled={isDisabled}
        className={`
            px-3 py-1.5 text-xs font-medium rounded-md transition-all
            ${isActive
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-slate-500 hover:text-slate-800 hover:bg-slate-200/50'}
            ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
    >
        {label}
        {isDisabled && <span className="ml-1 text-[10px] opacity-70">(Binnenkort)</span>}
    </button>
);
