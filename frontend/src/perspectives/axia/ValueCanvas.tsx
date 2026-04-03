import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { ValueCanvasResponse, ValueClaimItem } from '@/services/api';

interface ValueCanvasProps {
    designSpaceId: string;
}

export function ValueCanvas({ designSpaceId }: ValueCanvasProps) {
    const [data, setData] = useState<ValueCanvasResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const result = await api.getValueClaims(designSpaceId);
                if (!cancelled) {
                    setData(result);
                }
            } catch {
                if (!cancelled) {
                    setError('Kon waardeclaims niet laden.');
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        load();
        return () => { cancelled = true; };
    }, [designSpaceId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                Waardeclaims laden...
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full text-destructive text-sm">
                {error}
            </div>
        );
    }

    if (!data || Object.keys(data.groups).length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm italic">
                Geen waardeclaims gevonden voor deze DesignSpace.
            </div>
        );
    }

    const groups = Object.entries(data.groups);

    return (
        <div className="h-full w-full overflow-x-auto">
            <div className="flex gap-4 p-4 min-h-full">
                {groups.map(([valueTypeUri, claims]) => (
                    <ValueTypeColumn
                        key={valueTypeUri}
                        valueTypeUri={valueTypeUri}
                        valueTypeLabel={claims[0]?.value_type_label ?? valueTypeUri}
                        claims={claims}
                    />
                ))}
            </div>
        </div>
    );
}

interface ValueTypeColumnProps {
    valueTypeUri: string;
    valueTypeLabel: string;
    claims: ValueClaimItem[];
}

function ValueTypeColumn({ valueTypeLabel, claims }: ValueTypeColumnProps) {
    return (
        <div className="flex flex-col gap-2 min-w-[220px] max-w-[280px]">
            <div className="rounded-md bg-zinc-100 dark:bg-zinc-800 px-3 py-2">
                <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-200 truncate" title={valueTypeLabel}>
                    {valueTypeLabel}
                </h3>
                <span className="text-xs text-muted-foreground">{claims.length} claim{claims.length !== 1 ? 's' : ''}</span>
            </div>
            <div className="flex flex-col gap-2">
                {claims.map((claim) => (
                    <ValueClaimCard key={claim.tessera_id} claim={claim} />
                ))}
            </div>
        </div>
    );
}

interface ValueClaimCardProps {
    claim: ValueClaimItem;
}

function ValueClaimCard({ claim }: ValueClaimCardProps) {
    return (
        <div className="rounded-md border border-border bg-card p-3 shadow-sm">
            <p className="text-sm text-card-foreground leading-snug">{claim.claim_content}</p>
            <p className="mt-1 text-xs text-muted-foreground">
                Door {claim.claimed_by} &middot; {new Date(claim.claimed_at).toLocaleDateString('nl-NL')}
            </p>
        </div>
    );
}
