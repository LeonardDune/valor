import React, { useState } from 'react';
import { Sidebar, type NavItem } from '@/components/ui/Sidebar';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { LayoutDashboard, MessageSquare, FileText, Settings, Users, GitBranch, Clock } from 'lucide-react';
import { useParams, Outlet } from 'react-router-dom';

interface VersionLayoutProps {
    children?: React.ReactNode;
}

export const VersionLayout: React.FC<VersionLayoutProps> = ({ children }) => {
    const { dsId } = useParams();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const versionNavItems: NavItem[] = [
        {
            id: 'overview',
            icon: LayoutDashboard,
            label: 'Overview',
            path: `/designspace/${dsId}/overview`,
        },
        {
            id: 'claims',
            icon: FileText,
            label: 'Verfijn',
            path: `/designspace/${dsId}/claims`
        },
        {
            id: 'argumentatie',
            icon: GitBranch,
            label: 'Argumentatie',
            path: `/designspace/${dsId}/argumentatie`
        },
        {
            id: 'tijdlijn',
            icon: Clock,
            label: 'Tijdlijn',
            path: `/designspace/${dsId}/tijdlijn`
        },
        {
            id: 'chat',
            icon: MessageSquare,
            label: 'Chat',
            path: `/designspace/${dsId}/chat`
        },
        {
            id: 'members',
            icon: Users,
            label: 'Members',
            path: `/designspace/${dsId}/members`
        },
        {
            id: 'settings',
            icon: Settings,
            label: 'Settings',
            path: `/designspace/${dsId}/settings`
        },
    ];

    return (
        <div className="h-screen flex bg-background overflow-hidden font-sans text-foreground">
            {/* Version Context Sidebar */}
            <Sidebar className="hidden lg:flex z-50" items={versionNavItems} />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden relative">
                <DashboardHeader
                    onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)}
                />

                <main className="flex-1 overflow-y-auto bg-muted/10 relative">
                    {children || <Outlet />}
                </main>
            </div>
        </div>
    );
};
