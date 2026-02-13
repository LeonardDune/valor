import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Focus } from "lucide-react";
import { sessionService } from '@/services/sessions';
import type { Claim } from '@/services/api';

interface FocusBoardProps {
    sessionId: string;
    claims: Claim[];
    onClose: () => void;
}

export const FocusBoard: React.FC<FocusBoardProps> = ({ sessionId, claims, onClose }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [motivation, setMotivation] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const currentClaim = claims[currentIndex];

    const handleSubmitFeedback = async (color: 'green' | 'amber' | 'red') => {
        if (color === 'red' && !motivation.trim()) {
            alert('Motivatie is verplicht voor rode feedback.');
            return;
        }

        setIsSubmitting(true);
        try {
            await sessionService.submitFeedback(sessionId, currentClaim.id, color, motivation);

            if (currentIndex < claims.length - 1) {
                setCurrentIndex(prev => prev + 1);
                setMotivation('');
            } else {
                onClose();
            }
        } catch (error) {
            console.error('Feedback submission failed', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!currentClaim) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <Card className="w-full max-w-2xl shadow-2xl border-primary/20">
                <CardHeader>
                    <div className="flex justify-between items-center">
                        <CardTitle className="text-2xl font-bold flex items-center gap-2">
                            <Focus className="h-6 w-6 text-primary" />
                            Focus Mode: Deliberatie
                        </CardTitle>
                        <span className="text-sm text-muted-foreground">
                            Claim {currentIndex + 1} van {claims.length}
                        </span>
                    </div>
                    <CardDescription>
                        Beoordeel de onderstaande claim met het stoplicht-systeem.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="p-6 bg-muted/30 rounded-lg border border-border italic text-lg text-center">
                        "{currentClaim.statement}"
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <Button
                            variant="outline"
                            className="h-24 flex flex-col gap-2 border-green-500/50 hover:bg-green-500/10 text-green-600 dark:text-green-400"
                            onClick={() => handleSubmitFeedback('green')}
                            disabled={isSubmitting}
                        >
                            <div className="w-4 h-4 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
                            <span>Eens (Groen)</span>
                        </Button>
                        <Button
                            variant="outline"
                            className="h-24 flex flex-col gap-2 border-amber-500/50 hover:bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            onClick={() => handleSubmitFeedback('amber')}
                            disabled={isSubmitting}
                        >
                            <div className="w-4 h-4 rounded-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]" />
                            <span>Nuance (Oranje)</span>
                        </Button>
                        <Button
                            variant="outline"
                            className="h-24 flex flex-col gap-2 border-red-500/50 hover:bg-red-500/10 text-red-600 dark:text-red-400"
                            onClick={() => handleSubmitFeedback('red')}
                            disabled={isSubmitting}
                        >
                            <div className="w-4 h-4 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]" />
                            <span>Oneens (Rood)</span>
                        </Button>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium">Motivatie (verplicht bij Rood)</label>
                        <Textarea
                            placeholder="Beschrijf waarom u deze claim wilt verfijnen of waarom u het er niet mee eens bent..."
                            value={motivation}
                            onChange={(e) => setMotivation(e.target.value)}
                            className="min-h-[100px]"
                        />
                    </div>

                    <div className="flex justify-between items-center pt-4">
                        <Button variant="ghost" onClick={onClose}>Annuleren</Button>
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))} disabled={currentIndex === 0}>Vorige</Button>
                            <Button variant="outline" onClick={() => setCurrentIndex(prev => Math.min(claims.length - 1, prev + 1))} disabled={currentIndex === claims.length - 1}>Slaan Over</Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
