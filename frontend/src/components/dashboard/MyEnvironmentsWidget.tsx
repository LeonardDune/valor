import React, { useEffect, useState } from 'react';
import { Panel } from '@/design-system/primitives/Panel';
import { ChevronRight, ChevronDown, MoreVertical, Plus, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';
import { useOrganization } from '@/context/OrganizationContext';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';
import { CreateOrganizationDialog } from './dialogs/CreateOrganizationDialog';
import { toast } from 'sonner';

// Types (should eventually be in types file)
interface EnvironmentNode {
    id: string;
    name: string;
    type: 'ORGANIZATION' | 'PROJECT' | 'THEME';
    role?: string;
    status?: string;
    description?: string;
    projects?: EnvironmentNode[]; // For ORG
    themes?: EnvironmentNode[];   // For PROJECT
}

interface WidgetProps {
    className?: string;
}

const EnvironmentItem: React.FC<{
    node: EnvironmentNode;
    level: number;
    onNavigate: (node: EnvironmentNode) => void;
    userId?: string;
}> = ({ node, level, onNavigate, userId }) => {
    const [expanded, setExpanded] = useState(true);
    const hasChildren = (node.projects && node.projects.length > 0) || (node.themes && node.themes.length > 0);

    const getIcon = () => {
        if (level === 0) return <div className="w-2 h-2 rounded-full bg-primary mr-2" />; // Org
        if (level === 1) return <div className="w-1.5 h-1.5 rounded-sm bg-muted-foreground mr-2" />; // Project
        return <div className="w-1 h-1 rounded-full bg-muted mr-2" />; // Theme
    };

    const handleInvite = (e: React.MouseEvent) => {
        e.stopPropagation();
        toast.info("Uitnodigingen komen binnenkort beschikbaar in deze weergave.");
    };

    const handleAccessRequest = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!userId) {
            toast.error("Je bent niet ingelogd.");
            return;
        }

        try {
            await api.createProposal({
                title: `Toegangsaanvraag: ${node.name}`,
                description: `Software gegenereerde toegangsaanvraag voor ${node.type} ${node.name}`,
                type: 'ACCESS_REQUEST',
                author_id: userId,
                target_id: node.id
            });
            toast.success("Aanvraag verstuurd!");
        } catch (error) {
            console.error(error);
            toast.error("Aanvraag versturen mislukt.");
        }
    };

    return (
        <div className="select-none">
            <div
                className={`
                  flex items-center justify-between p-2 rounded-md hover:bg-accent/50 cursor-pointer group
                  ${level > 0 ? 'ml-4 border-l border-white/5 pl-4' : 'mb-1'}
                `}
                onClick={(e) => {
                    e.stopPropagation();
                    onNavigate(node);
                }}
            >
                <div className="flex items-center flex-1 overflow-hidden">
                    {/* Explicit Expand Button for nodes with children */}
                    <div
                        className={`mr-2 cursor-pointer p-1 hover:bg-white/10 rounded ${hasChildren ? '' : 'invisible'}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            setExpanded(!expanded);
                        }}
                    >
                        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </div>

                    {getIcon()}

                    <span className="truncate text-sm font-medium">{node.name}</span>
                    {node.role && <span className="ml-2 text-[10px] bg-secondary px-1 rounded text-secondary-foreground uppercase tracking-wider">{node.role}</span>}
                </div>

                <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button variant="ghost" size="icon" className="h-6 w-6 mr-1" onClick={(e) => {
                        e.stopPropagation();
                        onNavigate(node);
                    }}>
                        <ArrowRight size={14} />
                    </Button>

                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-6 w-6">
                                <MoreVertical size={14} />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => onNavigate(node)}>Werkruimte Openen</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem disabled>Details Bekijken</DropdownMenuItem>
                            <DropdownMenuItem onClick={handleInvite} disabled={!node.role || node.role !== 'admin'}>
                                Lid Uitnodigen
                            </DropdownMenuItem>

                            <DropdownMenuItem onClick={handleAccessRequest}>
                                Toegang Aanvragen / Upgrade
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>

            {expanded && hasChildren && (
                <div className="animate-in fade-in slide-in-from-top-1 duration-200">
                    {node.projects?.map(p => <EnvironmentItem key={p.id} node={p} level={level + 1} onNavigate={onNavigate} userId={userId} />)}
                    {node.themes?.map(t => <EnvironmentItem key={t.id} node={t} level={level + 1} onNavigate={onNavigate} userId={userId} />)}
                </div>
            )}
        </div>
    );
};


export const MyEnvironmentsWidget: React.FC<WidgetProps> = ({ className }) => {
    const [data, setData] = useState<EnvironmentNode[]>([]);
    const [loading, setLoading] = useState(true);
    const { switchOrganization } = useOrganization();
    const { user } = useAuth(); // Get real user

    useEffect(() => {
        // Use standard API client
        const load = async () => {
            try {
                const envs = await api.getDashboardEnvironments();
                setData(envs);
            } catch (err) {
                console.error("Failed to load environments", err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    const navigate = useNavigate();

    const handleNavigate = (node: EnvironmentNode) => {
        if (node.type === 'ORGANIZATION') {
            switchOrganization(node.id);
            navigate(`/organizations/${node.id}`);
        } else if (node.type === 'PROJECT') {
            navigate(`/projects/${node.id}`);
        } else if (node.type === 'THEME') {
            navigate(`/themes/${node.id}`);
        }
    };

    return (
        <Panel className={`flex flex-col h-full ${className}`}>
            <div className="flex items-center justify-between p-4 border-b border-white/5">
                <h3 className="font-medium text-lg">Mijn Omgevingen</h3>
                <CreateOrganizationDialog
                    trigger={
                        <Button variant="ghost" size="sm"><Plus size={16} /></Button>
                    }
                    onSuccess={() => window.location.reload()}
                />
            </div>

            <ScrollArea className="flex-1 p-4">
                {loading && <div className="text-muted-foreground text-sm">Laden...</div>}

                {!loading && data.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-6 text-center space-y-3">
                        <div className="text-muted-foreground text-sm italic">Je bent nog geen lid van een organisatie.</div>
                        <CreateOrganizationDialog
                            trigger={
                                <Button variant="outline" size="sm" className="gap-2">
                                    <Plus size={14} />
                                    Nieuwe Organisatie
                                </Button>
                            }
                            onSuccess={() => window.location.reload()}
                        />
                    </div>
                )}

                {!loading && data.map(org => (
                    <EnvironmentItem key={org.id} node={org} level={0} onNavigate={handleNavigate} userId={user?.id} />
                ))}
            </ScrollArea>
        </Panel>
    );
};
