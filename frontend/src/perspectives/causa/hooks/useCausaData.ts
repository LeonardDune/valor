import { useState, useCallback, useEffect, useRef } from 'react';
import { api, type Factor, type Claim } from '../../../services/api';
import { mapFactors, mapClaims } from '../layout/mappers';
import type { CausalNode, CausalLink } from '../types';

interface CausaData {
    nodes: CausalNode[];
    links: CausalLink[];
    factors: Factor[]; // Raw data for Modals
    claims: Claim[];   // Raw data for Modals
    cycleNodeIds: Set<string>;
    loading: boolean;
    error: Error | null;
    refresh: (force?: boolean) => Promise<void>;
}

export const useCausaData = (themeId: string, versionId?: string, phase?: string | null): CausaData => {
    const [nodes, setNodes] = useState<CausalNode[]>([]);
    const [links, setLinks] = useState<CausalLink[]>([]);
    const [factors, setFactors] = useState<Factor[]>([]);
    const [claims, setClaims] = useState<Claim[]>([]);
    const [cycleNodeIds, setCycleNodeIds] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const lastFetchRef = useRef<string | null>(null);

    const refresh = useCallback(async (force = false) => {
        const fetchKey = `${themeId}-${versionId || 'active'}-${phase || 'current'}`;
        if (!force && lastFetchRef.current === fetchKey && !loading) return;

        try {
            setLoading(true);
            lastFetchRef.current = fetchKey;
            let claimsData: Claim[];
            let factorsData: Factor[];

            console.log('[useCausaData] Refreshing...', { themeId, versionId, force });

            if (versionId) {
                [claimsData, factorsData] = await Promise.all([
                    api.getThemeVersionClaims(versionId, phase ?? undefined),
                    api.getThemeVersionFactors(versionId, phase ?? undefined)
                ]);
            } else {
                [claimsData, factorsData] = await Promise.all([
                    api.getThemeVersionClaims(themeId, phase ?? undefined),
                    api.getThemeFactors(themeId, phase ?? undefined)
                ]);
            }

            setFactors(factorsData);
            setClaims(claimsData);
            setNodes(mapFactors(factorsData));
            setLinks(mapClaims(claimsData));
            setError(null);

            // Non-blocking cycle detectie na de hoofd-refresh
            api.detectCycles(themeId).then(ids => {
                setCycleNodeIds(new Set(ids));
            }).catch(err => {
                console.warn('[useCausaData] Cycle detectie mislukt:', err);
            });
        } catch (err) {
            console.error('Failed to load Causa data:', err);
            setError(err as Error);
            lastFetchRef.current = null; // Allow retry
        } finally {
            setLoading(false);
        }
    }, [themeId, versionId, phase]);

    // Initial Load
    useEffect(() => {
        if (themeId) {
            refresh();
        }
    }, [refresh]);

    return { nodes, links, factors, claims, cycleNodeIds, loading, error, refresh };
};
