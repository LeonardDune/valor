import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { useOrganization } from '../../context/OrganizationContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { CreateProjectDialog } from "./dialogs/CreateProjectDialog";

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
    const { activeOrganization } = useOrganization();
    const [projects, setProjects] = useState<Project[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    useEffect(() => {
        if (activeOrganization) {
            fetchProjects();
        }
    }, [activeOrganization]);

    const fetchProjects = async () => {
        if (!activeOrganization) return;
        setIsLoading(true);
        console.log(`[ProjectList] Fetching projects for org: ${activeOrganization.name} (${activeOrganization.id})`);
        try {
            const data = await api.getProjects(activeOrganization.id);
            console.log(`[ProjectList] Found ${data.length} projects`);
            setProjects(data);
        } catch (error) {
            console.error('[ProjectList] Failed to fetch projects', error);
        } finally {
            setIsLoading(false);
        }
    };


    if (isLoading) return <div className="p-8 text-muted-foreground">Projecten laden...</div>;

    return (
        <div className="max-w-5xl mx-auto p-8 space-y-8">
            <div className="flex justify-between items-end">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">Mijn Projecten</h1>
                    <p className="text-muted-foreground">
                        Beheer projecten voor <span className="font-semibold text-primary">{activeOrganization?.name}</span>.
                    </p>
                </div>

                <CreateProjectDialog
                    organizationId={activeOrganization?.id || ''}
                    open={isDialogOpen}
                    onOpenChange={setIsDialogOpen}
                    trigger={
                        <Button className="gap-2">
                            <Plus className="h-4 w-4" />
                            Nieuw Project
                        </Button>
                    }
                    onSuccess={fetchProjects}
                />
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {projects.map(project => (
                    <Card
                        key={project.id}
                        className="hover:border-primary/50 transition-colors cursor-pointer group relative overflow-hidden"
                        onClick={() => onSelectProject(project.id, project.name)}
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <CardHeader>
                            <CardTitle className="group-hover:text-primary transition-colors">{project.name}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <CardDescription className="line-clamp-3">
                                {project.description || "Geen omschrijving."}
                            </CardDescription>
                        </CardContent>
                        <CardFooter>
                            <div className="flex items-center text-xs text-muted-foreground">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2"></span>
                                Actief
                            </div>
                        </CardFooter>
                    </Card>
                ))}
            </div>

            {projects.length === 0 && (
                <Card className="border-dashed">
                    <CardContent className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                        <p>Nog geen projecten in <span className="font-semibold">{activeOrganization?.name}</span>.</p>
                        <Button variant="link" onClick={() => setIsDialogOpen(true)}>
                            Maak je eerste project aan
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};
