import { useState } from 'react';
import { Plus, Layers, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { PerspectiveToolbar } from '@/components/shell/PerspectiveToolbar';
import { StakeholderMap } from './views/StakeholderMap';
import { StakeholderGroupPanel } from './views/StakeholderGroupPanel';
import { api, type StakeholderClaimType } from '@/services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SociaShellProps {
    dsId: string;
}

type ActorType = 'Burger' | 'Organisatie' | 'Overheid' | 'Bedrijf';

const ACTOR_TYPE_OPTIONS: { value: ActorType; label: string }[] = [
    { value: 'Burger', label: 'Burger' },
    { value: 'Organisatie', label: 'Organisatie' },
    { value: 'Overheid', label: 'Overheid' },
    { value: 'Bedrijf', label: 'Bedrijf' },
];

// ---------------------------------------------------------------------------
// CreateActorModal
// ---------------------------------------------------------------------------

interface CreateActorModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    dsId: string;
    onCreated: () => void;
}

function CreateActorModal({ open, onOpenChange, dsId, onCreated }: CreateActorModalProps) {
    const [naam, setNaam] = useState('');
    const [type, setType] = useState<ActorType>('Organisatie');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleClose = () => {
        setNaam('');
        setType('Organisatie');
        setError(null);
        onOpenChange(false);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!naam.trim()) return;

        setIsSubmitting(true);
        setError(null);

        // Tijdelijke workaround: actor aanmaken via stakeholder claim (GoalClaim)
        // totdat er een dedicated POST /actor endpoint bestaat.
        const claimType: StakeholderClaimType = 'GoalClaim';
        const actorSlug = naam.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
        const actorUri = `urn:valor:socia:actor:${actorSlug}`;

        try {
            await api.createStakeholderClaim(dsId, {
                claim_type: claimType,
                claim_content: naam.trim(),
                actor_uri: actorUri,
            });
            onCreated();
            handleClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Aanmaken mislukt.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Nieuwe Actor</DialogTitle>
                    <DialogDescription>
                        Voeg een stakeholder toe aan de SOCIA-analyse.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="actor-naam">Naam</Label>
                        <Input
                            id="actor-naam"
                            value={naam}
                            onChange={(e) => setNaam(e.target.value)}
                            placeholder="Bijv. Wijkbewoners Noord"
                            autoFocus
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="actor-type">Type</Label>
                        <Select value={type} onValueChange={(v) => setType(v as ActorType)}>
                            <SelectTrigger id="actor-type">
                                <SelectValue placeholder="Kies een type" />
                            </SelectTrigger>
                            <SelectContent>
                                {ACTOR_TYPE_OPTIONS.map((opt) => (
                                    <SelectItem key={opt.value} value={opt.value}>
                                        {opt.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    {error && (
                        <p className="text-xs text-destructive">{error}</p>
                    )}
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
                            Annuleren
                        </Button>
                        <Button type="submit" disabled={!naam.trim() || isSubmitting}>
                            {isSubmitting && <Loader2 className="animate-spin mr-2 h-4 w-4" />}
                            Aanmaken
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// ---------------------------------------------------------------------------
// SociaShell
// ---------------------------------------------------------------------------

export function SociaShell({ dsId }: SociaShellProps) {
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [showGroupsPanel, setShowGroupsPanel] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);

    const handleCreated = () => {
        setRefreshKey((k) => k + 1);
    };

    return (
        <div className="w-full h-full bg-background relative">
            <PerspectiveToolbar>
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                size="sm"
                                onClick={() => setIsCreateModalOpen(true)}
                                variant="ghost"
                                className="h-8 w-8 p-0"
                            >
                                <Plus className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>Nieuwe Actor</TooltipContent>
                    </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                size="sm"
                                variant={showGroupsPanel ? 'secondary' : 'ghost'}
                                className="h-8 w-8 p-0"
                                onClick={() => setShowGroupsPanel((v) => !v)}
                            >
                                <Layers className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>StakeholderGroepen</TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </PerspectiveToolbar>

            {/* Hoofdcanvas */}
            <StakeholderMap key={`map-${refreshKey}`} dsId={dsId} />

            {/* StakeholderGroepen sidebar */}
            {showGroupsPanel && (
                <div className="absolute top-0 right-0 h-full w-[380px] bg-background border-l shadow-2xl z-50 overflow-hidden flex flex-col transition-transform duration-300 ease-in-out">
                    <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
                        <span className="text-sm font-semibold">StakeholderGroepen</span>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0"
                            onClick={() => setShowGroupsPanel(false)}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        <StakeholderGroupPanel dsId={dsId} />
                    </div>
                </div>
            )}

            {/* Modals */}
            <CreateActorModal
                open={isCreateModalOpen}
                onOpenChange={setIsCreateModalOpen}
                dsId={dsId}
                onCreated={handleCreated}
            />
        </div>
    );
}

// Re-export voor achterwaartse compatibiliteit (indien gebruikt als default export ergens)
export default SociaShell;
