import { useEffect, useState, useMemo, useCallback } from 'react';
import { ProjectCard, type Project } from './ProjectCard';
import { api } from '@/services/api';
import { GridToolbar, type FilterOption, type SortOption, type GroupOption } from './GridToolbar';
import { CreateProjectDialog } from './dialogs/CreateProjectDialog';
import { Button } from '@/components/ui/button';
import { Plus, Briefcase } from 'lucide-react';

interface ProjectGridProps {
    organizationId?: string;
    organizationName?: string;
}

export function ProjectGrid({ organizationId, organizationName }: ProjectGridProps) {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    // Toolbar State
    const [searchQuery, setSearchQuery] = useState('');
    const [currentSort, setCurrentSort] = useState('name_asc');
    const [currentGroup, setCurrentGroup] = useState('none');
    const [activeFilters, setActiveFilters] = useState<Record<string, string[]>>({
        status: ['active'] // Default only active
    });

    const fetchProjects = useCallback(async (clearFirst: boolean = false) => {
        if (clearFirst) setProjects([]);
        setLoading(true);
        setError(null);
        try {
            let allProjects: Project[] = [];
            if (organizationId) {
                const data = await api.getProjects(organizationId);
                allProjects = data.map((p: any) => ({
                    ...p,
                    organization_id: organizationId,
                    organization_name: organizationName,
                    type: 'PROJECT'
                }));
            } else {
                const data = await api.getDashboardEnvironments();
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
            }
            setProjects(allProjects);
        } catch (err) {
            console.error("Failed to fetch projects", err);
            setError("Kon projecten niet laden.");
        } finally {
            setLoading(false);
        }
    }, [organizationId, organizationName]);

    useEffect(() => {
        fetchProjects(true);
    }, [fetchProjects]);

    // Filtering & Sorting Logic
    const filteredProjects = useMemo(() => {
        return projects.filter(proj => {
            // Search
            const matchesSearch = !searchQuery ||
                proj.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                proj.description?.toLowerCase().includes(searchQuery.toLowerCase());

            // Status Filter
            const statusFilter = activeFilters.status || [];
            const matchesStatus = statusFilter.length === 0 ||
                (statusFilter.includes('active') && proj.status !== 'archived') ||
                (statusFilter.includes('archived') && proj.status === 'archived');

            // Organization Filter (only if on global view)
            const orgFilter = activeFilters.organization || [];
            const matchesOrg = organizationId || orgFilter.length === 0 ||
                orgFilter.includes(proj.organization_id || '');

            return matchesSearch && matchesStatus && matchesOrg;
        }).sort((a, b) => {
            if (currentSort === 'name_asc') return a.name.localeCompare(b.name);
            if (currentSort === 'name_desc') return b.name.localeCompare(a.name);
            if (currentSort === 'newest') return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
            return 0;
        });
    }, [projects, searchQuery, activeFilters, currentSort, organizationId]);

    // Grouping Logic
    const groupedData = useMemo(() => {
        if (currentGroup === 'organization' && !organizationId) {
            const groups: Record<string, Project[]> = {};
            filteredProjects.forEach(proj => {
                const key = proj.organization_name || 'Onbekende Organisatie';
                if (!groups[key]) groups[key] = [];
                groups[key].push(proj);
            });
            return Object.entries(groups).map(([name, items]) => ({ name, items }));
        }
        return [{ name: '', items: filteredProjects }];
    }, [filteredProjects, currentGroup, organizationId]);

    // Toolbar Config
    const sortOptions: SortOption[] = [
        { label: 'Alfabetisch (A-Z)', value: 'name_asc' },
        { label: 'Alfabetisch (Z-A)', value: 'name_desc' },
        { label: 'Nieuwste eerst', value: 'newest' },
    ];

    const groupOptions: GroupOption[] = organizationId ? [] : [
        { label: 'Per Organisatie', value: 'organization' },
    ];

    const filterConfig: FilterOption[] = [
        {
            label: 'Status',
            field: 'status',
            options: [
                { label: 'Actief', value: 'active' },
                { label: 'Gearchiveerd', value: 'archived' },
            ]
        }
    ];

    // Add Organization filter if global
    if (!organizationId) {
        const uniqueOrgs = Array.from(new Set(projects.map(p => p.organization_id).filter(Boolean)));
        if (uniqueOrgs.length > 1) {
            filterConfig.push({
                label: 'Organisatie',
                field: 'organization',
                options: uniqueOrgs.map(id => ({
                    label: projects.find(p => p.organization_id === id)?.organization_name || 'Onbekend',
                    value: id!
                }))
            });
        }
    }

    if (error) {
        return <div className="p-8 text-destructive">{error}</div>;
    }

    if (loading && projects.length === 0) {
        return (
            <div className="flex-1 p-4 lg:p-8 space-y-6">
                <div className="h-20 bg-muted/20 rounded-xl animate-pulse" />
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                        <div key={i} className="h-64 bg-muted/10 rounded-xl border border-muted/20 animate-pulse"></div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 lg:p-8">
            <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-primary mb-1">
                        <Briefcase className="h-5 w-5" />
                        <span className="text-sm font-semibold uppercase tracking-wider">Projecten</span>
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight">
                        {organizationName ? `Projecten in ${organizationName}` : 'Mijn Projecten'}
                    </h2>
                    <p className="text-muted-foreground">
                        {organizationName
                            ? `Overzicht van alle projecten binnen de organisatie ${organizationName}.`
                            : 'Alle projecten waar je toegang toe hebt, over alle organisaties heen.'}
                    </p>
                </div>

                {organizationId && (
                    <CreateProjectDialog
                        organizationId={organizationId}
                        open={isDialogOpen}
                        onOpenChange={setIsDialogOpen}
                        onSuccess={fetchProjects}
                        trigger={
                            <Button className="gap-2 shadow-lg shadow-primary/20">
                                <Plus className="h-4 w-4" />
                                Nieuw Project
                            </Button>
                        }
                    />
                )}
            </div>

            <GridToolbar
                onSearch={setSearchQuery}
                sortOptions={sortOptions}
                currentSort={currentSort}
                onSortChange={setCurrentSort}
                groupOptions={groupOptions}
                currentGroup={currentGroup}
                onGroupChange={setCurrentGroup}
                filterConfig={filterConfig}
                activeFilters={activeFilters}
                onFilterChange={(field, values) => setActiveFilters(prev => ({ ...prev, [field]: values }))}
            />

            {filteredProjects.length === 0 ? (
                <div className="text-center py-20 bg-muted/5 rounded-2xl border border-dashed border-border/50">
                    <p className="text-muted-foreground mb-4">Geen projecten gevonden die voldoen aan je criteria.</p>
                    {organizationId ? (
                        <Button variant="outline" onClick={() => setIsDialogOpen(true)}>
                            Maak je eerste project aan
                        </Button>
                    ) : (
                        <p className="text-sm text-muted-foreground">Probeer je filters aan te passen of zoekopdracht te wijzigen.</p>
                    )}
                </div>
            ) : (
                <div className="space-y-12">
                    {groupedData.map((group) => (
                        <div key={group.name} className="space-y-6">
                            {group.name && (
                                <div className="flex items-center gap-4">
                                    <h3 className="text-lg font-semibold whitespace-nowrap">{group.name}</h3>
                                    <div className="h-px w-full bg-border/50" />
                                    <span className="text-xs font-medium text-muted-foreground bg-muted/50 px-2 py-1 rounded-full">
                                        {group.items.length}
                                    </span>
                                </div>
                            )}
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                                {group.items.map((proj) => (
                                    <ProjectCard key={proj.id} project={proj} onUpdate={fetchProjects} />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
