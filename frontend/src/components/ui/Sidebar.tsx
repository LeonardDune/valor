import { LayoutDashboard, Layers, Eye, Building2, FolderKanban, Settings, type LucideIcon } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

export interface NavItem {
    id: string;
    icon: LucideIcon;
    label: string;
    path: string;
    exact?: boolean; // If true, matches exact path only
}

interface SidebarProps {
    className?: string;
    items?: NavItem[];
}

const defaultNavItems: NavItem[] = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', path: '/', exact: true },
    { id: 'themes', icon: Layers, label: "Mijn Thema's", path: '/dashboard/themes' },
    { id: 'perspectives', icon: Eye, label: 'Perspectieven', path: '/dashboard/perspectives' },
    { id: 'organizations', icon: Building2, label: 'Mijn Organisaties', path: '/dashboard/organizations' },
    { id: 'projects', icon: FolderKanban, label: 'Mijn Projecten', path: '/dashboard/projects' },
    { id: 'settings', icon: Settings, label: 'Instellingen', path: '/settings' },
];

export function Sidebar({ className, items = defaultNavItems }: SidebarProps) {
    const navigate = useNavigate();
    const location = useLocation();

    const handleItemClick = (path: string) => {
        navigate(path);
    };

    return (
        <div className={cn("hidden lg:flex w-16 bg-background border-r border-border flex-col items-center py-6 gap-4 z-50", className)}>
            {/* Logo */}
            <div className="mb-4">
                <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity" onClick={() => navigate('/')}>
                    <span className="text-primary-foreground font-bold text-sm">V</span>
                </div>
            </div>

            {/* Navigation */}
            <TooltipProvider delayDuration={0}>
                <nav className="flex flex-col gap-2 flex-1 w-full px-2">
                    {items.map((item) => {
                        const Icon = item.icon;
                        // Active check
                        const isActive = item.exact
                            ? location.pathname === item.path
                            : location.pathname.startsWith(item.path);

                        return (
                            <Tooltip key={item.id}>
                                <TooltipTrigger asChild>
                                    <button
                                        onClick={() => handleItemClick(item.path)}
                                        className={cn(
                                            "w-12 h-12 rounded-lg flex items-center justify-center transition-all duration-200",
                                            isActive
                                                ? "bg-primary text-primary-foreground shadow-md"
                                                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                                        )}
                                    >
                                        <Icon className="w-5 h-5" />
                                    </button>
                                </TooltipTrigger>
                                <TooltipContent side="right">
                                    <p>{item.label}</p>
                                </TooltipContent>
                            </Tooltip>
                        );
                    })}
                </nav>
            </TooltipProvider>

            {/* Bottom Profile (Placeholder) */}
            <div className="mt-auto pb-4">
                <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-xs font-bold text-muted-foreground cursor-pointer hover:ring-2 ring-primary/20 transition-all">
                    ME
                </div>
            </div>
        </div>
    );
}
