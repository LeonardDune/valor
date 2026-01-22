import { useEffect, useState } from 'react';
import { OrganizationCard, type Organization } from './OrganizationCard';
import { api } from '@/services/api'; // Using existing environment API
import { CreateOrganizationDialog } from './dialogs/CreateOrganizationDialog';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export function OrganizationGrid() {
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchOrganizations = async () => {
        try {
            const data = await api.getDashboardEnvironments();
            // Filter only top-level nodes which are organizations
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
                    <h2 className="text-2xl font-bold tracking-tight mb-2">Mijn Organisaties</h2>
                    <p className="text-muted-foreground">
                        Beheer de organisaties waar je lid van bent.
                    </p>
                </div>
                <CreateOrganizationDialog
                    trigger={
                        <Button className="gap-2">
                            <Plus size={16} />
                            Nieuwe Organisatie
                        </Button>
                    }
                    onSuccess={fetchOrganizations}
                />
            </div>

            {organizations.length === 0 ? (
                <div className="text-center py-20 bg-muted/10 rounded-xl border border-dashed">
                    <p className="text-muted-foreground mb-4">Je bent nog geen lid van een organisatie.</p>
                    <CreateOrganizationDialog
                        trigger={
                            <Button variant="outline">Start een Organisatie</Button>
                        }
                        onSuccess={fetchOrganizations}
                    />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {organizations.map((org) => (
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
