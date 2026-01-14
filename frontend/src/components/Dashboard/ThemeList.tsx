import React, { useState, useEffect } from 'react';
import { api, type Theme } from '../../services/api';

interface ThemeListProps {
    projectId: string;
    projectName: string;
    onSelectTheme: (themeId: string, themeName: string) => void;
    onBack: () => void;
}

export const ThemeList: React.FC<ThemeListProps> = ({ projectId, projectName, onSelectTheme, onBack }) => {
    const [themes, setThemes] = useState<Theme[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [newThemeName, setNewThemeName] = useState('');
    const [newThemeDesc, setNewThemeDesc] = useState('');

    useEffect(() => {
        fetchThemes();
    }, [projectId]);

    const fetchThemes = async () => {
        try {
            const data = await api.getProjectThemes(projectId);
            setThemes(data);
        } catch (error) {
            console.error('Failed to fetch themes', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newThemeName) return;

        try {
            await api.createTheme(projectId, newThemeName, newThemeDesc);
            setNewThemeName('');
            setNewThemeDesc('');
            setIsCreating(false);
            fetchThemes();
        } catch (error) {
            console.error('Failed to create theme', error);
        }
    };

    if (isLoading) return <div className="p-8 text-slate-500">Thema's laden...</div>;

    return (
        <div className="max-w-4xl mx-auto p-8">
            <button
                onClick={onBack}
                className="text-slate-500 hover:text-slate-800 mb-6 flex items-center gap-2 text-sm font-medium"
            >
                ← Terug naar Projecten
            </button>

            <div className="flex justify-between items-center mb-8">
                <div>
                    <h2 className="text-xl text-slate-500">Project</h2>
                    <h1 className="text-3xl font-bold text-slate-900">{projectName}</h1>
                    <p className="text-slate-500 mt-2">Selecteer een thema om te verkennen.</p>
                </div>
                <button
                    onClick={() => setIsCreating(true)}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                    + Nieuw Thema
                </button>
            </div>

            {isCreating && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-8 animate-fade-in">
                    <h3 className="text-lg font-semibold mb-4">Nieuw Thema Toevoegen</h3>
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Naam</label>
                            <input
                                type="text"
                                value={newThemeName}
                                onChange={e => setNewThemeName(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="Bijv. Sneeuwoverlast"
                                autoFocus
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Omschrijving</label>
                            <textarea
                                value={newThemeDesc}
                                onChange={e => setNewThemeDesc(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="Wat gaan we onderzoeken?"
                                rows={3}
                            />
                        </div>
                        <div className="flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={() => setIsCreating(false)}
                                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                            >
                                Annuleren
                            </button>
                            <button
                                type="submit"
                                disabled={!newThemeName}
                                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                            >
                                Aanmaken
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-2">
                {themes.map(theme => (
                    <div
                        key={theme.id}
                        onClick={() => onSelectTheme(theme.id, theme.name)}
                        className="bg-white p-6 rounded-xl border border-slate-200 hover:border-indigo-400 hover:shadow-md cursor-pointer transition-all group"
                    >
                        <div className="flex items-start justify-between">
                            <h3 className="text-lg font-semibold text-slate-800 group-hover:text-indigo-600 mb-2">{theme.name}</h3>
                            <span className="bg-indigo-50 text-indigo-700 text-xs px-2 py-1 rounded-full border border-indigo-100">
                                Thema
                            </span>
                        </div>
                        <p className="text-slate-500 text-sm line-clamp-3">
                            {theme.description || "Geen omschrijving."}
                        </p>
                    </div>
                ))}
                {themes.length === 0 && !isCreating && (
                    <div className="col-span-full text-center py-12 text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                        Nog geen thema's in dit project.
                    </div>
                )}
            </div>
        </div>
    );
};
