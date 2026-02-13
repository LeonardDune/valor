import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, CheckCircle, Loader2, X } from 'lucide-react';
import { useSessionParticipation, useUpdateSessionStage, useFinalizeDeliberation, useSessionValidation } from '@/hooks/queries/useSessions';
import { toast } from 'sonner';
import { ConfirmModal } from '@/components/ui/ConfirmModal';

interface ModeratorDashboardProps {
    sessionId: string;
    stage: string;
    onClose?: () => void;
}

export const ModeratorDashboard: React.FC<ModeratorDashboardProps> = ({ sessionId, stage, onClose }) => {
    const { data: participation, isLoading } = useSessionParticipation(sessionId);
    const updateStageMutation = useUpdateSessionStage();
    const finalizeMutation = useFinalizeDeliberation();
    const [isConfirmOpen, setIsConfirmOpen] = React.useState(false);

    const nextStage = stage === 'refine' ? 'ranking' : stage === 'ranking' ? 'consent' : stage === 'consent' ? 'closed' : null;

    const { data: validation } = useSessionValidation(sessionId, nextStage || '');

    const handleAdvance = () => {
        if (!nextStage) return;

        if (validation && !validation.allowed) {
            toast.error(validation.message);
            return;
        }

        updateStageMutation.mutate({ sessionId, stage: nextStage });
        toast.success(`Volgende fase (${getStageLabel(nextStage)}) gestart!`);
    };

    const handleFinalize = () => {
        setIsConfirmOpen(true);
    };

    const confirmFinalize = () => {
        finalizeMutation.mutate(sessionId, {
            onSuccess: () => {
                toast.success("Deliberatie succesvol afgerond!");
                if (onClose) onClose();
                setIsConfirmOpen(false);
            },
            onError: (err: any) => {
                toast.error(err.message || "Fout bij finaliseren");
                setIsConfirmOpen(false);
            }
        });
    };

    if (isLoading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

    const totalParticipants = participation?.length || 0;
    const activeParticipants = participation?.filter((p: any) => p.has_feedback || p.has_ranking || p.has_consent).length || 0;

    return (
        <div className="space-y-6">
            <header className="flex justify-between items-start">
                <div>
                    <h2 className="text-2xl font-bold">Moderator Dashboard</h2>
                    <p className="text-muted-foreground">Beheer de voortgang en deelname van deze sessie.</p>
                </div>
                <div className="flex gap-2">
                    {stage !== 'consent' && stage !== 'closed' && (
                        <div className="flex flex-col items-end gap-1">
                            <Button
                                onClick={handleAdvance}
                                disabled={updateStageMutation.isPending || (validation && !validation.allowed)}
                                className={validation && !validation.allowed ? "opacity-50 cursor-not-allowed" : ""}
                            >
                                <Play className="mr-2 h-4 w-4" />
                                Start {nextStage ? getStageLabel(nextStage) : 'Volgende Fase'}
                            </Button>
                            {validation && !validation.allowed && (
                                <span className="text-[10px] text-red-500 font-medium max-w-[200px] text-right leading-tight">
                                    {validation.message}
                                </span>
                            )}
                        </div>
                    )}
                    {(stage === 'consent' || stage === 'closed') && (
                        <Button
                            variant="default"
                            className={stage === 'closed' ? "bg-amber-600 hover:bg-amber-700" : "bg-green-600 hover:bg-green-700"}
                            onClick={handleFinalize}
                            disabled={finalizeMutation.isPending}
                        >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            {stage === 'closed' ? 'Finalisatie Uitvoeren (Herstel)' : 'Finaliseer Besluit'}
                        </Button>
                    )}
                    {onClose && (
                        <Button variant="ghost" size="icon" onClick={onClose}>
                            <X className="h-4 w-4" />
                        </Button>
                    )}
                </div>
            </header>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Deelnemers</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{activeParticipants} / {totalParticipants}</div>
                        <p className="text-xs text-muted-foreground">Actieve vs Totaal Uitgenodigd</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Huidige Fase</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold capitalize">
                            {stage === 'closed' ? 'Voltooid' : getStageLabel(stage)}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {stage === 'closed' ? 'De sessie is succesvol afgerond' : 'Wacht op moderator actie'}
                        </p>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Deelnemerslijst</CardTitle>
                    <CardDescription>Status per individuele deelnemer.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {participation && participation.length > 0 ? (
                            participation.map((p: any) => (
                                <div key={p.email} className="flex items-center justify-between p-3 border rounded-lg bg-card/50 hover:bg-accent/5 transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-medium text-xs text-primary">
                                            {p.name?.[0]?.toUpperCase() || '?'}
                                        </div>
                                        <div>
                                            <div className="font-medium text-sm">{p.name || p.email}</div>
                                            <div className="text-[10px] text-muted-foreground">{p.email}</div>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <StatusBadge label="Verfijnen" active={p.has_feedback} />
                                        <StatusBadge label="Prioritering" active={p.has_ranking} />
                                        <StatusBadge label="Instemming" active={p.has_consent} />
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-muted-foreground">
                                Geen uitgenodigde deelnemers gevonden.
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>

            {stage === 'closed' && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
                    <strong>Let op:</strong> De sessie is gesloten.
                </div>
            )}

            <ConfirmModal
                isOpen={isConfirmOpen}
                onCancel={() => setIsConfirmOpen(false)}
                onConfirm={confirmFinalize}
                title="Besluit Finaliseren"
                message="Weet je zeker dat je dit besluit wilt finaliseren? Er wordt een nieuwe versie van het thema aangemaakt met de gekozen claims. Dit kan niet ongedaan gemaakt worden."
                confirmLabel="Finaliseren"
                isDanger={false}
            />
        </div>
    );
};

const getStageLabel = (stage: string) => {
    switch (stage) {
        case 'refine': return 'Verfijnen';
        case 'ranking': return 'Prioritering';
        case 'consent': return 'Instemming';
        case 'closed': return 'Gesloten';
        default: return stage;
    }
};

const StatusBadge = ({ label, active }: { label: string, active: boolean }) => (
    <div className={`px-2 py-0.5 rounded text-[10px] font-medium border ${active ? 'bg-green-100 text-green-700 border-green-200' : 'bg-secondary text-muted-foreground border-border'}`}>
        {label}
    </div>
);
