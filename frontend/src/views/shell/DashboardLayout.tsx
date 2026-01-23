import React, { useState } from 'react';
import { Sidebar } from '@/components/ui/Sidebar';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { ThemeGrid } from '@/components/dashboard/ThemeGrid';
import { ContextPanel, type OrganizationSummary, type ProjectSummary } from '@/components/dashboard/ContextPanel';
import { useOrganization } from '@/context/OrganizationContext';

interface DashboardLayoutProps {
    children?: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
    // State for responsive toggles
    // We might want to lift this state or use a layout context if needed elsewhere
    const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Mobile sidebar
    const [isContextPanelOpen, setIsContextPanelOpen] = useState(false); // Desktop/Mobile context panel

    const { organizations } = useOrganization();

    // Map organizations context to ContextPanel props
    // TODO: We need a way to fetch 'My Projects' across all organizations for the ContextPanel.
    // For now, we will just show Organizations. Or we could map active org projects.
    // Let's assume for MVP we list Organizations in the context panel.
    const mappedOrgs: OrganizationSummary[] = organizations.map(o => ({
        id: o.id,
        name: o.name,
        description: o.description
    }));

    // Flatten all projects from all organizations for the "My Projects" list
    const mappedProjects: ProjectSummary[] = organizations.flatMap(org =>
        (org.projects || []).map(p => ({
            id: p.id,
            name: p.name,
            organization_name: org.name
        }))
    );

    return (
        <div className="h-screen flex bg-background overflow-hidden font-sans text-foreground">
            {/* Global Navigation Sidebar */}
            {/* Mobile: toggled via state. Desktop: persistent. */}
            {/* Note: The Sidebar component currently handles its own responsiveness via CSS (hidden lg:flex) */}
            {/* We need to ensure mobile drawer logic is handled either inside Sidebar or here. */}
            {/* The refactored Sidebar.tsx has 'hidden lg:flex' but lacks the mobile drawer implementation. */}
            {/* For this step, we rely on the desktop sidebar working and mobile header trigger needing a mobile drawer. */}
            <Sidebar className="hidden lg:flex z-50" />

            {/* Mobile Sidebar Drawer (if implemented in Sidebar or separate) */}
            {/* TODO: Implement MobileDrawer if Sidebar doesn't handle it internally yet */}

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden relative">
                <DashboardHeader
                    onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    onContextPanelClick={() => setIsContextPanelOpen(!isContextPanelOpen)}
                />

                <div className="flex-1 flex overflow-hidden relative">
                    {/* Main Content (Theme Grid or Child Route) */}
                    <main className="flex-1 overflow-y-auto bg-muted/10 relative">
                        {children || <ThemeGrid />}
                    </main>

                    {/* Context Panel (Right Sidebar) */}
                    <ContextPanel
                        organizations={mappedOrgs}
                        projects={mappedProjects}
                        isOpen={isContextPanelOpen}
                        onClose={() => setIsContextPanelOpen(false)}
                    />
                </div>
            </div>
        </div>
    );
};
