import React, { useState, useEffect, useCallback } from 'react';
import ChatInterface from '../Chat/ChatInterface';
import CausalGraph from '../Graph/CausalGraph';
import { InspectorSidebar } from '../Graph/InspectorSidebar';
import { api, type Claim } from '../../services/api';
import { FactorModal } from '../Graph/FactorModal';
import { Maximize2, Minimize2 } from 'lucide-react';

interface ValorWorkspaceProps {
    projectId: string;
    projectName: string;
    themeId: string;
    themeName: string;
    onBack: () => void;
}

type AgentType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

export const ValorWorkspace: React.FC<ValorWorkspaceProps> = ({ themeId, projectName, themeName, onBack }) => {
    const [activeAgent, setActiveAgent] = useState<AgentType>('CAUSA');
    const [claims, setClaims] = useState<Claim[]>([]);
    const [factors, setFactors] = useState<any[]>([]);
    const [selection, setSelection] = useState<{ type: 'node' | 'link'; data: any } | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [focusMode, setFocusMode] = useState(false);

    const refreshData = useCallback(async () => {
        try {
            const [existingClaims, themeFactors] = await Promise.all([
                api.getThemeClaims(themeId),
                api.getThemeFactors(themeId)
            ]);
            console.log('WS: Refreshed Data', { claims: existingClaims.length, factors: themeFactors.length, themeFactors });
            setClaims(existingClaims);
            setFactors(themeFactors);
        } catch (error) {
            console.error('Failed to fetch theme data:', error);
        }
    }, [themeId]);

    // Fetch data on mount
    useEffect(() => {
        refreshData();
    }, [refreshData]);

    const handleClaimsUpdate = async (newClaims: Claim[]) => {
        setClaims(prev => {
            const existingIds = new Set(prev.map(c => c.id));
            const filteredNew = newClaims.filter(c => !existingIds.has(c.id));
            return [...prev, ...filteredNew];
        });
        // Important: Refresh factors too as chat agent might have created new ones
        await refreshData();
    };

    const handleSaveFactor = async (name: string, type: any, description: string) => {
        try {
            await api.createFactor(themeId, name, description, type);
            refreshData();
        } catch (error) {
            console.error('Failed to create factor', error);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-white overflow-hidden">
            <header className="h-14 border-b border-slate-200 flex items-center justify-between px-4 bg-white shrink-0 z-30">
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors">
                        ←
                    </button>
                    <div className="flex flex-col">
                        <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold leading-none mb-1">{projectName}</span>
                        <span className="text-sm font-bold text-slate-900 leading-none">{themeName}</span>
                    </div>
                </div>

                <div className="flex bg-slate-100 p-1 rounded-xl">
                    <AgentButton label="CAUSA" isActive={activeAgent === 'CAUSA'} onClick={() => setActiveAgent('CAUSA')} />
                    <AgentButton label="AXIA" isActive={activeAgent === 'AXIA'} onClick={() => setActiveAgent('AXIA')} isDisabled={true} />
                    <AgentButton label="ACTOR" isActive={activeAgent === 'ACTOR'} onClick={() => setActiveAgent('ACTOR')} isDisabled={true} />
                    <AgentButton label="PRAXIS" isActive={activeAgent === 'PRAXIS'} onClick={() => setActiveAgent('PRAXIS')} isDisabled={true} />
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setFocusMode(!focusMode)}
                        className={`p-2 rounded-lg transition-all ${focusMode ? 'bg-blue-50 text-blue-600' : 'text-slate-400 hover:bg-slate-100'}`}
                        title={focusMode ? "Exit Focus Mode" : "Enter Focus Mode"}
                    >
                        {focusMode ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
                    </button>
                </div>
            </header>

            <main className="flex-1 flex overflow-hidden relative">
                {activeAgent === 'CAUSA' ? (
                    <div className="flex-1 flex overflow-hidden">
                        {/* Left: Chat */}
                        {!focusMode && (
                            <div className="w-[400px] border-r border-slate-200 bg-white flex flex-col h-full shrink-0 z-10 transition-all duration-300">
                                <ChatInterface topic={themeName} onClaimsUpdate={handleClaimsUpdate} />
                            </div>
                        )}

                        {/* Middle: Graph */}
                        <div className="flex-1 bg-slate-50 h-full relative overflow-hidden transition-all duration-300">
                            <div className="absolute top-4 left-4 z-20 flex gap-2">
                                <div className="bg-white/90 backdrop-blur-md border border-slate-200 px-3 py-1.5 rounded-full text-[10px] font-bold text-slate-500 shadow-sm uppercase tracking-wider">
                                    Causaal Model
                                </div>
                                <button
                                    onClick={() => setIsModalOpen(true)}
                                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-full text-[10px] font-bold shadow-md shadow-blue-200 transition-all hover:scale-105 active:scale-95 uppercase tracking-wider"
                                >
                                    + Nieuwe Factor
                                </button>
                            </div>
                            <CausalGraph
                                claims={claims}
                                factors={factors}
                                onSelect={setSelection}
                                selectedId={selection?.data?.id}
                            />
                        </div>

                        {/* Right: Sidebar */}
                        {selection && !focusMode && (
                            <InspectorSidebar
                                selection={selection}
                                themeId={themeId}
                                factors={factors}
                                onClose={() => setSelection(null)}
                                onRefresh={refreshData}
                            />
                        )}
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center bg-slate-50 text-slate-400">
                        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4 text-slate-300">
                            ?
                        </div>
                        <p className="font-medium">Module {activeAgent} is nog in ontwikkeling.</p>
                        <p className="text-sm">We werken hard aan de volgende stap in de analyse.</p>
                    </div>
                )}
            </main>

            <FactorModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSaveFactor}
            />
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
