import { useNavigate } from 'react-router-dom';
import { MoreVertical, Activity, Users, MessageSquare } from 'lucide-react';
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

export interface Theme {
    id: string;
    name: string;
    description: string;
    organization_name: string;
    project_name?: string;
    role?: string;
    status?: string;
    is_archived?: boolean;
    stats?: {
        active_claims: number;
        members: number;
    };
    perspectives?: {
        name: string;
        color: string;
        progress: number;
    }[];
}

interface ThemeCardProps {
    theme: Theme;
    onUpdate?: () => void;
}

// Mock output for visual fidelity
const DEFAULT_PERSPECTIVES = [
    { name: 'CAUSA', color: '#3B82F6', progress: 0 },
    { name: 'NORM', color: '#10B981', progress: 0 },
    { name: 'ACTOR', color: '#8B5CF6', progress: 0 },
    { name: 'VALUE', color: '#F59E0B', progress: 0 },
];

export function ThemeCard({ theme, onUpdate }: ThemeCardProps) {
    const navigate = useNavigate();
    const [isManageDialogOpen, setIsManageDialogOpen] = useState(false);
    const [isArchiveConfirmOpen, setIsArchiveConfirmOpen] = useState(false);
    const [isArchiving, setIsArchiving] = useState(false);

    const perspectives = theme.perspectives || DEFAULT_PERSPECTIVES;
    const commentCount = theme.stats?.active_claims || 0;
    const memberCount = theme.stats?.members || 1;
    const isAdmin = theme.role === 'admin';

    const handlePerspectiveClick = (e: React.MouseEvent, mode: string) => {
        e.stopPropagation();
        navigate(`/designspace/${theme.id}?mode=${mode}`);
    };

    const handleCardClick = () => {
        navigate(`/designspace/${theme.id}`);
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
            await api.archiveTheme(theme.id);
            toast.success("Thema gearchiveerd");
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
                        <CardTitle className="text-lg group-hover:text-primary transition-colors truncate">
                            {theme.name}
                        </CardTitle>
                        <CardDescription className="line-clamp-2 min-h-[2.5em] mt-1">
                            {theme.description || "Geen beschrijving beschikbaar."}
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
                    <div className="flex flex-wrap gap-2 mb-4">
                        {(theme.status === 'archived' || theme.is_archived) && (
                            <Badge variant="destructive" className="font-normal uppercase tracking-wider text-[10px]">
                                Gearchiveerd
                            </Badge>
                        )}
                        <Badge variant="secondary" className="font-normal bg-secondary/30 uppercase tracking-wider text-[10px]">
                            Thema
                        </Badge>
                        {theme.role && (
                            <Badge variant={isAdmin ? "default" : "outline"} className="font-normal uppercase tracking-wider text-[10px]">
                                {theme.role === 'admin' ? 'Beheerder' : 'Lid'}
                            </Badge>
                        )}
                        <Badge variant="secondary" className="font-normal bg-secondary/50 text-[10px]">
                            {theme.organization_name}
                        </Badge>
                        {theme.project_name && (
                            <Badge variant="outline" className="font-normal text-muted-foreground border-dashed text-[10px]">
                                {theme.project_name}
                            </Badge>
                        )}
                    </div>

                    {/* Perspectives Grid */}
                    <div className="space-y-3">
                        <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
                            Perspectieven
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            {perspectives.map((perspective) => (
                                <div
                                    key={perspective.name}
                                    role="button"
                                    onClick={(e) => handlePerspectiveClick(e, perspective.name)}
                                    className="p-2.5 rounded-lg border border-border bg-background/50 hover:bg-accent/50 hover:border-accent-foreground/20 transition-all text-left group/perspective flex flex-col gap-2"
                                    style={{ borderLeftColor: perspective.color, borderLeftWidth: '3px' }}
                                >
                                    <div className="flex items-center justify-between">
                                        <span
                                            className="text-xs font-bold"
                                            style={{ color: perspective.color }}
                                        >
                                            {perspective.name}
                                        </span>
                                        {perspective.progress > 0 && <span className="text-[10px] text-muted-foreground">{perspective.progress}%</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </CardContent>

                <CardFooter className="pt-4 border-t border-border flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5" title="Claims / Argumenten">
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>{commentCount}</span>
                    </div>
                    <div className="flex items-center gap-1.5" title="Leden">
                        <Users className="w-3.5 h-3.5" />
                        <span>{memberCount}</span>
                    </div>
                    <div className="flex items-center gap-1.5 ml-auto">
                        <Activity className="w-3.5 h-3.5" />
                        <span>{(theme.status === 'archived' || theme.is_archived) ? 'Gearchiveerd' : 'Actief'}</span>
                    </div>
                </CardFooter>
            </Card >

            <ManageEntityDialog
                open={isManageDialogOpen}
                onOpenChange={setIsManageDialogOpen}
                entityId={theme.id}
                entityType="theme"
                initialData={{
                    name: theme.name,
                    description: theme.description || '',
                    role: theme.role
                }}
                onUpdated={onUpdate}
            />

            <ConfirmModal
                isOpen={isArchiveConfirmOpen}
                onCancel={() => setIsArchiveConfirmOpen(false)}
                onConfirm={handleArchiveConfirm}
                title="Thema Archiveren"
                message="Weet je zeker dat je dit thema wilt archiveren?"
                isDanger={true}
                confirmLabel={isArchiving ? "Bezig..." : "Archiveren"}
            />
        </>
    );
}
