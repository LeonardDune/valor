import React, { useState } from 'react';
import { Sidebar, type NavItem } from '@/components/ui/Sidebar';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { LayoutDashboard, MessageSquare, FileText, Settings, Users } from 'lucide-react';
import { useParams, Outlet } from 'react-router-dom';

interface VersionLayoutProps {
    children?: React.ReactNode;
}

export const VersionLayout: React.FC<VersionLayoutProps> = ({ children }) => {
    // We use 'versionId' in the route now (was spaceId)
    // Fallback to spaceId if router hasn't been fully updated yet during dev
    const params = useParams();
    const versionId = params.versionId || params.spaceId;
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const versionNavItems: NavItem[] = [
        {
            id: 'overview',
            icon: LayoutDashboard,
            label: 'Overview',
            path: `/versions/${versionId}`,
            exact: true
        },
        {
            id: 'claims',
            icon: FileText,
            label: 'Claims',
            path: `/versions/${versionId}/claims`
        },
        {
            id: 'chat',
            icon: MessageSquare,
            label: 'Chat',
            path: `/versions/${versionId}/chat`
        },
        {
            id: 'members',
            icon: Users,
            label: 'Members',
            path: `/versions/${versionId}/members`
        },
        {
            id: 'settings',
            icon: Settings,
            label: 'Settings',
            path: `/versions/${versionId}/settings`
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
