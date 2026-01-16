import React, { useState, useEffect, useCallback } from 'react';
import ChatInterface from '../Chat/ChatInterface';
// import CausalGraph from '../Graph/CausalGraph';
// import { ReactFlowCanvas } from '../Graph/ReactFlowCanvas';
import { InspectorSidebar } from '../Graph/InspectorSidebar';
import { CausaShell } from '../../perspectives/causa';
import { api, type Claim } from '../../services/api';
import { FactorModal } from '../Graph/FactorModal';
import { Maximize2, Minimize2, PanelLeftClose, PanelLeftOpen, ArrowLeft } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

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
    // const [claims, setClaims] = useState<Claim[]>([]);
    const [factors, setFactors] = useState<any[]>([]);
    const [selection, setSelection] = useState<{ type: 'node' | 'link'; data: any } | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isChatOpen, setIsChatOpen] = useState(true);
    const [focusMode, setFocusMode] = useState(false);

    const refreshData = useCallback(async () => {
        try {
            const [existingClaims, themeFactors] = await Promise.all([
                api.getThemeClaims(themeId),
                api.getThemeFactors(themeId)
            ]);
            console.log('WS: Refreshed Data', { claims: existingClaims.length, factors: themeFactors.length, themeFactors });
            // setClaims(existingClaims);
            setFactors(themeFactors);
        } catch (error) {
            console.error('Failed to fetch theme data:', error);
        }
    }, [themeId]);

    // Fetch data on mount
    useEffect(() => {
        refreshData();
    }, [refreshData]);

    const handleClaimsUpdate = async (_newClaims: Claim[]) => {
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
        <div className="flex flex-col h-screen bg-background overflow-hidden">
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
                        {/* Left: Chat */}
                        <div
                            className={`border-r border-border bg-background flex flex-col h-full shrink-0 z-10 transition-all duration-300 ease-in-out overflow-hidden ${!focusMode && isChatOpen ? 'w-[400px] opacity-100' : 'w-0 opacity-0 border-none'
                                }`}
                        >
                            <div className="w-[400px] h-full">
                                <ChatInterface topic={themeName} onClaimsUpdate={handleClaimsUpdate} />
                            </div>
                        </div>

                        {/* Middle: Graph */}
                        <div className="flex-1 bg-muted/30 h-full relative overflow-hidden transition-all duration-300">
                            <div className="absolute top-4 left-4 z-20 flex gap-2 items-center">
                                <Button
                                    variant="outline"
                                    size="icon"
                                    onClick={() => setIsChatOpen(!isChatOpen)}
                                    className="h-8 w-8 bg-background/90 backdrop-blur"
                                    title={isChatOpen ? "Verberg Agent" : "Toon Agent"}
                                >
                                    {isChatOpen ? <PanelLeftClose size={14} /> : <PanelLeftOpen size={14} />}
                                </Button>
                                <Badge variant="outline" className="bg-background/90 backdrop-blur font-bold uppercase tracking-wider text-[10px]">
                                    Causaal Model
                                </Badge>
                            </div>

                            <CausaShell themeId={themeId} />
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
                    <div className="flex-1 flex flex-col items-center justify-center bg-muted/10 text-muted-foreground">
                        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4 text-muted-foreground/50">
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
