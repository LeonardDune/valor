import { useNavigate } from 'react-router-dom';
import { MoreVertical, Users, Briefcase, Building2 } from 'lucide-react';
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

export interface Organization {
    id: string;
    name: string;
    description?: string;
    role?: string;
    status?: string;
    type: 'ORGANIZATION';
    projects?: any[];
}

interface OrganizationCardProps {
    organization: Organization;
    onUpdate?: () => void;
}

export function OrganizationCard({ organization, onUpdate }: OrganizationCardProps) {
    const navigate = useNavigate();
    const [isManageDialogOpen, setIsManageDialogOpen] = useState(false);
    const [isArchiveConfirmOpen, setIsArchiveConfirmOpen] = useState(false);
    const [isArchiving, setIsArchiving] = useState(false);

    const projectCount = organization.projects?.length || 0;
    const isAdmin = organization.role === 'admin';

    const handleCardClick = () => {
        navigate(`/organizations/${organization.id}`);
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
            await api.archiveOrganization(organization.id);
            toast.success("Organisatie gearchiveerd");
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
                            <Building2 className="w-5 h-5 text-muted-foreground transition-colors group-hover:text-primary shrink-0" />
                            <span className="truncate">{organization.name}</span>
                        </CardTitle>
                        <CardDescription className="line-clamp-2 min-h-[2.5em] mt-1">
                            {organization.description || "Geen beschrijving beschikbaar."}
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
                        {organization.status === 'archived' && (
                            <Badge variant="destructive" className="font-normal uppercase tracking-wider text-[10px]">
                                Gearchiveerd
                            </Badge>
                        )}
                        <Badge variant="secondary" className="font-normal bg-secondary/30 uppercase tracking-wider text-[10px]">
                            Organisatie
                        </Badge>
                        {organization.role && (
                            <Badge variant={isAdmin ? "default" : "outline"} className="font-normal uppercase tracking-wider text-[10px]">
                                {organization.role === 'admin' ? 'Beheerder' : 'Lid'}
                            </Badge>
                        )}
                    </div>
                </CardContent>

                <CardFooter className="pt-4 border-t border-border flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5" title="Projecten">
                        <Briefcase className="w-3.5 h-3.5" />
                        <span>{projectCount} Projecten</span>
                    </div>
                    {isAdmin && (
                        <div className="flex items-center gap-1.5 ml-auto text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                            <Users className="w-3.5 h-3.5" />
                            <span>Beheer Leden</span>
                        </div>
                    )}
                </CardFooter>
            </Card>

            {/* Management Dialog stays outside the clickable Card to prevent bubbling issues */}
            {isManageDialogOpen && (
                <ManageEntityDialog
                    open={isManageDialogOpen}
                    onOpenChange={setIsManageDialogOpen}
                    entityId={organization.id}
                    entityType="organization"
                    initialData={{
                        name: organization.name,
                        description: organization.description || '',
                        role: organization.role
                    }}
                    onUpdated={onUpdate}
                />
            )}

            <ConfirmModal
                isOpen={isArchiveConfirmOpen}
                onCancel={() => setIsArchiveConfirmOpen(false)}
                onConfirm={handleArchiveConfirm}
                title="Organisatie Archiveren"
                message="Weet je zeker dat je deze organisatie wilt archiveren? Alle onderliggende projecten en thema's worden ook verborgen."
                isDanger={true}
                confirmLabel={isArchiving ? "Bezig..." : "Archiveren"}
            />
        </>
    );
}
