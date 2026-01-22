import { useNavigate } from 'react-router-dom';
import { MoreVertical, Layers, Briefcase, Building2, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useState } from 'react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle
} from '@/components/ui/card';
import { ManageEntityDialog } from './dialogs/ManageEntityDialog';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { api } from '@/services/api';
import { toast } from 'sonner';

export interface Project {
    id: string;
    name: string;
    description?: string;
    organization_name?: string;
    organization_id?: string;
    role?: string;
    status?: string;
    type: 'PROJECT';
    themes?: any[];
    created_at?: string;
}

interface ProjectCardProps {
    project: Project;
    onUpdate?: () => void;
}

export function ProjectCard({ project, onUpdate }: ProjectCardProps) {
    const navigate = useNavigate();
    const [isManageDialogOpen, setIsManageDialogOpen] = useState(false);
    const [isArchiveConfirmOpen, setIsArchiveConfirmOpen] = useState(false);
    const [isArchiving, setIsArchiving] = useState(false);

    const themeCount = project.themes?.length || 0;
    const isAdmin = project.role === 'admin';

    const handleCardClick = () => {
        navigate(`/projects/${project.id}`);
    };

    const handleManageClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsManageDialogOpen(true);
    };

    const handleArchiveClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsArchiveConfirmOpen(true);
    };

    const handleArchiveConfirm = async () => {
        setIsArchiving(true);
        try {
            await api.archiveProject(project.id);
            toast.success("Project gearchiveerd");
            onUpdate?.();
        } catch (error) {
            console.error(error);
            toast.error("Fout bij archiveren");
        } finally {
            setIsArchiving(false);
            setIsArchiveConfirmOpen(false);
        }
    };

    return (
        <>
            <Card
                onClick={handleCardClick}
                className="hover:shadow-lg transition-all duration-300 group cursor-pointer flex flex-col h-full relative"
            >
                <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                    <div className="flex-1 pr-4">
                        <CardTitle className="text-lg group-hover:text-primary transition-colors flex items-center gap-2">
                            <Briefcase className="w-4 h-4 text-muted-foreground transition-colors group-hover:text-primary shrink-0" />
                            <span className="truncate">{project.name}</span>
                        </CardTitle>
                        <CardDescription className="line-clamp-2 min-h-[2.5em] mt-1">
                            {project.description || "Geen beschrijving beschikbaar."}
                        </CardDescription>
                    </div>

                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 -mr-2 opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={(e) => e.stopPropagation()}
                            >
                                <MoreVertical className="w-4 h-4 text-muted-foreground" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleCardClick(); }}>
                                Openen
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={handleManageClick} disabled={!isAdmin}>
                                Beheren
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                                onClick={handleArchiveClick}
                                className="text-destructive"
                                disabled={!isAdmin}
                            >
                                Archiveren
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </CardHeader>

                <CardContent className="flex-1 pb-4">
                    <div className="flex flex-wrap gap-2">
                        {project.status === 'archived' && (
                            <Badge variant="destructive" className="font-normal uppercase tracking-wider text-[10px]">
                                Gearchiveerd
                            </Badge>
                        )}
                        <Badge variant="secondary" className="font-normal bg-secondary/30 uppercase tracking-wider text-[10px]">
                            Project
                        </Badge>
                        {project.organization_name && (
                            <Badge variant="secondary" className="font-normal bg-secondary/50 flex items-center gap-1 text-[10px]">
                                <Building2 className="w-3 h-3" />
                                {project.organization_name}
                            </Badge>
                        )}
                        {project.role && (
                            <Badge variant={isAdmin ? "default" : "outline"} className="font-normal uppercase tracking-wider text-[10px]">
                                {project.role === 'admin' ? 'Beheerder' : 'Lid'}
                            </Badge>
                        )}
                    </div>
                </CardContent>

                <CardFooter className="pt-4 border-t border-border flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5" title="Thema's">
                        <Layers className="w-3.5 h-3.5" />
                        <span>{themeCount} Thema's</span>
                    </div>
                    {isAdmin && (
                        <div className="flex items-center gap-1.5 ml-auto text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                            <Settings className="w-3.5 h-3.5" />
                            <span>Instellingen</span>
                        </div>
                    )}
                </CardFooter>
            </Card>

            <ManageEntityDialog
                open={isManageDialogOpen}
                onOpenChange={setIsManageDialogOpen}
                entityId={project.id}
                entityType="project"
                initialData={{
                    name: project.name,
                    description: project.description || '',
                    role: project.role
                }}
                onUpdated={onUpdate}
            />

            <ConfirmModal
                isOpen={isArchiveConfirmOpen}
                onCancel={() => setIsArchiveConfirmOpen(false)}
                onConfirm={handleArchiveConfirm}
                title="Project Archiveren"
                message="Weet je zeker dat je dit project wilt archiveren? Alle onderliggende thema's worden ook verborgen."
                isDanger={true}
                confirmLabel={isArchiving ? "Bezig..." : "Archiveren"}
            />
        </>
    );
}
