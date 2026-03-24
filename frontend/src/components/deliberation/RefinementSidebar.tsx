// 
import React from 'react';
import { type Claim } from '@/services/api';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Circle, AlertCircle, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface RefinementSidebarProps {
    claims: Claim[];
    selectedId: string | null;
    onSelect: (id: string) => void;
    feedbackData: any[];
    onBack?: () => void;
    currentUserId?: string;
}

export const RefinementSidebar: React.FC<RefinementSidebarProps> = ({
    claims,
    selectedId,
    onSelect,
    feedbackData,
    onBack,
    currentUserId
}) => {
    // Helper to get my feedback for a claim
    const getClaimStatus = (claimVersionId: string) => {
        if (!currentUserId || currentUserId === 'anon') return 'pending';
        const feedback = feedbackData.find(f =>
            f.tessera_base_id === claimVersionId &&
            f.user_id === currentUserId
        );
        return feedback ? (feedback.color as 'green' | 'amber' | 'red') : 'pending';
    };

    const getFullFeedback = (claimVersionId: string) => {
        if (!currentUserId || currentUserId === 'anon') return null;
        return feedbackData.find(f =>
            f.tessera_base_id === claimVersionId &&
            f.user_id === currentUserId
        ) || null;
    };

    const completedCount = claims.filter(c => {
        const f = getFullFeedback(c.version_id || '');
        return f && f.color && f.motivation && f.motivation.trim().length > 0;
    }).length;

    const handleFinish = () => {
        if (completedCount < claims.length) {
            if (confirm(`Je hebt ${claims.length - completedCount} van de ${claims.length} claims nog niet volledig beoordeeld (keuze + motivatie). Weet je zeker dat je wilt afronden?`)) {
                onBack?.();
            }
        } else {
            onBack?.();
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b border-border bg-background space-y-4">
                <Button
                    variant="ghost"
                    size="sm"
                    className="-ml-2 h-8 text-muted-foreground gap-2 hover:text-foreground"
                    onClick={onBack}
                >
                    <ArrowLeft className="h-4 w-4" />
                    Terug naar Analyse
                </Button>
                <div>
                    <h3 className="font-semibold text-lg leading-none">Claims</h3>
                    <p className="text-xs text-muted-foreground mt-1">{claims.length} claims gevonden</p>
                </div>
            </div>

            <ScrollArea className="flex-1">
                <ul className="p-2 space-y-1">
                    {claims.map((claim) => {
                        const status = getClaimStatus(claim.version_id || '');
                        const isSelected = selectedId === claim.id;

                        return (
                            <li key={claim.id}>
                                <button
                                    onClick={() => onSelect(claim.id)}
                                    className={cn(
                                        "w-full text-left p-3 rounded-md transition-all group relative",
                                        isSelected
                                            ? "bg-primary/10 text-primary border border-primary/20 shadow-sm"
                                            : "hover:bg-muted text-foreground border border-transparent"
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className="mt-1 flex-shrink-0">
                                            {status === 'green' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                                            {status === 'amber' && <AlertCircle className="h-4 w-4 text-amber-500" />}
                                            {status === 'red' && <AlertCircle className="h-4 w-4 text-red-500" />}
                                            {status === 'pending' && <Circle className="h-4 w-4 text-muted-foreground/30" />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className={cn(
                                                "text-sm font-medium line-clamp-2 leading-tight",
                                                isSelected ? "text-primary" : "text-foreground"
                                            )}>
                                                {claim.statement}
                                            </p>
                                            <div className="flex items-center gap-2 mt-2">
                                                <Badge variant="outline" className="text-[10px] px-1 h-4 uppercase opacity-60">
                                                    {claim.polarity === '+' ? 'Positief' : 'Negatief'}
                                                </Badge>
                                                <span className="text-[10px] text-muted-foreground">
                                                    {Math.round(claim.confidence * 100)}% zeker
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    {isSelected && (
                                        <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-primary rounded-r-full" />
                                    )}
                                </button>
                            </li>
                        );
                    })}
                </ul>
            </ScrollArea>

            <div className="p-4 border-t border-border bg-background">
                <div className="flex justify-between items-center mb-2 px-1">
                    <span className="text-[10px] font-medium text-muted-foreground uppercase">Voortgang</span>
                    <span className="text-[10px] font-bold text-primary">{completedCount} / {claims.length}</span>
                </div>
                <Button
                    className="w-full gap-2 font-bold"
                    variant="default"
                    onClick={handleFinish}
                >
                    <CheckCircle2 className="h-4 w-4" />
                    Verfijning Afronden
                </Button>
                <p className="text-[10px] text-muted-foreground text-center mt-2 px-2 leading-tight">
                    Hiermee keer je terug naar de graaf terwijl de anderen hun review afmaken.
                </p>
            </div>
        </div>
    );
};
