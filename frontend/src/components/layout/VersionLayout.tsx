import React, { useState } from 'react';
import { Sidebar, type NavItem } from '@/components/ui/Sidebar';
import {
    LayoutDashboard,
    MessageSquare,
    FileText,
    Settings,
    Users,
    GitBranch,
    Clock,
    Workflow,
    Maximize2,
    Minimize2,
} from 'lucide-react';
import { useParams, Outlet, useSearchParams, useNavigate } from 'react-router-dom';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { PhaseSelector } from '@/components/deliberation/PhaseSelector';
import { MemberManagement } from '@/components/Settings/MemberManagement';
import { DesignSpaceProvider } from '@/context/DesignSpaceContext';
import { useDesignSpace } from '@/context/DesignSpaceContext';
import { useOrganization } from '@/context/OrganizationContext';

type AgentType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

interface VersionLayoutInnerProps {
    projectName: string;
    themeName: string;
    dsId: string;
}

const VersionLayoutInner: React.FC<VersionLayoutInnerProps> = ({ projectName, themeName, dsId }) => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [focusMode, setFocusMode] = useState(false);

    const { phaseSnapshots, activePhaseId, setActivePhaseId } = useDesignSpace();

    const activeAgent = (searchParams.get('mode') as AgentType) || 'CAUSA';

    const handleAgentChange = (val: string) => {
        if (!val) return;
        navigate(`/designspace/${dsId}?mode=${val}`);
    };

    const versionNavItems: NavItem[] = [
        {
            id: 'overview',
            icon: LayoutDashboard,
            label: 'Overview',
            path: `/designspace/${dsId}/overview`,
        },
        {
            id: 'workspace',
            icon: Workflow,
            label: 'Werkruimte',
            path: `/designspace/${dsId}`,
            exact: true,
        },
        {
            id: 'claims',
            icon: FileText,
            label: 'Verfijn',
            path: `/designspace/${dsId}/claims`,
        },
        {
            id: 'argumentatie',
            icon: GitBranch,
            label: 'Argumentatie',
            path: `/designspace/${dsId}/argumentatie`,
        },
        {
            id: 'tijdlijn',
            icon: Clock,
            label: 'Tijdlijn',
            path: `/designspace/${dsId}/tijdlijn`,
        },
        {
            id: 'chat',
            icon: MessageSquare,
            label: 'Chat',
            path: `/designspace/${dsId}/chat`,
        },
        {
            id: 'members',
            icon: Users,
            label: 'Leden',
            path: `/designspace/${dsId}/members`,
        },
        {
            id: 'settings',
            icon: Settings,
            label: 'Instellingen',
            path: `/designspace/${dsId}/settings`,
        },
    ];

    return (
        <div className="h-screen flex bg-background overflow-hidden font-sans text-foreground">
            <Sidebar className="hidden lg:flex z-50" items={versionNavItems} />

            <div className="flex-1 flex flex-col overflow-hidden">
                {!focusMode && (
                    <header className="h-14 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-4 shrink-0 z-30">
                        <div className="flex flex-col">
                            <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold leading-none mb-1">
                                {projectName}
                            </span>
                            <span className="text-sm font-bold leading-none">{themeName}</span>
                        </div>

                        <div className="flex items-center gap-4">
                            <ToggleGroup
                                type="single"
                                value={activeAgent}
                                onValueChange={handleAgentChange}
                            >
                                <ToggleGroupItem value="CAUSA" aria-label="Toggle CAUSA">CAUSA</ToggleGroupItem>
                                <ToggleGroupItem value="AXIA" disabled aria-label="Toggle AXIA">
                                    AXIA <span className="ml-1.5 text-[9px] opacity-70">SOON</span>
                                </ToggleGroupItem>
                                <ToggleGroupItem value="ACTOR" disabled aria-label="Toggle ACTOR">
                                    ACTOR <span className="ml-1.5 text-[9px] opacity-70">SOON</span>
                                </ToggleGroupItem>
                                <ToggleGroupItem value="PRAXIS" disabled aria-label="Toggle PRAXIS">
                                    PRAXIS <span className="ml-1.5 text-[9px] opacity-70">SOON</span>
                                </ToggleGroupItem>
                            </ToggleGroup>
                        </div>

                        <div className="flex items-center gap-2">
                            <PhaseSelector
                                snapshots={phaseSnapshots}
                                activePhaseId={activePhaseId}
                                onSelect={setActivePhaseId}
                            />
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setIsSettingsOpen(true)}
                                title="Thema Instellingen & Leden"
                            >
                                <Settings size={18} />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setFocusMode(!focusMode)}
                                title={focusMode ? 'Focusmodus verlaten' : 'Focusmodus'}
                                className={focusMode ? 'text-primary bg-primary/10' : ''}
                            >
                                {focusMode ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                            </Button>
                        </div>
                    </header>
                )}

                {focusMode && (
                    <div className="absolute top-2 right-2 z-50">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setFocusMode(false)}
                            title="Focusmodus verlaten"
                            className="text-primary bg-primary/10"
                        >
                            <Minimize2 size={18} />
                        </Button>
                    </div>
                )}

                <main className="flex-1 overflow-hidden relative">
                    <Outlet />
                </main>
            </div>

            <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
                <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto" aria-describedby={undefined}>
                    <DialogHeader>
                        <DialogTitle>Thema Instellingen: {themeName}</DialogTitle>
                    </DialogHeader>
                    <div className="py-4">
                        <MemberManagement entityId={dsId} entityType="theme" />
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export const VersionLayout: React.FC = () => {
    const { dsId } = useParams<{ dsId: string }>();
    const { organizations, isLoading } = useOrganization();

    const found = organizations
        .flatMap(org => org.projects.flatMap(proj =>
            proj.themes.map(theme => ({ project: proj, theme }))
        ))
        .find(item => item.theme.id === dsId);

    if (isLoading) {
        return <div className="flex items-center justify-center h-screen text-muted-foreground">Laden...</div>;
    }

    if (!found) {
        return <div className="flex items-center justify-center h-screen text-muted-foreground">DesignSpace niet gevonden of geen toegang.</div>;
    }

    return (
        <DesignSpaceProvider dsId={found.theme.id}>
            <VersionLayoutInner
                projectName={found.project.name}
                themeName={found.theme.name}
                dsId={found.theme.id}
            />
        </DesignSpaceProvider>
    );
};
