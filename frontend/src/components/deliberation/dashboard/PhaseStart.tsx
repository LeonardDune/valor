import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Loader2, Play, Users } from 'lucide-react';
import type { VotingSessionConfig } from '@/types/session';

interface PhaseStartProps {
    onStart: (config: VotingSessionConfig) => void;
    isStarting: boolean;
    participantCount?: number;
}

export const PhaseStart: React.FC<PhaseStartProps> = ({ onStart, isStarting, participantCount = 0 }) => {
    const [dots, setDots] = useState<number>(3);
    const [timeLimit, setTimeLimit] = useState<number | ''>('');

    const handleStart = () => {
        onStart({
            dots_per_user: dots,
            time_limit: timeLimit === '' ? null : Number(timeLimit)
        });
    };

    return (
        <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Sessie Instellingen</CardTitle>
                        <CardDescription>Configureer de parameters voor deze stemmingsronde.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label htmlFor="dots">Stemmen per deelnemer</Label>
                            <Input
                                id="dots"
                                type="number"
                                value={dots}
                                onChange={(e) => setDots(Number(e.target.value))}
                                min={1}
                                max={10}
                            />
                            <p className="text-xs text-muted-foreground">
                                Het aantal 'dots' dat elke deelnemer mag verdelen tijdens de prioriteringsfase.
                            </p>
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="time">Tijdslimiet (minuten)</Label>
                            <Input
                                id="time"
                                type="number"
                                value={timeLimit}
                                onChange={(e) => setTimeLimit(e.target.value === '' ? '' : Number(e.target.value))}
                                placeholder="Geen limiet"
                            />
                            <p className="text-xs text-muted-foreground">
                                Optioneel. De sessie sluit niet automatisch, maar toont een timer.
                            </p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Deelnemers</CardTitle>
                        <CardDescription>Overzicht van genodigden.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-primary/10 rounded-full">
                                <Users className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold">{participantCount}</div>
                                <div className="text-sm text-muted-foreground">Geregistreerde gebruikers</div>
                            </div>
                        </div>

                        <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm text-amber-800">
                            <strong>Let op:</strong> Zodra je start, wordt de sessie actief voor alle deelnemers.
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="flex justify-end">
                <Button
                    size="lg"
                    onClick={handleStart}
                    disabled={isStarting}
                    className="w-full md:w-auto"
                >
                    {isStarting ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Sessie Starten...
                        </>
                    ) : (
                        <>
                            <Play className="mr-2 h-4 w-4" />
                            Start Stemsessie
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
};
