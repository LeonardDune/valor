import { useEffect, useState, useMemo } from 'react';
import { OrganizationCard, type Organization } from './OrganizationCard';
import { api } from '@/services/api';
import { CreateOrganizationDialog } from './dialogs/CreateOrganizationDialog';
import { GridToolbar, type FilterOption, type SortOption } from './GridToolbar';
import { Button } from '@/components/ui/button';
import { Plus, Building2 } from 'lucide-react';

export function OrganizationGrid() {
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Toolbar State
    const [searchQuery, setSearchQuery] = useState('');
    const [currentSort, setCurrentSort] = useState('name_asc');
    const [activeFilters, setActiveFilters] = useState<Record<string, string[]>>({
        status: ['active']
    });

    const fetchOrganizations = async () => {
        try {
            setLoading(true);
            const data = await api.getDashboardEnvironments();
            const orgs = data.filter((node: any) => node.type === 'ORGANIZATION');
            setOrganizations(orgs);
        } catch (err) {
            console.error("Failed to fetch organizations", err);
            setError("Kon organisaties niet laden.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchOrganizations();
    }, []);

    // Filter & Sort
    const filteredOrgs = useMemo(() => {
        return organizations.filter(org => {
            const matchesSearch = !searchQuery ||
                org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                org.description?.toLowerCase().includes(searchQuery.toLowerCase());

            const statusFilter = activeFilters.status || [];
            const matchesStatus = statusFilter.length === 0 ||
                (statusFilter.includes('active') && org.status !== 'archived') ||
                (statusFilter.includes('archived') && org.status === 'archived');

            return matchesSearch && matchesStatus;
        }).sort((a, b) => {
            if (currentSort === 'name_asc') return a.name.localeCompare(b.name);
            if (currentSort === 'name_desc') return b.name.localeCompare(a.name);
            return 0;
        });
    }, [organizations, searchQuery, activeFilters, currentSort]);

    const sortOptions: SortOption[] = [
        { label: 'Alfabetisch (A-Z)', value: 'name_asc' },
        { label: 'Alfabetisch (Z-A)', value: 'name_desc' },
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

    if (error) {
        return <div className="p-8 text-destructive">{error}</div>;
    }

    if (loading && organizations.length === 0) {
        return (
            <div className="flex-1 p-4 lg:p-8 space-y-6">
                <div className="h-20 bg-muted/20 rounded-xl animate-pulse" />
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
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
                        <Building2 className="h-5 w-5" />
                        <span className="text-sm font-semibold uppercase tracking-wider">Organisaties</span>
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight">Mijn Organisaties</h2>
                    <p className="text-muted-foreground">
                        Beheer de organisaties waar je lid van bent.
                    </p>
                </div>
                <CreateOrganizationDialog
                    trigger={
                        <Button className="gap-2 shadow-lg shadow-primary/20">
                            <Plus size={16} />
                            Nieuwe Organisatie
                        </Button>
                    }
                    onSuccess={fetchOrganizations}
                />
            </div>

            <GridToolbar
                onSearch={setSearchQuery}
                sortOptions={sortOptions}
                currentSort={currentSort}
                onSortChange={setCurrentSort}
                filterConfig={filterConfig}
                activeFilters={activeFilters}
                onFilterChange={(field, values) => setActiveFilters(prev => ({ ...prev, [field]: values }))}
            />

            {filteredOrgs.length === 0 ? (
                <div className="text-center py-20 bg-muted/5 rounded-2xl border border-dashed border-border/50">
                    <p className="text-muted-foreground mb-4">Geen organisaties gevonden.</p>
                    <CreateOrganizationDialog
                        trigger={
                            <Button variant="outline">Start een Organisatie</Button>
                        }
                        onSuccess={fetchOrganizations}
                    />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filteredOrgs.map((org) => (
                        <OrganizationCard
                            key={org.id}
                            organization={org}
                            onUpdate={fetchOrganizations}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
