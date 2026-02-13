import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

import { sessionService } from '@/services/sessions';
import type { ShortlistClaim } from '@/services/api';
import { toast } from 'sonner';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

interface ConsentBoardProps {
    sessionId: string;
    onClose: () => void;
    isModerator?: boolean;
}

export const ConsentBoard: React.FC<ConsentBoardProps> = ({ sessionId, onClose }) => {
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
            queryClient.invalidateQueries({ queryKey: ['validation', sessionId] });
            setObjectionTarget(null);
            setMotivation('');
        },
        onError: (error) => {
            console.error('Failed to submit vote', error);
            toast.error('Fout bij het verwerken van de stem');
        }
    });

    // advanceStageMutation removed - Finalization is now Moderator-only via Dashboard


    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'high_p':
                return (
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 border border-green-500/20 text-[10px] font-bold uppercase tracking-wider">
                        <CheckCircle2 className="h-3 w-3" />
                        Groot Draagvlak
                    </div>
                );
            case 'medium_p':
                return (
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 border border-blue-500/20 text-[10px] font-bold uppercase tracking-wider">
                        <AlertCircle className="h-3 w-3" />
                        Voldoende Draagvlak
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <Dialog open onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="max-w-5xl h-[90vh] flex flex-col p-8 gap-8">
                <DialogHeader>
                    <div className="flex justify-between items-start">
                        <div className="space-y-2">
                            <DialogTitle className="text-3xl font-bold">Besluitvorming</DialogTitle>
                            <DialogDescription className="text-base text-muted-foreground">
                                Geef per claim aan of je akkoord gaat of een gemotiveerd bezwaar hebt.
                            </DialogDescription>
                        </div>
                        <div className="flex gap-2">

                            <Button variant="ghost" onClick={onClose}>Sluiten</Button>
                        </div>
                    </div>
                </DialogHeader>

                {isLoading ? (
                    <div className="flex-1 flex items-center justify-center">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                ) : (
                    <div className="flex-1 overflow-y-auto pr-4 space-y-4 custom-scrollbar">
                        {claims.filter(c => c.status !== 'rejected').map(claim => (
                            <Card key={claim.id} className="border-l-4 border-l-primary/20 hover:border-l-primary transition-all">
                                <CardContent className="p-6 flex justify-between items-center gap-6">
                                    <div className="space-y-2 flex-1">
                                        <div className="flex items-center gap-3">
                                            {getStatusBadge(claim.status)}
                                            <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold opacity-50">
                                                Draagvlak: {(claim.high_p * 100).toFixed(0)}% Hoog
                                            </span>
                                        </div>
                                        <p className="text-lg font-medium leading-tight italic">
                                            "{claim.statement}"
                                        </p>
                                    </div>

                                    <div className="flex gap-2">
                                        <Button
                                            variant={claim.user_vote === 'approve' ? 'default' : 'outline'}
                                            className={`transition-colors ${claim.user_vote === 'approve' ? 'bg-green-600 hover:bg-green-700 border-transparent text-white' : 'border-green-500/20 hover:bg-green-500 hover:text-white'}`}
                                            onClick={() => vote({ claimId: claim.id, type: 'approve' })}
                                            disabled={isVoting || !!claim.user_vote}
                                        >
                                            {claim.user_vote === 'approve' ? 'Akkoord (Ingediend)' : 'Akkoord'}
                                        </Button>
                                        <Button
                                            variant={claim.user_vote === 'object' ? 'destructive' : 'outline'}
                                            className={`transition-colors ${claim.user_vote === 'object' ? 'bg-red-600 hover:bg-red-700 border-transparent text-white' : 'border-red-500/20 hover:bg-red-500 hover:text-white'}`}
                                            onClick={() => setObjectionTarget(claim)}
                                            disabled={isVoting || (!!claim.user_vote && claim.user_vote !== 'object')}
                                        >
                                            {claim.user_vote === 'object' ? 'Bezwaar (Ingediend)' : 'Bezwaar'}
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}

                        {claims.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center opacity-40 py-20">
                                <AlertCircle className="h-12 w-12 mb-4" />
                                <p className="text-xl font-medium italic">Geen shortlisted claims gevonden</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Objection Motivation Dialog */}
                <Dialog open={!!objectionTarget} onOpenChange={(open) => !open && setObjectionTarget(null)}>
                    <DialogContent className="max-w-lg">
                        <DialogHeader>
                            <DialogTitle>Bezwaar Motiveren</DialogTitle>
                            <DialogDescription>
                                Waarom heb je bezwaar tegen deze claim? Jouw motivatie helpt bij de verdere dialoog.
                            </DialogDescription>
                        </DialogHeader>

                        <div className="py-4">
                            <p className="text-sm italic mb-4 bg-muted p-3 rounded">
                                "{objectionTarget?.statement}"
                            </p>
                            <Textarea
                                placeholder="Typ hier je motivatie..."
                                value={motivation}
                                onChange={(e) => setMotivation(e.target.value)}
                                className="min-h-[120px]"
                            />
                        </div>

                        <DialogFooter>
                            <Button variant="ghost" onClick={() => setObjectionTarget(null)}>Annuleren</Button>
                            <Button
                                disabled={!motivation.trim() || isVoting}
                                onClick={() => vote({ claimId: objectionTarget!.id, type: 'object', motivation })}
                            >

                                {objectionTarget?.user_vote === 'object' ? 'Motivatie Updaten' : 'Bezwaar Indienen'}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </DialogContent>
        </Dialog>
    );
};
