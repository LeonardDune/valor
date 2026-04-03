import { useState } from 'react';
import { Plus, GitBranch, AlertTriangle } from 'lucide-react';
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
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import {
    ToggleGroup,
    ToggleGroupItem,
} from '@/components/ui/toggle-group';
import { PerspectiveToolbar } from '@/components/shell/PerspectiveToolbar';
import { ValueCanvas } from './ValueCanvas';
import { ValueChain } from './ValueChain';
import { ValueTensionView } from './ValueTensionView';
import { api } from '@/services/api';
import type { CreateValueCriterionPayload } from '@/services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type AxiaView = 'canvas' | 'keten' | 'spanningen';

interface AxiaShellProps {
    designSpaceId: string;
}

// ---------------------------------------------------------------------------
// CreateValueClaimModal
// ---------------------------------------------------------------------------

interface CreateValueClaimModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    designSpaceId: string;
    onCreated: () => void;
}

function CreateValueClaimModal({ open, onOpenChange, designSpaceId, onCreated }: CreateValueClaimModalProps) {
    const [inhoud, setInhoud] = useState('');
    const [waardetype, setWaardetype] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleClose = () => {
        setInhoud('');
        setWaardetype('');
        setError(null);
        onOpenChange(false);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inhoud.trim() || !waardetype.trim()) return;

        setIsSubmitting(true);
        setError(null);

        const slug = waardetype.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
        const payload: CreateValueCriterionPayload = {
            label: inhoud.trim(),
            value_type_uri: `urn:valor:cover:${slug}`,
        };

        try {
            await api.createValueCriterion(designSpaceId, payload);
            onCreated();
            handleClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Opslaan mislukt.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Nieuwe Waardeclaim</DialogTitle>
                    <DialogDescription>
                        Voeg een waardeclaim toe aan de AXIA-analyse.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="vc-inhoud">Inhoud</Label>
                        <Input
                            id="vc-inhoud"
                            value={inhoud}
                            onChange={(e) => setInhoud(e.target.value)}
                            placeholder="Bijv. Het systeem moet eerlijk zijn voor alle burgers"
                            autoFocus
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="vc-waardetype">Waardetype</Label>
                        <Input
                            id="vc-waardetype"
                            value={waardetype}
                            onChange={(e) => setWaardetype(e.target.value)}
                            placeholder="bijv. Rechtvaardigheid"
                        />
                    </div>
                    {error && (
                        <p className="text-xs text-destructive">{error}</p>
                    )}
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
                            Annuleren
                        </Button>
                        <Button type="submit" disabled={!inhoud.trim() || !waardetype.trim() || isSubmitting}>
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
// ViewToggle
// ---------------------------------------------------------------------------

interface AxiaViewToggleProps {
    value: AxiaView;
    onChange: (view: AxiaView) => void;
}

function AxiaViewToggle({ value, onChange }: AxiaViewToggleProps) {
    return (
        <ToggleGroup
            type="single"
            value={value}
            onValueChange={(v) => v && onChange(v as AxiaView)}
            className="gap-1"
        >
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <ToggleGroupItem value="canvas" size="sm" aria-label="Waardeclaims">
                            <span className="text-xs font-medium px-1">Claims</span>
                        </ToggleGroupItem>
                    </TooltipTrigger>
                    <TooltipContent>Waardeclaims</TooltipContent>
                </Tooltip>
            </TooltipProvider>

            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <ToggleGroupItem value="keten" size="sm" aria-label="Waardeketen">
                            <GitBranch className="h-4 w-4" />
                        </ToggleGroupItem>
                    </TooltipTrigger>
                    <TooltipContent>Waardeketen</TooltipContent>
                </Tooltip>
            </TooltipProvider>

            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <ToggleGroupItem value="spanningen" size="sm" aria-label="Waardespanningen">
                            <AlertTriangle className="h-4 w-4" />
                        </ToggleGroupItem>
                    </TooltipTrigger>
                    <TooltipContent>Waardespanningen</TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </ToggleGroup>
    );
}

// ---------------------------------------------------------------------------
// AxiaShell
// ---------------------------------------------------------------------------

export function AxiaShell({ designSpaceId }: AxiaShellProps) {
    const [view, setView] = useState<AxiaView>('canvas');
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
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
                        <TooltipContent>Nieuwe Waardeclaim</TooltipContent>
                    </Tooltip>
                </TooltipProvider>

                <AxiaViewToggle value={view} onChange={setView} />
            </PerspectiveToolbar>

            <div className="w-full h-full overflow-hidden">
                {view === 'canvas' && <ValueCanvas key={`canvas-${refreshKey}`} designSpaceId={designSpaceId} />}
                {view === 'keten' && <ValueChain key={`keten-${refreshKey}`} designSpaceId={designSpaceId} />}
                {view === 'spanningen' && <ValueTensionView key={`spanningen-${refreshKey}`} designSpaceId={designSpaceId} />}
            </div>

            <CreateValueClaimModal
                open={isCreateModalOpen}
                onOpenChange={setIsCreateModalOpen}
                designSpaceId={designSpaceId}
                onCreated={handleCreated}
            />
        </div>
    );
}
