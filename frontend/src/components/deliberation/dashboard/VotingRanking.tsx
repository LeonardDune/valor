import React, { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from "@/components/ui/button";
import { sessionService } from '@/services/sessions';
import { api } from '@/services/api';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface VotingRankingProps {
    sessionId: string;
    dsId: string;
    onComplete?: () => void;
}

type Category = 'high' | 'medium' | 'backlog' | 'discard';

const CATEGORIES: { id: Category; label: string; color: string }[] = [
    { id: 'high', label: 'Hoge Prioriteit', color: 'bg-green-500/10 border-green-500/20 text-green-700' },
    { id: 'medium', label: 'Medium Prioriteit', color: 'bg-blue-500/10 border-blue-500/20 text-blue-700' },
    { id: 'backlog', label: 'Backlog', color: 'bg-amber-500/10 border-amber-500/20 text-amber-700' },
    { id: 'discard', label: 'Verwijderen', color: 'bg-red-500/10 border-red-500/20 text-red-700' }
];

export const VotingRanking: React.FC<VotingRankingProps> = ({ sessionId, dsId, onComplete }) => {
    const queryClient = useQueryClient();
    const [items, setItems] = useState<Record<Category, string[]>>({
        high: [],
        medium: [],
        backlog: [],
        discard: []
    });

    // Fetch full claim objects (id + statement) from the DesignSpace
    const { data: allClaims = [], isLoading: isLoadingClaims } = useQuery({
        queryKey: ['claims', dsId],
        queryFn: () => api.getThemeVersionClaims(dsId),
        enabled: !!dsId,
    });

    // Fetch eligible claim IDs (claims without red feedback)
    const { data: eligibleRaw = [], isLoading: isLoadingEligible } = useQuery({
        queryKey: ['eligible-claims', sessionId],
        queryFn: () => sessionService.getEligibleClaims(sessionId),
    });

    const { data: existingRankings = [] } = useQuery({
        queryKey: ['rankings', sessionId],
        queryFn: () => sessionService.getRankings(sessionId),
    });

    // Build eligible claim set from the raw IDs
    const eligibleIds = new Set(eligibleRaw.map((r: any) => r.tessera_base_id));

    // Filter full claims to only those eligible
    const claims = allClaims.filter(c => eligibleIds.has(c.id));

    const isLoading = isLoadingClaims || isLoadingEligible;

    const isInitializedRef = useRef(false);

    // Initialize items — wait until both queries have finished loading
    useEffect(() => {
        if (!isLoadingClaims && !isLoadingEligible && !isInitializedRef.current) {
            const ids = new Set(eligibleRaw.map((r: any) => r.tessera_base_id));
            const eligible = allClaims.filter(c => ids.has(c.id));

            const initialItems: Record<Category, string[]> = {
                high: [],
                medium: [],
                backlog: [],
                discard: []
            };

            const rankedIds = new Set<string>();
            existingRankings.forEach((r: any) => {
                if (initialItems[r.category as Category]) {
                    initialItems[r.category as Category].push(r.tessera_base_id);
                    rankedIds.add(r.tessera_base_id);
                }
            });

            eligible.forEach(c => {
                if (!rankedIds.has(c.id)) {
                    initialItems.backlog.push(c.id);
                }
            });

            setItems(initialItems);
            isInitializedRef.current = true;
        }
    }, [isLoadingClaims, isLoadingEligible, allClaims, eligibleRaw, existingRankings]);

    const { mutate: submitRankings, isPending } = useMutation({
        mutationFn: async () => {
            // Save all categories
            for (const category of Object.keys(items) as Category[]) {
                for (const claimId of items[category]) {
                    await sessionService.submitRanking(sessionId, claimId, category);
                }
            }
        },
        onSuccess: () => {
            toast.success('Rankings opgeslagen');
            queryClient.invalidateQueries({ queryKey: ['rankings', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['validation', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['participation', sessionId] });
            onComplete?.();
        },
        onError: (error) => {
            console.error('Failed to submit rankings', error);
            toast.error('Fout bij opslaan');
        }
    });

    const moveItem = (claimId: string, toCategory: Category) => {
        setItems(prev => {
            const next = { ...prev };
            // Remove from source
            (Object.keys(next) as Category[]).forEach(cat => {
                next[cat] = next[cat].filter(id => id !== claimId);
            });
            // Add to target
            next[toCategory] = [...next[toCategory], claimId];
            return next;
        });
        // Auto-save on move? Maybe safer to explicit save. User asked for interaction like Mod Dashboard.
    };

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;

    const totalItems = Object.values(items).reduce((acc, curr) => acc + curr.length, 0);
    const backlogCount = items.backlog.length;
    const isComplete = totalItems === claims.length && backlogCount < claims.length;

    return (
        <div className="flex flex-col h-full bg-background p-4 gap-4">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Prioritering</h3>
                <div className="flex items-center gap-2">
                    {!isComplete && (
                        <span className="text-xs text-muted-foreground">
                            {backlogCount} items te plaatsen
                        </span>
                    )}
                    <Button size="sm" onClick={() => submitRankings()} disabled={isPending || !isComplete}>
                        {isPending ? 'Afronden...' : 'Prioritering afronden'}
                    </Button>
                </div>
            </div>

            <ScrollArea className="flex-1 pr-2">
                <Accordion type="multiple" defaultValue={['high', 'medium', 'backlog', 'discard']} className="w-full">
                    {CATEGORIES.map(cat => (
                        <AccordionItem value={cat.id} key={cat.id} className="border-b-0 mb-4">
                            <AccordionTrigger className={`px-4 py-2 rounded-t-lg hover:no-underline ${cat.color} border`}>
                                <div className="flex items-center justify-between w-full">
                                    <span>{cat.label}</span>
                                    <Badge variant="secondary" className="bg-background/50 ml-2">{items[cat.id]?.length || 0}</Badge>
                                </div>
                            </AccordionTrigger>
                            <AccordionContent className="p-2 border border-t-0 rounded-b-lg bg-muted/5 min-h-[100px] space-y-2">
                                {items[cat.id]?.map(claimId => {
                                    const claim = claims.find(c => c.id === claimId);
                                    if (!claim) return null;
                                    return (
                                        <Card key={claimId} className="p-3 text-sm flex flex-col gap-2 shadow-sm bg-background">
                                            <p className="font-medium leading-tight">"{claim.statement}"</p>
                                            <div className="flex flex-wrap gap-1 mt-1">
                                                {CATEGORIES.filter(c => c.id !== cat.id).map(target => (
                                                    <Button
                                                        key={target.id}
                                                        variant="outline"
                                                        size="sm"
                                                        className="h-5 text-[10px] px-2 py-0"
                                                        onClick={() => moveItem(claimId, target.id)}
                                                    >
                                                        {target.label}
                                                    </Button>
                                                ))}
                                            </div>
                                        </Card>
                                    );
                                })}
                                {(!items[cat.id] || items[cat.id].length === 0) && (
                                    <p className="text-xs text-muted-foreground italic text-center py-4">Sleep items hierheen (gebruik knoppen)</p>
                                )}
                            </AccordionContent>
                        </AccordionItem>
                    ))}
                </Accordion>
            </ScrollArea>
        </div>
    );
};
