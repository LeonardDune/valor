import React, { useState, useEffect } from 'react';

interface Project {
    id: string;
    name: string;
    description: string;
    created_at: string;
}

interface ProjectListProps {
    onSelectProject: (projectId: string, projectName: string) => void;
}

export const ProjectList: React.FC<ProjectListProps> = ({ onSelectProject }) => {
    const [projects, setProjects] = useState<Project[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [newProjectName, setNewProjectName] = useState('');
    const [newProjectDesc, setNewProjectDesc] = useState('');

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const res = await fetch('http://localhost:8000/projects');
            const data = await res.json();
            setProjects(data);
        } catch (error) {
            console.error('Failed to fetch projects', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newProjectName) return;

        try {
            const res = await fetch('http://localhost:8000/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newProjectName, description: newProjectDesc }),
            });
            if (res.ok) {
                setNewProjectName('');
                setNewProjectDesc('');
                setIsCreating(false);
                fetchProjects();
            }
        } catch (error) {
            console.error('Failed to create project', error);
        }
    };

    if (isLoading) return <div className="p-8 text-slate-500">Projecten laden...</div>;

    return (
        <div className="max-w-4xl mx-auto p-8">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Mijn Projecten</h1>
                    <p className="text-slate-500 mt-2">Beheer je VALOR projecten en dossiers.</p>
                </div>
                <button
                    onClick={() => setIsCreating(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                    + Nieuw Project
                </button>
            </div>

            {isCreating && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-8 animate-fade-in">
                    <h3 className="text-lg font-semibold mb-4">Nieuw Project Starten</h3>
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Naam</label>
                            <input
                                type="text"
                                value={newProjectName}
                                onChange={e => setNewProjectName(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="Bijv. Bereikbaarheid Randstad"
                                autoFocus
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Omschrijving</label>
                            <textarea
                                value={newProjectDesc}
                                onChange={e => setNewProjectDesc(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="Korte toelichting op het project..."
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
                                disabled={!newProjectName}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                            >
                                Aanmaken
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {projects.map(project => (
                    <div
                        key={project.id}
                        onClick={() => onSelectProject(project.id, project.name)}
                        className="bg-white p-6 rounded-xl border border-slate-200 hover:border-blue-400 hover:shadow-md cursor-pointer transition-all group"
                    >
                        <h3 className="text-lg font-semibold text-slate-800 group-hover:text-blue-600 mb-2">{project.name}</h3>
                        <p className="text-slate-500 text-sm line-clamp-3">
                            {project.description || "Geen omschrijving."}
                        </p>
                        <div className="mt-4 flex items-center text-xs text-slate-400">
                            <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
                            Actief
                        </div>
                    </div>
                ))}
                {projects.length === 0 && !isCreating && (
                    <div className="col-span-full text-center py-12 text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                        Nog geen projecten. Maak er eentje aan om te beginnen!
                    </div>
                )}
            </div>
        </div>
    );
};
