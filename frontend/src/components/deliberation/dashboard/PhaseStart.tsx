import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Loader2, Play, Users } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { VotingSessionConfig } from '@/types/session';

interface Member {
    id: string;
    name: string;
    email: string;
    role: string;
}

interface PhaseStartProps {
    onStart: (config: VotingSessionConfig) => void;
    isStarting: boolean;
    members?: Member[];
}

export const PhaseStart: React.FC<PhaseStartProps> = ({ onStart, isStarting, members = [] }) => {
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

                <Card className="flex flex-col">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Users className="h-4 w-4" />
                            Deelnemers ({members.length})
                        </CardTitle>
                        <CardDescription>Leden van deze DesignSpace.</CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1 flex flex-col gap-3">
                        <ScrollArea className="h-[160px]">
                            <div className="space-y-1.5 pr-2">
                                {members.length === 0 && (
                                    <p className="text-sm text-muted-foreground py-4 text-center">Geen leden gevonden.</p>
                                )}
                                {members.map(m => (
                                    <div key={m.id} className="flex items-center justify-between p-2 rounded-md bg-muted/30 text-sm">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-bold text-primary shrink-0">
                                                {(m.name || m.email)?.[0]?.toUpperCase() ?? '?'}
                                            </div>
                                            <span className="truncate">{m.name || m.email}</span>
                                        </div>
                                        <span className="text-xs text-muted-foreground shrink-0 ml-2 capitalize">{m.role}</span>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>
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
