
import { useEffect, useState } from 'react';
import { ThemeCard } from './ThemeCard';
import { api, type DashboardTheme } from '@/services/api';

export function ThemeGrid() {
    const [themes, setThemes] = useState<DashboardTheme[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchThemes = async () => {
        try {
            const data = await api.getDashboardThemes();
            setThemes(data);
        } catch (err) {
            console.error("Failed to fetch themes", err);
            setError("Kon thema's niet laden.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchThemes();
    }, []);

    if (loading) {
        return (
            <div className="flex-1 p-8 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 animate-pulse">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="h-64 bg-muted/20 rounded-xl border border-muted/30"></div>
                ))}
            </div>
        );
    }

    if (error) {
        return <div className="p-8 text-destructive">{error}</div>;
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 lg:p-8">
            <div className="mb-8">
                <h2 className="text-2xl font-bold tracking-tight mb-2">Mijn Thema's</h2>
                <p className="text-muted-foreground">
                    Overzicht van {themes.length} thema's waar je actief toegang toe hebt.
                </p>
            </div>

            {themes.length === 0 ? (
                <div className="text-center py-20 bg-muted/10 rounded-xl border border-dashed">
                    <p className="text-muted-foreground">Je hebt nog geen toegang tot thema's.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {themes.map((theme) => (
                        <ThemeCard
                            key={theme.id}
                            theme={theme}
                            onUpdate={fetchThemes}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
