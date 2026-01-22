import { Building2, FolderKanban, ChevronRight } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useNavigate } from 'react-router-dom';
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";

export interface OrganizationSummary {
    id: string;
    name: string;
    description?: string;
}

export interface ProjectSummary {
    id: string;
    name: string;
    organization_name: string;
}

interface ContextPanelProps {
    organizations: OrganizationSummary[];
    projects: ProjectSummary[];
    isOpen: boolean;
    onClose: () => void;
}

export function ContextPanel({ organizations, projects, isOpen, onClose }: ContextPanelProps) {
    const navigate = useNavigate();

    const handleNavigate = (path: string) => {
        onClose();
        navigate(path);
    };

    return (
        <Sheet open={isOpen} onOpenChange={onClose}>
            <SheetContent side="right" className="w-[320px] sm:w-[400px] p-0 flex flex-col">
                <SheetHeader className="p-6 border-b">
                    <SheetTitle className="text-lg font-semibold flex items-center gap-2">
                        Context
                    </SheetTitle>
                </SheetHeader>

                <ScrollArea className="flex-1">
                    <div className="p-6 space-y-8">
                        {/* Organizations Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-4 text-muted-foreground">
                                <Building2 className="w-4 h-4" />
                                <h3 className="text-xs font-semibold uppercase tracking-wider">Mijn Organisaties</h3>
                            </div>
                            <div className="space-y-2">
                                {organizations.map((org) => (
                                    <button
                                        key={org.id}
                                        onClick={() => handleNavigate(`/organizations/${org.id}`)}
                                        className="w-full p-3 rounded-lg border border-border bg-card hover:bg-accent hover:text-accent-foreground transition-all text-left group flex items-center gap-3"
                                    >
                                        <div className="w-8 h-8 rounded-md bg-primary/10 text-primary flex items-center justify-center font-bold text-[10px] uppercase shrink-0">
                                            {org.name.substring(0, 2)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium text-sm truncate">{org.name}</div>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                                    </button>
                                ))}
                                {organizations.length === 0 && (
                                    <p className="text-xs text-muted-foreground italic">Geen organisaties gevonden.</p>
                                )}
                            </div>
                        </section>

                        {/* Projects Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-4 text-muted-foreground">
                                <FolderKanban className="w-4 h-4" />
                                <h3 className="text-xs font-semibold uppercase tracking-wider">Mijn Projecten</h3>
                            </div>
                            <div className="space-y-2">
                                {projects.map((project) => (
                                    <button
                                        key={project.id}
                                        onClick={() => handleNavigate(`/projects/${project.id}`)}
                                        className="w-full p-3 rounded-lg border border-border bg-card hover:bg-accent hover:text-accent-foreground transition-all text-left group"
                                    >
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="font-medium text-sm truncate">{project.name}</div>
                                            <ChevronRight className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                                        </div>
                                        <div className="text-[10px] text-muted-foreground truncate">{project.organization_name}</div>
                                    </button>
                                ))}
                                {projects.length === 0 && (
                                    <p className="text-xs text-muted-foreground italic">Geen projecten gevonden.</p>
                                )}
                            </div>
                        </section>
                    </div>
                </ScrollArea>
            </SheetContent>
        </Sheet>
    );
}
