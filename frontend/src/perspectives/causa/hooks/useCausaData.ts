import { useState, useCallback, useEffect } from 'react';
import { api } from '../../../services/api';
import { mapFactors, mapClaims } from '../layout/mappers';
import type { CausalNode, CausalLink } from '../types';

interface CausaData {
    nodes: CausalNode[];
    links: CausalLink[];
    loading: boolean;
    error: Error | null;
    refresh: () => Promise<void>;
}

export const useCausaData = (themeId: string): CausaData => {
    const [nodes, setNodes] = useState<CausalNode[]>([]);
    const [links, setLinks] = useState<CausalLink[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const refresh = useCallback(async () => {
        try {
            setLoading(true);
            const [claimsData, factorsData] = await Promise.all([
                api.getThemeClaims(themeId),
                api.getThemeFactors(themeId)
            ]);

            setNodes(mapFactors(factorsData));
            setLinks(mapClaims(claimsData));
            setError(null);
        } catch (err) {
            console.error('Failed to load Causa data:', err);
            setError(err as Error);
        } finally {
            setLoading(false);
        }
    }, [themeId]);

    // Initial Load
    useEffect(() => {
        if (themeId) {
            refresh();
        }
    }, [themeId, refresh]);

    return { nodes, links, loading, error, refresh };
};
