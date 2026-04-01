import { useState, useEffect, useRef } from 'react';
import { api, type SociaOntology } from '../../../services/api';

const _cache: { data: SociaOntology | null } = { data: null };

interface UseSociaOntologyResult {
    ontology: SociaOntology | null;
    loading: boolean;
    error: Error | null;
}

export function useSociaOntology(): UseSociaOntologyResult {
    const [ontology, setOntology] = useState<SociaOntology | null>(_cache.data);
    const [loading, setLoading] = useState(_cache.data === null);
    const [error, setError] = useState<Error | null>(null);
    const fetchedRef = useRef(_cache.data !== null);

    useEffect(() => {
        if (fetchedRef.current) return;
        fetchedRef.current = true;

        api.getSociaOntology()
            .then((data) => {
                _cache.data = data;
                setOntology(data);
            })
            .catch((err) => setError(err instanceof Error ? err : new Error(String(err))))
            .finally(() => setLoading(false));
    }, []);

    return { ontology, loading, error };
}
