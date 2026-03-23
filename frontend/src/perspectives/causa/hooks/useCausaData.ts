import { useState, useCallback, useEffect, useRef } from 'react';
import { api, type Factor, type Claim, type ClaimViewType } from '../../../services/api';
import { mapFactors, mapClaims } from '../layout/mappers';
import type { CausalNode, CausalLink } from '../types';

interface CausaData {
    nodes: CausalNode[];
    links: CausalLink[];
    factors: Factor[]; // Raw data for Modals
    claims: Claim[];   // Raw data for Modals
    loading: boolean;
    error: Error | null;
    refresh: (force?: boolean) => Promise<void>;
    viewFilter: ClaimViewType | null;
    setViewFilter: (filter: ClaimViewType | null) => void;
}

export const useCausaData = (themeId: string, versionId?: string): CausaData => {
    const [nodes, setNodes] = useState<CausalNode[]>([]);
    const [links, setLinks] = useState<CausalLink[]>([]);
    const [factors, setFactors] = useState<Factor[]>([]);
    const [claims, setClaims] = useState<Claim[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const [viewFilter, setViewFilter] = useState<ClaimViewType | null>(null);

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
            setNodes(mapFactors(factorsData));
            setLinks(mapClaims(claimsData));
            setError(null);
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

    // Lokale filter: nodes altijd zichtbaar, links gefilterd op claimType
    const filteredLinks = viewFilter === null
        ? links
        : links.filter(link => (link as any).claimType === viewFilter || !(link as any).claimType);

    return { nodes, links: filteredLinks, factors, claims, loading, error, refresh, viewFilter, setViewFilter };
};
