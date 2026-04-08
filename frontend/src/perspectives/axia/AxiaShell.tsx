import { useState, useEffect } from 'react';
import { Plus, GitBranch, AlertTriangle, Loader2, AlertCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
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
import type { CreateValueClaimPayload, AxiaSchema, ValueClaimItem } from '@/services/api';
import { useAxiaSchema } from './hooks/useAxiaSchema';

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
    schema: AxiaSchema;
    onCreated: () => void;
}

function CreateValueClaimModal({ open, onOpenChange, designSpaceId, schema, onCreated }: CreateValueClaimModalProps) {
    const [inhoud, setInhoud] = useState('');
    const [valueTypeUri, setValueTypeUri] = useState('');
    const [polarityUri, setPolarityUri] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleClose = () => {
        setInhoud('');
        setValueTypeUri('');
        setPolarityUri('');
        setError(null);
        onOpenChange(false);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inhoud.trim()) return;

        setIsSubmitting(true);
        setError(null);

        const payload: CreateValueClaimPayload = {
            claim_content: inhoud.trim(),
            value_type_uri: valueTypeUri || undefined,
            claim_polarity_uri: polarityUri || undefined,
        };

        try {
            await api.createValueClaim(designSpaceId, payload);
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
                        <Label>Waardetype</Label>
                        <Select value={valueTypeUri} onValueChange={setValueTypeUri}>
                            <SelectTrigger>
                                <SelectValue placeholder="Kies een waardetype" />
                            </SelectTrigger>
                            <SelectContent>
                                {schema.value_types.map((vt) => (
                                    <SelectItem key={vt.uri} value={vt.uri}>
                                        {vt.label_nl || vt.label_en}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid gap-2">
                        <Label>Polariteit</Label>
                        <Select value={polarityUri} onValueChange={setPolarityUri}>
                            <SelectTrigger>
                                <SelectValue placeholder="Kies een polariteit" />
                            </SelectTrigger>
                            <SelectContent>
                                {schema.claim_polarities.map((p) => (
                                    <SelectItem key={p.uri} value={p.uri}>
                                        {p.label_nl || p.label_en}
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
                        <Button type="submit" disabled={!inhoud.trim() || isSubmitting}>
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
// ValueClaimDetailPanel
// ---------------------------------------------------------------------------

interface ValueClaimDetailPanelProps {
    claim: ValueClaimItem;
    onClose: () => void;
}

function polarityLabel(uri?: string | null): string {
    if (!uri) return 'Onbekend';
    if (uri.includes('Supporting')) return 'Ondersteunend';
    if (uri.includes('Undermining')) return 'Ondermijnend';
    if (uri.includes('Ambiguous')) return 'Ambigu';
    return uri.split('#').pop() ?? uri;
}

function polarityVariant(uri?: string | null): 'default' | 'destructive' | 'secondary' | 'outline' {
    if (!uri) return 'outline';
    if (uri.includes('Supporting')) return 'default';
    if (uri.includes('Undermining')) return 'destructive';
    return 'secondary';
}

function ValueClaimDetailPanel({ claim, onClose }: ValueClaimDetailPanelProps) {
    return (
        <div className="absolute top-0 right-0 h-full w-80 bg-background border-l border-border shadow-xl z-20 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <span className="text-sm font-semibold">Waardeclaim</span>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={onClose}>
                    <X className="h-4 w-4" />
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <div>
                    <p className="text-xs text-muted-foreground mb-1">Inhoud</p>
                    <p className="text-sm leading-relaxed">{claim.claim_content}</p>
                </div>

                {claim.value_type_label && (
                    <div>
                        <p className="text-xs text-muted-foreground mb-1">Waardetype</p>
                        <Badge variant="secondary">{claim.value_type_label}</Badge>
                    </div>
                )}

                {claim.polarity_uri && (
                    <div>
                        <p className="text-xs text-muted-foreground mb-1">Polariteit</p>
                        <Badge variant={polarityVariant(claim.polarity_uri)}>
                            {claim.polarity_label ?? polarityLabel(claim.polarity_uri)}
                        </Badge>
                    </div>
                )}

                {claim.epistemic_status && (
                    <div>
                        <p className="text-xs text-muted-foreground mb-1">Epistemische status</p>
                        <Badge variant="outline">{claim.epistemic_status}</Badge>
                    </div>
                )}

                <div>
                    <p className="text-xs text-muted-foreground mb-1">Aangemaakt door</p>
                    <p className="text-xs text-foreground font-mono truncate">{claim.claimed_by}</p>
                </div>

                <div>
                    <p className="text-xs text-muted-foreground mb-1">Aangemaakt op</p>
                    <p className="text-xs text-foreground">
                        {new Date(claim.claimed_at).toLocaleString('nl-NL')}
                    </p>
                </div>
            </div>
        </div>
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
    const { schema, loading, error } = useAxiaSchema();
    const [view, setView] = useState<AxiaView>('canvas');
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);
    const [selectedClaim, setSelectedClaim] = useState<ValueClaimItem | null>(null);

    useEffect(() => {
        const prev = document.title;
        document.title = 'AXIA — Waardeperspectief';
        return () => { document.title = prev; };
    }, []);

    const handleCreated = () => {
        setRefreshKey((k) => k + 1);
    };

    if (loading) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-background">
                <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Loader2 className="h-6 w-6 animate-spin" />
                    <span className="text-sm">AXIA-schema laden...</span>
                </div>
            </div>
        );
    }

    if (error || !schema) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-background">
                <div className="flex flex-col items-center gap-3 text-destructive max-w-sm text-center">
                    <AlertCircle className="h-6 w-6" />
                    <p className="text-sm font-medium">AXIA-schema kon niet worden geladen</p>
                    <p className="text-xs text-muted-foreground">
                        {error?.message ?? 'Controleer of de ontologie beschikbaar is in Fuseki.'}
                    </p>
                </div>
            </div>
        );
    }

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
                {view === 'canvas' && (
                    <ValueCanvas
                        refreshTrigger={refreshKey}
                        designSpaceId={designSpaceId}
                        onSelect={setSelectedClaim}
                    />
                )}
                {view === 'keten' && <ValueChain key={`keten-${refreshKey}`} designSpaceId={designSpaceId} />}
                {view === 'spanningen' && <ValueTensionView key={`spanningen-${refreshKey}`} designSpaceId={designSpaceId} />}
            </div>

            {selectedClaim && (
                <ValueClaimDetailPanel
                    claim={selectedClaim}
                    onClose={() => setSelectedClaim(null)}
                />
            )}

            <CreateValueClaimModal
                open={isCreateModalOpen}
                onOpenChange={setIsCreateModalOpen}
                designSpaceId={designSpaceId}
                schema={schema}
                onCreated={handleCreated}
            />
        </div>
    );
}
