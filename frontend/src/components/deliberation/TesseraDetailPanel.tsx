import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { type TesseraNode } from '@/services/api';

interface TesseraDetailPanelProps {
    tessera: TesseraNode | null;
    open: boolean;
    onClose: () => void;
}

const STATUS_LABELS: Record<string, string> = {
    Proposed: 'Voorgesteld',
    Contested: 'Betwist',
    Accepted: 'Geaccepteerd',
    Rejected: 'Afgewezen',
    Deprecated: 'Verouderd',
};

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    Proposed: 'secondary',
    Contested: 'outline',
    Accepted: 'default',
    Rejected: 'destructive',
    Deprecated: 'outline',
};

export const TesseraDetailPanel: React.FC<TesseraDetailPanelProps> = ({ tessera, open, onClose }) => {
    const statusKey = tessera?.epistemicStatus ?? '';
    const statusLabel = STATUS_LABELS[statusKey] ?? statusKey;
    const statusVariant = STATUS_VARIANT[statusKey] ?? 'secondary';

    return (
        <Sheet open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
            <SheetContent side="right" className="w-full sm:max-w-md flex flex-col gap-0 p-0">
                <SheetHeader className="px-6 pt-6 pb-4">
                    <SheetTitle className="text-base">Tessera detail</SheetTitle>
                    <SheetDescription className="sr-only">
                        Informatie over de geselecteerde tessera
                    </SheetDescription>
                </SheetHeader>
                <Separator />
                {tessera ? (
                    <div className="flex flex-col gap-5 px-6 py-5 flex-1 overflow-y-auto">
                        <div className="flex items-center gap-2 flex-wrap">
                            <Badge variant={statusVariant}>{statusLabel}</Badge>
                        </div>

                        <div className="flex flex-col gap-1">
                            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                                Claim
                            </span>
                            <p className="text-sm text-foreground leading-relaxed">
                                {tessera.claimContent}
                            </p>
                        </div>

                        <Separator />

                        <div className="flex flex-col gap-1">
                            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                                Tessera ID
                            </span>
                            <code className="text-xs text-muted-foreground font-mono break-all">
                                {tessera.id}
                            </code>
                        </div>
                    </div>
                ) : (
                    <div className="flex items-center justify-center flex-1 text-muted-foreground text-sm px-6">
                        Geen tessera geselecteerd.
                    </div>
                )}
            </SheetContent>
        </Sheet>
    );
};
