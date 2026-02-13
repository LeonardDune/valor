import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { sessionService } from '@/services/sessions';
import { useSessionValidation } from '@/hooks/queries/useSessions';
import { toast } from 'sonner';
import { Loader2, Target } from 'lucide-react';

interface RankingBoardProps {
    sessionId: string;
    onClose: () => void;
    isModerator?: boolean;
}

type Category = 'high' | 'medium' | 'backlog' | 'discard';

const CATEGORIES: { id: Category; label: string; color: string }[] = [
    { id: 'high', label: 'Hoge Prioriteit', color: 'border-green-500/50 bg-green-500/5' },
    { id: 'medium', label: 'Medium Prioriteit', color: 'border-blue-500/50 bg-blue-500/5' },
    { id: 'backlog', label: 'Backlog', color: 'border-amber-500/50 bg-amber-500/5' },
    { id: 'discard', label: 'Verwijderen', color: 'border-red-500/50 bg-red-500/5' }
];

export const RankingBoard: React.FC<RankingBoardProps> = ({ sessionId, onClose, isModerator }) => {
    const queryClient = useQueryClient();
    const [items, setItems] = useState<Record<Category, string[]>>({
        high: [],
        medium: [],
        backlog: [],
        discard: []
    });

    const { data: claims = [], isLoading } = useQuery({
        queryKey: ['eligible-claims', sessionId],
        queryFn: () => sessionService.getEligibleClaims(sessionId)
    });

    const { data: existingRankings = [] } = useQuery({
        queryKey: ['rankings', sessionId],
        queryFn: () => sessionService.getRankings(sessionId)
    });

    // Initialize items from claims and existing rankings
    useEffect(() => {
        if (claims.length > 0) {
            const initialItems: Record<Category, string[]> = {
                high: [],
                medium: [],
                backlog: [],
                discard: []
            };

            // Map existing rankings to categories
            const rankedIds = new Set();
            existingRankings.forEach((r: any) => {
                if (initialItems[r.category as Category]) {
                    initialItems[r.category as Category].push(r.claim_version_id);
                    rankedIds.add(r.claim_version_id);
                }
            });

            // Put unranked claims in backlog
            claims.forEach(c => {
                if (!rankedIds.has(c.id)) {
                    initialItems.backlog.push(c.id);
                }
            });

            setItems(initialItems);
        }
    }, [claims, existingRankings]);

    const { mutate: submitRankings, isPending } = useMutation({
        mutationFn: async () => {
            for (const category of Object.keys(items) as Category[]) {
                for (const claimId of items[category]) {
                    // Optimized: Only submit if changed? For now, re-submit is safer
                    await sessionService.submitRanking(sessionId, claimId, category);
                }
            }
        },
        onSuccess: () => {
            toast.success('Rankings succesvol opgeslagen');
            // Invalidate all relevant queries to ensure UI sync
            queryClient.invalidateQueries({ queryKey: ['rankings', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['validation', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['participation', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['consent-shortlist', sessionId] });
            onClose();
        },
        onError: (error) => {
            console.error('Failed to submit rankings', error);
            toast.error('Fout bij het opslaan van de rankings');
        }
    });

    const advanceStageMutation = useMutation({
        mutationFn: () => sessionService.updateStage(sessionId, 'consent'),
        onSuccess: () => {
            toast.success("Consent fase gestart");
            queryClient.invalidateQueries({ queryKey: ['sessions'] });
            onClose();
        },
        onError: (err) => {
            console.error("Failed to advance stage", err);
            toast.error("Kon fase niet wijzigen");
        }
    });

    const { data: validation } = useSessionValidation(sessionId, 'consent');

    const handleAdvance = () => {
        if (validation && !validation.allowed) {
            toast.error(validation.message);
            return;
        }
        advanceStageMutation.mutate();
    };

    const moveItem = (claimId: string, toCategory: Category) => {
        setItems(prev => {
            const next = { ...prev };
            (Object.keys(next) as Category[]).forEach(cat => {
                next[cat] = next[cat].filter(id => id !== claimId);
            });
            next[toCategory] = [...next[toCategory], claimId];
            return next;
        });
    };

    return (
        <Dialog open onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="max-w-7xl h-[90vh] flex flex-col p-8 gap-8">
                <DialogHeader className="flex-row justify-between items-end space-y-0">
                    <div className="space-y-2">
                        <DialogTitle className="text-3xl font-bold">Ranking & Shortlisting</DialogTitle>
                        <DialogDescription className="text-base text-muted-foreground">
                            Verplaats de claims naar de juiste categorie om de shortlist te bepalen.
                        </DialogDescription>
                    </div>
                    <div className="flex gap-4">
                        <Button variant="ghost" onClick={onClose}>Annuleren</Button>

                        {isModerator && (
                            <div className="flex flex-col items-end gap-1">
                                <Button
                                    variant="outline"
                                    onClick={handleAdvance}
                                    disabled={advanceStageMutation.isPending || (validation && !validation.allowed)}
                                    className={`gap-2 ${validation && !validation.allowed ? "opacity-50 cursor-not-allowed" : ""}`}
                                >
                                    {advanceStageMutation.isPending ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <Target className="h-4 w-4" />
                                    )}
                                    Start Consent Fase
                                </Button>
                                {validation && !validation.allowed && (
                                    <span className="text-[10px] text-red-500 font-medium max-w-[200px] text-right leading-tight">
                                        {validation.message}
                                    </span>
                                )}
                            </div>
                        )}

                        <Button
                            onClick={() => submitRankings()}
                            disabled={isPending || isLoading}
                            className="bg-primary text-primary-foreground min-w-[140px]"
                        >
                            {isPending ? 'Opslaan...' : 'Opslaan & Verder'}
                        </Button>
                    </div>
                </DialogHeader>

                {isLoading ? (
                    <div className="flex-1 flex items-center justify-center">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 flex-1 overflow-hidden">
                        {CATEGORIES.map(cat => (
                            <Card key={cat.id} className={`flex flex-col h-full border-2 ${cat.color} transition-colors shadow-lg overflow-hidden`}>
                                <CardHeader className="pb-2 flex-row justify-between items-center space-y-0">
                                    <CardTitle className="text-sm uppercase tracking-wider font-semibold opacity-70">
                                        {cat.label}
                                    </CardTitle>
                                    <span className="text-xs font-medium text-muted-foreground bg-background/50 px-2 py-0.5 rounded-full border">
                                        {items[cat.id]?.length || 0}
                                    </span>
                                </CardHeader>
                                <CardContent className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
                                    {items[cat.id]?.map(claimId => {
                                        const claim = claims.find(c => c.id === claimId);
                                        if (!claim) return null;
                                        return (
                                            <Card
                                                key={claimId}
                                                className="p-3 bg-card border rounded-md shadow-sm text-sm group relative hover:border-primary/50 transition-all cursor-default"
                                            >
                                                <p className="font-medium lead-tight">"{claim.statement}"</p>

                                                <div className="mt-2 flex flex-wrap gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    {CATEGORIES.filter(c => c.id !== cat.id).map(target => (
                                                        <Button
                                                            key={target.id}
                                                            variant="secondary"
                                                            size="sm"
                                                            onClick={() => moveItem(claimId, target.id)}
                                                            className="h-6 text-[10px] px-2 py-0 font-normal hover:bg-primary hover:text-primary-foreground"
                                                        >
                                                            Naar {target.label.split(' ')[0]}
                                                        </Button>
                                                    ))}
                                                </div>
                                            </Card>
                                        );
                                    })}
                                    {(items[cat.id]?.length === 0 || !items[cat.id]) && (
                                        <div className="h-full flex items-center justify-center border-2 border-dashed rounded-lg opacity-20">
                                            <p className="text-xs font-medium italic">Geen items</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
};

