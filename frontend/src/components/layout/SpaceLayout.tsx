import React, { useState } from 'react';
import { Sidebar, type NavItem } from '@/components/ui/Sidebar';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { LayoutDashboard, MessageSquare, FileText, Settings, Users } from 'lucide-react';
import { useParams, Outlet } from 'react-router-dom';

interface SpaceLayoutProps {
    children?: React.ReactNode;
}

export const SpaceLayout: React.FC<SpaceLayoutProps> = ({ children }) => {
    const { spaceId } = useParams();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const spaceNavItems: NavItem[] = [
        {
            id: 'overview',
            icon: LayoutDashboard,
            label: 'Overview',
            path: `/spaces/${spaceId}`,
            exact: true
        },
        {
            id: 'claims',
            icon: FileText,
            label: 'Claims',
            path: `/spaces/${spaceId}/claims`
        },
        {
            id: 'chat',
            icon: MessageSquare,
            label: 'Chat',
            path: `/spaces/${spaceId}/chat`
        },
        {
            id: 'members',
            icon: Users,
            label: 'Members',
            path: `/spaces/${spaceId}/members`
        },
        {
            id: 'settings',
            icon: Settings,
            label: 'Settings',
            path: `/spaces/${spaceId}/settings`
        },
    ];

    return (
        <div className="h-screen flex bg-background overflow-hidden font-sans text-foreground">
            {/* Space Context Sidebar */}
            <Sidebar className="hidden lg:flex z-50" items={spaceNavItems} />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden relative">
                {/* We might want a specialized SpaceHeader here later */}
                <DashboardHeader
                    onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)}
                // Space context panel logic could be added here
                />

                <main className="flex-1 overflow-y-auto bg-muted/10 relative">
                    {children || <Outlet />}
                </main>
            </div>
        </div>
    );
};
