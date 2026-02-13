import { useMemo, useState } from 'react';
import { ThemeCard, type Theme } from './ThemeCard';
import { useThemes, useDashboardThemes } from '@/hooks/queries/useThemes';
import { GridToolbar, type FilterOption, type SortOption, type GroupOption } from './GridToolbar';
import { CreateThemeDialog } from './dialogs/CreateThemeDialog';
import { Button } from '@/components/ui/button';
import { Plus, Layers } from 'lucide-react';
import { ModeratorSection } from './ModeratorSection';

interface ThemeGridProps {
    projectId?: string;
    projectName?: string;
}

export function ThemeGrid({ projectId, projectName }: ThemeGridProps) {
    const { data: projectThemes = [], isLoading: isLoadingProject, refetch: refetchProject } = useThemes(projectId || '');
    const { data: dashboardThemes = [], isLoading: isLoadingDashboard, refetch: refetchDashboard } = useDashboardThemes();

    const isLoading = projectId ? isLoadingProject : isLoadingDashboard;
    const refetch = projectId ? refetchProject : refetchDashboard;

    // Unified themes list for display
    const themes = useMemo(() => {
        if (projectId) {
            return (projectThemes as any[]).map(t => ({
                ...t,
                organization_name: '', // Will be empty in project-specific view
                project_name: projectName || '',
                type: 'THEME' as const
            }));
        }
        return dashboardThemes;
    }, [projectId, projectName, projectThemes, dashboardThemes]);

    // Toolbar State
    const [searchQuery, setSearchQuery] = useState('');
    const [currentSort, setCurrentSort] = useState('name_asc');
    const [currentGroup, setCurrentGroup] = useState('none');
    const [activeFilters, setActiveFilters] = useState<Record<string, string[]>>({
        status: ['active']
    });

    // Filtering & Sorting
    const filteredThemes = useMemo(() => {
        return (themes as any[]).filter(t => {
            // Search
            const matchesSearch = !searchQuery ||
                t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                (t.description || '').toLowerCase().includes(searchQuery.toLowerCase());

            // Status
            const statusFilter = activeFilters.status || [];
            const isArchived = t.status === 'archived' || t.is_archived;
            const matchesStatus = statusFilter.length === 0 ||
                (statusFilter.includes('active') && !isArchived) ||
                (statusFilter.includes('archived') && isArchived);

            // Org/Project (Global)
            const orgFilter = activeFilters.organization || [];
            const matchesOrg = orgFilter.length === 0 || orgFilter.includes(t.organization_name);

            const projFilter = activeFilters.project || [];
            const matchesProj = projectId || projFilter.length === 0 || (t.project_name && projFilter.includes(t.project_name));

            return matchesSearch && matchesStatus && matchesOrg && matchesProj;
        }).sort((a, b) => {
            switch (currentSort) {
                case 'name_asc': return a.name.localeCompare(b.name);
                case 'name_desc': return b.name.localeCompare(a.name);
                case 'claims': return (b.stats?.active_claims || 0) - (a.stats?.active_claims || 0);
                case 'members': return (b.stats?.members || 0) - (a.stats?.members || 0);
                default: return 0;
            }
        });
    }, [themes, searchQuery, activeFilters, currentSort, projectId]);

    // Grouping
    const groupedData = useMemo(() => {
        if (currentGroup === 'project' && !projectId) {
            const groups: Record<string, Theme[]> = {};
            filteredThemes.forEach(t => {
                const key = t.project_name || 'Geen Project';
                if (!groups[key]) groups[key] = [];
                groups[key].push(t);
            });
            return Object.entries(groups).map(([name, items]) => ({ name, items }));
        }
        if (currentGroup === 'organization') {
            const groups: Record<string, Theme[]> = {};
            filteredThemes.forEach(t => {
                const key = t.organization_name || 'Geen Organisatie';
                if (!groups[key]) groups[key] = [];
                groups[key].push(t);
            });
            return Object.entries(groups).map(([name, items]) => ({ name, items }));
        }
        if (currentGroup === 'status') {
            const groups: Record<string, Theme[]> = {
                'Actief': [],
                'Gearchiveerd': []
            };
            filteredThemes.forEach(t => {
                const key = (t.status === 'archived' || t.is_archived) ? 'Gearchiveerd' : 'Actief';
                groups[key].push(t);
            });
            return Object.entries(groups).filter(([_, items]) => items.length > 0).map(([name, items]) => ({ name, items }));
        }
        return [{ name: '', items: filteredThemes }];
    }, [filteredThemes, currentGroup, projectId]);

    // Toolbar Options
    const sortOptions: SortOption[] = [
        { label: 'Alfabetisch (A-Z)', value: 'name_asc' },
        { label: 'Alfabetisch (Z-A)', value: 'name_desc' },
        { label: 'Meeste Claims', value: 'claims' },
        { label: 'Meeste Leden', value: 'members' },
    ];

    const groupOptions: GroupOption[] = [
        { label: 'Per Status', value: 'status' },
    ];
    if (!projectId) {
        groupOptions.push({ label: 'Per Project', value: 'project' });
        groupOptions.push({ label: 'Per Organisatie', value: 'organization' });
    }

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

    if (!projectId) {
        const uniqueOrgs = Array.from(new Set((themes as any[]).map(t => t.organization_name).filter(Boolean))) as string[];
        if (uniqueOrgs.length > 1) {
            filterConfig.push({
                label: 'Organisatie',
                field: 'organization',
                options: uniqueOrgs.map(org => ({ label: org, value: org }))
            });
        }
        const uniqueProjs = Array.from(new Set((themes as any[]).map(t => t.project_name).filter(Boolean))) as string[];
        if (uniqueProjs.length > 1) {
            filterConfig.push({
                label: 'Project',
                field: 'project',
                options: uniqueProjs.map(p => ({ label: p, value: p }))
            });
        }
    }

    if (isLoading && themes.length === 0) {
        return (
            <div className="flex-1 p-4 lg:p-8 space-y-6">
                <div className="h-20 bg-muted/20 rounded-xl animate-pulse" />
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-72 bg-muted/10 rounded-xl border border-muted/20 animate-pulse"></div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 lg:p-8">
            {!projectId && <ModeratorSection />}

            <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-primary mb-1">
                        <Layers className="h-5 w-5" />
                        <span className="text-sm font-semibold uppercase tracking-wider">Thema's</span>
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight">
                        {projectName ? `Thema's in ${projectName}` : "Mijn Thema's"}
                    </h2>
                    <p className="text-muted-foreground">
                        {projectName
                            ? `Overzicht van alle thema's binnen het project ${projectName}.`
                            : `Verken de ${filteredThemes.length} thema's waar je momenteel toegang toe hebt.`}
                    </p>
                </div>

                {projectId && (
                    <CreateThemeDialog
                        projectId={projectId}
                        onSuccess={() => refetch()}
                        trigger={
                            <Button className="gap-2 shadow-lg shadow-primary/20">
                                <Plus className="h-4 w-4" />
                                Nieuw Thema
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

            {filteredThemes.length === 0 ? (
                <div className="text-center py-20 bg-muted/5 rounded-2xl border border-dashed border-border/50">
                    <p className="text-muted-foreground mb-4">Geen thema's gevonden die voldoen aan je criteria.</p>
                    {projectId && (
                        <CreateThemeDialog
                            projectId={projectId}
                            onSuccess={() => refetch()}
                            trigger={
                                <Button variant="outline">
                                    Maak je eerste thema aan
                                </Button>
                            }
                        />
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
                                {group.items.map((theme) => (
                                    <ThemeCard key={theme.id} theme={theme} onUpdate={() => refetch()} />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
