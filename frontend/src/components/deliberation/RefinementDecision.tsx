import React from 'react';
import { type Claim } from '@/services/api';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
    Check,
    XCircle,
    Info,
    AlertCircle,
    Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface RefinementDecisionProps {
    claim: Claim | null;
    initialFeedback: { color: string, motivation?: string } | null;
    onFeedbackSubmitted: (color: string, motivation: string) => void;
    isSubmitting: boolean;
}

export const RefinementDecision: React.FC<RefinementDecisionProps> = ({
    claim,
    initialFeedback,
    onFeedbackSubmitted,
    isSubmitting
}) => {
    const [selectedColor, setSelectedColor] = React.useState<string | null>(initialFeedback?.color || null);
    const [motivation, setMotivation] = React.useState(initialFeedback?.motivation || '');

    // Sync with initialFeedback only on mount or when switching claims (handled by key)
    // We avoid updating during active editing to prevent cursor jumps/overwrites
    React.useEffect(() => {
        if (initialFeedback) {
            setSelectedColor(prev => prev === null ? initialFeedback.color : prev);
            setMotivation(prev => prev === '' ? (initialFeedback.motivation || '') : prev);
        }
    }, [initialFeedback]);

    // Debounced effect for motivation auto-save
    React.useEffect(() => {
        const timer = setTimeout(() => {
            if (selectedColor && motivation !== (initialFeedback?.motivation || '')) {
                onFeedbackSubmitted(selectedColor, motivation);
            }
        }, 800);

        return () => clearTimeout(timer);
    }, [motivation, selectedColor, onFeedbackSubmitted, initialFeedback?.motivation]);

    if (!claim) {
        return (
            <div className="flex flex-col h-full bg-background border-l border-border">
                <div className="p-4 border-b border-border">
                    <h3 className="font-semibold text-lg">Collectieve positie</h3>
                </div>
                <div className="flex-1 flex items-center justify-center p-8 text-center text-muted-foreground text-sm">
                    <p>Selecteer een claim om je positie te bepalen.</p>
                </div>
            </div>
        );
    }

    const handleColorClick = (color: string) => {
        setSelectedColor(color);
        // Auto-submit on color change
        onFeedbackSubmitted(color, motivation);
    };

    // Validation: motivation is required if color is selected
    const isMotivationEmpty = !motivation || motivation.trim().length === 0;
    const showValidationError = selectedColor && isMotivationEmpty;

    return (
        <section className="flex flex-col h-full bg-background">
            <header className="p-4 border-b border-border bg-background">
                <h3 className="font-semibold text-lg">Collectieve positie</h3>
                <p className="text-xs text-muted-foreground italic">Bepaal je standpunt voor deze claim</p>
            </header>

            <div className="flex-1 overflow-y-auto p-4 space-y-8">
                <fieldset className="space-y-4 border-none p-0 m-0">
                    <legend className="text-xs uppercase tracking-wider text-muted-foreground font-medium mb-4">Selecteer Positie</legend>
                    <div className="grid grid-cols-1 gap-2">
                        <VoteButton
                            color="green"
                            label="Consent"
                            description="Geen overwegend bezwaar"
                            isSelected={selectedColor === 'green'}
                            onClick={() => handleColorClick('green')}
                            icon={<Check className="h-4 w-4" />}
                            activeClass="bg-green-500/10 text-green-700 border-green-500/50 shadow-sm"
                        />
                        <VoteButton
                            color="amber"
                            label="Onzeker"
                            description="Verduidelijking nodig"
                            isSelected={selectedColor === 'amber'}
                            onClick={() => handleColorClick('amber')}
                            icon={<AlertCircle className="h-4 w-4" />}
                            activeClass="bg-amber-500/10 text-amber-700 border-amber-500/50 shadow-sm"
                        />
                        <VoteButton
                            color="red"
                            label="Bezwaar"
                            description="Fundamenteel oneens"
                            isSelected={selectedColor === 'red'}
                            onClick={() => handleColorClick('red')}
                            icon={<XCircle className="h-4 w-4" />}
                            activeClass="bg-red-500/10 text-red-700 border-red-500/50 shadow-sm"
                        />
                    </div>
                </fieldset>

                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <Label htmlFor="motivation" className="text-xs uppercase tracking-wider text-muted-foreground">Motivatie (Verplicht)</Label>
                        {isSubmitting && <Loader2 className="h-3 w-3 animate-spin text-primary" />}
                    </div>
                    <Textarea
                        id="motivation"
                        placeholder="Waarom kies je voor deze positie? Een motivatie is verplicht voor elke keuze."
                        className={cn(
                            "min-h-[120px] resize-none text-sm transition-all duration-300",
                            showValidationError
                                ? "bg-red-500/5 border-red-500/50 ring-1 ring-red-500/20"
                                : "bg-muted/30 border-border/50 focus:bg-background"
                        )}
                        value={motivation}
                        onChange={(e) => setMotivation(e.target.value)}
                    />
                    {showValidationError && (
                        <p className="text-[10px] text-red-500/80 font-medium italic animate-in fade-in slide-in-from-top-1">
                            Voeg a.u.b. een motivatie toe om je keuze te onderbouwen.
                        </p>
                    )}
                </div>

                <article className="p-4 rounded-xl bg-primary/5 border border-primary/10 space-y-2">
                    <div className="flex items-center gap-2 text-primary">
                        <Info className="h-3 w-3" />
                        <h4 className="text-[10px] font-bold uppercase">Huidige consensus</h4>
                    </div>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                        Er is momenteel nog geen sterke consensus over deze claim. Jouw stem helpt bij het vormen van het collectieve gedragen standpunt.
                    </p>
                </article>
            </div>
        </section>
    );
};

interface VoteButtonProps {
    color: string;
    label: string;
    description: string;
    isSelected: boolean;
    onClick: () => void;
    icon: React.ReactNode;
    activeClass: string;
}

const VoteButton: React.FC<VoteButtonProps> = ({
    label,
    description,
    isSelected,
    onClick,
    icon,
    activeClass
}) => {
    return (
        <button
            onClick={onClick}
            className={cn(
                "flex items-center gap-3 p-3 rounded-xl border border-border/50 transition-all text-left group",
                isSelected ? activeClass : "hover:bg-muted/50 bg-background"
            )}
        >
            <div className={cn(
                "h-8 w-8 rounded-full flex items-center justify-center border transition-colors",
                isSelected ? "bg-background border-current" : "bg-muted border-transparent"
            )}>
                {icon}
            </div>
            <div className="flex-1">
                <p className="font-bold text-sm leading-none mb-1">{label}</p>
                <p className="text-[10px] opacity-70 leading-none">{description}</p>
            </div>
            {isSelected && <Check className="h-4 w-4 ml-auto" />}
        </button>
    );
};
