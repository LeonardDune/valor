import { useState, useEffect, useRef } from 'react';
import { api, type AxiaSchema } from '../../../services/api';

const _cache: { data: AxiaSchema | null } = { data: null };

interface UseAxiaSchemaResult {
    schema: AxiaSchema | null;
    loading: boolean;
    error: Error | null;
}

export function useAxiaSchema(): UseAxiaSchemaResult {
    const [schema, setSchema] = useState<AxiaSchema | null>(_cache.data);
    const [loading, setLoading] = useState(_cache.data === null);
    const [error, setError] = useState<Error | null>(null);
    const fetchedRef = useRef(_cache.data !== null);

    useEffect(() => {
        if (fetchedRef.current) return;
        fetchedRef.current = true;

        api.getAxiaSchema()
            .then((data) => {
                _cache.data = data;
                setSchema(data);
            })
            .catch((err) => setError(err instanceof Error ? err : new Error(String(err))))
            .finally(() => setLoading(false));
    }, []);

    return { schema, loading, error };
}
