import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, Clock, Gavel, Loader2 } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ConfirmModal } from '@/components/ui/ConfirmModal';

import type { Participation } from '@/types/session';

interface PhaseConsentProps {
    participants: Participation[];
    onFinalize: () => void;
    isFinalizing: boolean;
}

export const PhaseConsent: React.FC<PhaseConsentProps> = ({
    participants,
    onFinalize,
    isFinalizing
}) => {
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);
    const total = participants.length;
    const completed = participants.filter(p => p.has_completed_consent || p.has_consent).length;
    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

    return (
        <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Voortgang Instemming</CardTitle>
                        <CardDescription>Deelnemers stemmen op het voorstel.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Voltooid</span>
                                <span className="font-medium">{completed} / {total} ({percentage}%)</span>
                            </div>
                            <Progress value={percentage} className="h-2" />
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-4">
                            <div className="flex flex-col items-center justify-center p-4 bg-muted/20 rounded-lg border border-dashed">
                                <CheckCircle className="h-6 w-6 text-green-500 mb-2" />
                                <span className="text-2xl font-bold">{completed}</span>
                                <span className="text-xs text-muted-foreground">Gestemd</span>
                            </div>
                            <div className="flex flex-col items-center justify-center p-4 bg-muted/20 rounded-lg border border-dashed">
                                <Clock className="h-6 w-6 text-amber-500 mb-2" />
                                <span className="text-2xl font-bold">{total - completed}</span>
                                <span className="text-xs text-muted-foreground">Wachtend</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="flex flex-col">
                    <CardHeader>
                        <CardTitle>Status per Deelnemer</CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 min-h-[200px] p-0 relative">
                        <ScrollArea className="h-[200px] w-full px-6">
                            <div className="space-y-2 pb-4">
                                {participants.map((p) => (
                                    <div key={p.user_id} className="flex items-center justify-between p-2 rounded-md bg-muted/30">
                                        <div className="flex items-center gap-2">
                                            <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-bold text-primary">
                                                {p.user_name ?? p.name?.[0]?.toUpperCase() || '?'}
                                            </div>
                                            <div className="text-sm truncate max-w-[150px]">
                                                {p.user_name ?? p.name || 'Onbekend'}
                                            </div>
                                        </div>
                                        {(p.has_completed_consent || p.has_consent) ? (
                                            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded flex items-center gap-1">
                                                <CheckCircle className="h-3 w-3" /> Gestemd
                                            </span>
                                        ) : (
                                            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded flex items-center gap-1">
                                                <Clock className="h-3 w-3" /> Wachtend
                                            </span>
                                        )}
                                    </div>
                                ))}
                                {participants.length === 0 && (
                                    <div className="text-center text-muted-foreground py-8 text-sm">
                                        Geen deelnemers gevonden.
                                    </div>
                                )}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>
            </div>

            <div className="flex justify-end">
                <Button
                    size="lg"
                    variant="default"
                    className="bg-green-600 hover:bg-green-700 w-full md:w-auto"
                    onClick={() => setIsConfirmOpen(true)}
                    disabled={isFinalizing}
                >
                    {isFinalizing ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                        <Gavel className="mr-2 h-4 w-4" />
                    )}
                    Besluit Finaliseren
                </Button>
            </div>

            <ConfirmModal
                isOpen={isConfirmOpen}
                onCancel={() => setIsConfirmOpen(false)}
                onConfirm={() => {
                    setIsConfirmOpen(false);
                    onFinalize();
                }}
                title="Besluit Finaliseren"
                message="Weet je zeker dat je dit besluit wilt finaliseren? Er wordt een nieuwe versie van het thema aangemaakt met de gekozen claims. Dit kan niet ongedaan gemaakt worden."
                confirmLabel="Finaliseren"
                isDanger={false}
            />
        </div>
    );
};
