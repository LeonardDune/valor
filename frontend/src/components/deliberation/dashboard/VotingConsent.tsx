import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { sessionService } from '@/services/sessions';
import type { ShortlistClaim } from '@/services/api';
import { toast } from 'sonner';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

interface VotingConsentProps {
    sessionId: string;
    onComplete?: () => void;
}

export const VotingConsent: React.FC<VotingConsentProps> = ({ sessionId, onComplete }) => {
    const queryClient = useQueryClient();
    const [objectionTarget, setObjectionTarget] = useState<ShortlistClaim | null>(null);
    const [motivation, setMotivation] = useState('');

    const { data: claims = [], isLoading } = useQuery({
        queryKey: ['consent-shortlist', sessionId],
        queryFn: () => sessionService.getConsentShortlist(sessionId)
    });

    const { mutate: vote, isPending: isVoting } = useMutation({
        mutationFn: async ({ claimId, type, motivation }: { claimId: string; type: 'approve' | 'object'; motivation?: string }) => {
            await sessionService.submitConsentVote(sessionId, {
                session_id: sessionId,
                claim_version_id: claimId,
                vote: type,
                motivation
            });
        },
        onSuccess: () => {
            toast.success('Stem succesvol verwerkt');
            queryClient.invalidateQueries({ queryKey: ['consent-shortlist', sessionId] });
            queryClient.invalidateQueries({ queryKey: ['participation', sessionId] });
            setObjectionTarget(null);
            setMotivation('');
        },
        onError: () => toast.error('Fout bij stemmen')
    });

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;

    const sortedClaims = [...claims].sort((a, b) => {
        // Unvoted first
        if (!a.user_vote && b.user_vote) return -1;
        if (a.user_vote && !b.user_vote) return 1;
        return 0;
    });

    const voteCount = claims.filter(c => c.user_vote).length;
    const isComplete = voteCount === claims.length;

    return (
        <div className="flex flex-col h-full bg-background overflow-hidden relative">
            <div className="p-4 border-b bg-muted/5">
                <h3 className="font-semibold">Instemming</h3>
                <p className="text-xs text-muted-foreground">Geef akkoord of bezwaar per claim.</p>
            </div>

            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                    {sortedClaims.filter(c => c.status !== 'rejected').map(claim => (
                        <Card key={claim.id} className={`transition-all ${claim.user_vote ? 'opacity-70' : ''}`}>
                            <CardContent className="p-4 space-y-3">
                                <div className="flex justify-between items-start gap-2">
                                    <p className="text-sm font-medium leading-tight">"{claim.statement}"</p>
                                    {claim.high_p >= 0.8 && <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />}
                                </div>

                                {claim.user_vote ? (
                                    <div className={`text-xs font-bold uppercase p-2 rounded text-center border ${claim.user_vote === 'approve' ? 'bg-green-500/10 text-green-700 border-green-500/20' : 'bg-red-500/10 text-red-700 border-red-500/20'
                                        }`}>
                                        {claim.user_vote === 'approve' ? 'Akkoord Ingediend' : 'Bezwaar Ingediend'}
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-2 gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="border-green-500/20 hover:bg-green-500 hover:text-white text-green-700"
                                            onClick={() => vote({ claimId: claim.id, type: 'approve' })}
                                            disabled={isVoting}
                                        >
                                            <CheckCircle2 className="mr-1 h-3 w-3" /> Akkoord
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="border-red-500/20 hover:bg-red-500 hover:text-white text-red-700"
                                            onClick={() => setObjectionTarget(claim)}
                                            disabled={isVoting}
                                        >
                                            <XCircle className="mr-1 h-3 w-3" /> Bezwaar
                                        </Button>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                    {sortedClaims.length === 0 && (
                        <div className="text-center p-8 text-muted-foreground italic">Geen claims om te beoordelen.</div>
                    )}
                </div>
            </ScrollArea>

            {/* Objection Dialog - Rendered inside this component context (Portal) */}
            <Dialog open={!!objectionTarget} onOpenChange={(open) => !open && setObjectionTarget(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Bezwaar Motiveren</DialogTitle>
                        <DialogDescription>Waarom heb je bezwaar?</DialogDescription>
                    </DialogHeader>
                    <Textarea
                        value={motivation}
                        onChange={e => setMotivation(e.target.value)}
                        placeholder="Motivatie..."
                        className="min-h-[100px]"
                    />
                    <DialogFooter>
                        <Button variant="ghost" onClick={() => setObjectionTarget(null)}>Annuleren</Button>
                        <Button
                            onClick={() => vote({ claimId: objectionTarget!.id, type: 'object', motivation })}
                            disabled={!motivation.trim() || isVoting}
                        >
                            Indienen
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
            <div className="p-4 border-t bg-background flex flex-col gap-2">
                {!isComplete && (
                    <p className="text-[10px] text-muted-foreground text-center px-2 leading-tight">
                        Stem op alle {claims.length} claims om af te kunnen ronden ({claims.length - voteCount} te gaan).
                    </p>
                )}
                <div className="flex justify-end w-full">
                    <Button onClick={() => onComplete?.()} className="gap-2" disabled={!isComplete}>
                        <CheckCircle2 className="h-4 w-4" />
                        Consent Afronden
                    </Button>
                </div>
            </div>
        </div>
    );
};
