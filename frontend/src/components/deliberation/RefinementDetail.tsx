// 
import React from 'react';
import { type Claim, type Factor } from '@/services/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MessageSquare, ExternalLink, Info, ShieldCheck, BrainCircuit, Network } from 'lucide-react';
import { MiniGraph } from './MiniGraph.tsx';
import { FloatingThreadPanel } from '@/components/Chat/FloatingThreadPanel.tsx';

interface RefinementDetailProps {
    claim: Claim | null;
    allClaims: Claim[];
    factors?: Factor[];
}

export const RefinementDetail: React.FC<RefinementDetailProps> = ({ claim, allClaims, factors = [] }) => {
    const [activeThread, setActiveThread] = React.useState<{ targetId: string, label: string, initialThreadId?: string } | null>(null);

    const factorMap = React.useMemo(() => {
        const map = new Map<string, string>();
        factors.forEach(f => map.set(f.id, f.name));
        return map;
    }, [factors]);

    const getSourceName = (c: Claim) => c.source_node || (c.source_id ? factorMap.get(c.source_id) : null) || c.source_id?.substring(0, 8) || 'Onbekend';
    const getTargetName = (c: Claim) => c.target_node || (c.target_id ? factorMap.get(c.target_id) : null) || c.target_id?.substring(0, 8) || 'Onbekend';

    if (!claim) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-8 text-center">
                <Info className="h-12 w-12 mb-4 opacity-10" />
                <p>Selecteer een claim aan de linkerkant om de details te bekijken.</p>
            </div>
        );
    }

    const openThread = (targetId: string, label: string, initialThreadId?: string) => {
        setActiveThread({ targetId, label, initialThreadId });
    };

    return (
        <article className="flex flex-col h-full bg-background">
            <header className="p-6 border-b border-border bg-background sticky top-0 z-10">
                <div className="flex items-center gap-2 mb-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    <ShieldCheck className="h-3 w-3" />
                    <span>Geselecteerde Claim</span>
                </div>
                <h2 className="text-2xl font-extrabold tracking-tight mb-6 leading-tight bg-clip-text text-transparent bg-gradient-to-br from-foreground to-foreground/70">
                    {claim.statement}
                </h2>

                <div className="flex flex-wrap gap-4 items-center text-sm text-muted-foreground">
                    <section className="flex items-center gap-2">
                        <span className="font-semibold text-foreground uppercase text-[10px] bg-muted px-1.5 py-0.5 rounded">Bron:</span>
                        <span className="font-medium">{getSourceName(claim)}</span>
                    </section>
                    <section className="flex items-center gap-2">
                        <span className="font-semibold text-foreground uppercase text-[10px] bg-muted px-1.5 py-0.5 rounded">Doel:</span>
                        <span className="font-medium">{getTargetName(claim)}</span>
                    </section>
                    <section className="flex items-center gap-2">
                        <span className="font-semibold text-foreground uppercase text-[10px] bg-muted px-1.5 py-0.5 rounded">Status:</span>
                        <Badge variant="outline" className="capitalize text-[10px] h-5">{claim.status || 'Actief'}</Badge>
                    </section>
                </div>
            </header>

            <div className="flex-1 p-6 space-y-8">
                {/* MiniGraph Context */}
                <section className="space-y-3">
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                        <Network className="h-3 w-3" />
                        Visuele Context
                    </div>
                    <MiniGraph
                        selectedClaim={claim}
                        allClaims={allClaims}
                        factors={factors}
                        className="mb-2"
                    />
                </section>
                <Tabs defaultValue="arguments" className="w-full">
                    <TabsList className="grid w-full grid-cols-3 mb-8">
                        <TabsTrigger value="arguments" className="gap-2">
                            <MessageSquare className="h-4 w-4" />
                            Argumenten
                        </TabsTrigger>
                        <TabsTrigger value="evidence" className="gap-2">
                            <ShieldCheck className="h-4 w-4" />
                            Bewijs
                        </TabsTrigger>
                        <TabsTrigger value="ai-notes" className="gap-2">
                            <BrainCircuit className="h-4 w-4" />
                            AI Notities
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="arguments" className="space-y-6">
                        <div className="prose prose-sm max-w-none text-muted-foreground">
                            <p>Bekijk de lopende discussies over de factoren en claims die betrokken zijn bij dit argument.</p>
                        </div>

                        <ul className="grid gap-3 p-0 list-none">
                            {claim.source_id && (
                                <li>
                                    <ThreadLink
                                        label={`Discussie over ${getSourceName(claim)}`}
                                        onClick={() => openThread(claim.source_id!, getSourceName(claim), claim.source_thread_id)}
                                    />
                                </li>
                            )}
                            {claim.target_id && (
                                <li>
                                    <ThreadLink
                                        label={`Discussie over ${getTargetName(claim)}`}
                                        onClick={() => openThread(claim.target_id!, getTargetName(claim), claim.target_thread_id)}
                                    />
                                </li>
                            )}
                            {claim.id && (
                                <li>
                                    <ThreadLink
                                        label="Discussie over deze Claim"
                                        onClick={() => openThread(claim.id!, "Deze Claim", claim.claim_thread_id)}
                                    />
                                </li>
                            )}
                        </ul>
                    </TabsContent>

                    <TabsContent value="evidence" className="text-center py-12">
                        <section className="max-w-xs mx-auto space-y-4">
                            <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                                <ShieldCheck className="h-6 w-6 text-muted-foreground opacity-50" />
                            </div>
                            <h4 className="font-semibold text-foreground">Bewijslast</h4>
                            <p className="text-sm text-muted-foreground">
                                De mogelijkheid om brondocumenten en citaten te koppelen aan claims komt binnenkort beschikbaar.
                            </p>
                            <Badge variant="secondary" className="uppercase text-[10px]">TO DO</Badge>
                        </section>
                    </TabsContent>

                    <TabsContent value="ai-notes" className="text-center py-12">
                        <section className="max-w-xs mx-auto space-y-4">
                            <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                                <BrainCircuit className="h-6 w-6 text-muted-foreground opacity-50" />
                            </div>
                            <h4 className="font-semibold text-foreground">AI Analyse</h4>
                            <p className="text-sm text-muted-foreground">
                                Automatische samenvattingen en inconsistentie-detectie voor claims zijn momenteel in ontwikkeling.
                            </p>
                            <Badge variant="secondary" className="uppercase text-[10px]">BINNENKORT</Badge>
                        </section>
                    </TabsContent>
                </Tabs>
            </div>

            {activeThread && (
                <FloatingThreadPanel
                    targetId={activeThread.targetId}
                    targetLabel={activeThread.label}
                    initialThreadId={activeThread.initialThreadId}
                    onClose={() => setActiveThread(null)}
                    readOnly={true}
                />
            )}
        </article>
    );
};

const ThreadLink: React.FC<{ label: string; onClick: () => void }> = ({ label, onClick }) => (
    <Button
        variant="outline"
        className="w-full justify-between h-auto py-4 px-4 hover:border-primary hover:bg-primary/5 group"
        onClick={onClick}
    >
        <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                <MessageSquare className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
            </div>
            <span className="font-medium">{label}</span>
        </div>
        <ExternalLink className="h-4 w-4 text-muted-foreground opacity-50 group-hover:opacity-100 group-hover:text-primary transition-all" />
    </Button>
);
