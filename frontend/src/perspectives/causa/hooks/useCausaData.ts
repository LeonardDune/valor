import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { api, type Factor, type Claim } from '../../../services/api';
import { mapFactors, mapClaims } from '../layout/mappers';
import type { CausalNode, CausalLink } from '../types';
import type { ViewFilter } from '../components/AsIsToBeToggle';

interface CausaData {
    nodes: CausalNode[];
    links: CausalLink[];
    factors: Factor[]; // Raw data for Modals
    claims: Claim[];   // Raw data for Modals
    loading: boolean;
    error: Error | null;
    refresh: (force?: boolean) => Promise<void>;
    cycleNodeIds: string[];
}

export const useCausaData = (themeId: string, versionId?: string, viewFilter: ViewFilter = 'Beide'): CausaData => {
    const [allNodes, setAllNodes] = useState<CausalNode[]>([]);
    const [allLinks, setAllLinks] = useState<CausalLink[]>([]);
    const [factors, setFactors] = useState<Factor[]>([]);
    const [claims, setClaims] = useState<Claim[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const [cycleNodeIds, setCycleNodeIds] = useState<string[]>([]);

    const lastFetchRef = useRef<string | null>(null);

    const refresh = useCallback(async (force = false) => {
        const fetchKey = `${themeId}-${versionId || 'active'}`;
        if (!force && lastFetchRef.current === fetchKey && !loading) return;

        try {
            setLoading(true);
            lastFetchRef.current = fetchKey;
            let claimsData: Claim[];
            let factorsData: Factor[];

            console.log('[useCausaData] Refreshing...', { themeId, versionId, force });

            if (versionId) {
                [claimsData, factorsData] = await Promise.all([
                    api.getThemeVersionClaims(versionId),
                    api.getThemeVersionFactors(versionId)
                ]);
            } else {
                [claimsData, factorsData] = await Promise.all([
                    api.getThemeClaims(themeId),
                    api.getThemeFactors(themeId)
                ]);
            }

            setFactors(factorsData);
            setClaims(claimsData);
            setAllNodes(mapFactors(factorsData));
            setAllLinks(mapClaims(claimsData));
            setError(null);

            // Async cyclusdetectie — non-blocking, geen UI-blokkering
            api.detectCycles(themeId).then(setCycleNodeIds).catch(() => {
                setCycleNodeIds([]);
            });
        } catch (err) {
            console.error('Failed to load Causa data:', err);
            setError(err as Error);
            lastFetchRef.current = null; // Allow retry
        } finally {
            setLoading(false);
        }
    }, [themeId, versionId]);

    // Initial Load
    useEffect(() => {
        if (themeId) {
            refresh();
        }
    }, [refresh]);

    // Gefilterde links op basis van viewFilter.
    // Nodes blijven altijd volledig zichtbaar (AC-3: nodes met beide types altijd zichtbaar).
    const links = useMemo(() => {
        if (viewFilter === 'Beide') return allLinks;
        return allLinks.filter(l => !l.claimType || l.claimType === viewFilter);
    }, [allLinks, viewFilter]);

    return { nodes: allNodes, links, factors, claims, loading, error, refresh, cycleNodeIds };
};
