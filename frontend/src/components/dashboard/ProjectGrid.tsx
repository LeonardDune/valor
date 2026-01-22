import { useEffect, useState } from 'react';
import { ProjectCard, type Project } from './ProjectCard';
import { api } from '@/services/api';

export function ProjectGrid() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchAllProjects = async () => {
        try {
            const data = await api.getDashboardEnvironments();

            // Flatten logic: Iterate Orgs -> Extract Projects -> Enrich with Org Name
            const allProjects: Project[] = [];

            data.forEach((org: any) => {
                if (org.projects && Array.isArray(org.projects)) {
                    org.projects.forEach((proj: any) => {
                        allProjects.push({
                            ...proj,
                            organization_name: org.name,
                            organization_id: org.id
                        });
                    });
                }
            });

            setProjects(allProjects);
        } catch (err) {
            console.error("Failed to fetch projects", err);
            setError("Kon projecten niet laden.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAllProjects();
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
            <div className="mb-8 flex items-end justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight mb-2">Mijn Projecten</h2>
                    <p className="text-muted-foreground">
                        Alle projecten waar je toegang toe hebt, over alle organisaties heen.
                    </p>
                </div>
                {/* Create Project is usually context-dependent (need Org), so maybe redirect to Org view or show general info */}
                {/* Current choice: No Global Create button, users should create via Organization or Theme context, 
                     OR we could add a button that opens a dialog requiring Org selection. 
                     For simplicity/MVP: No button here, manage via Org. */}
            </div>

            {projects.length === 0 ? (
                <div className="text-center py-20 bg-muted/10 rounded-xl border border-dashed">
                    <p className="text-muted-foreground mb-4">Je hebt nog geen toegang tot projecten.</p>
                    <p className="text-sm text-muted-foreground">Maak een organisatie aan of vraag om uitgenodigd te worden.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {projects.map((proj) => (
                        <ProjectCard key={proj.id} project={proj} onUpdate={fetchAllProjects} />
                    ))}
                </div>
            )}
        </div>
    );
}
