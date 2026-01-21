import { useState, useEffect } from 'react';
import { ProjectList } from './components/dashboard/ProjectList';
import { ThemeList } from './components/dashboard/ThemeList';
import { ValorWorkspace } from './components/Workspace/ValorWorkspace';
import { MemberManagement } from './components/Settings/MemberManagement';
import { Sidebar } from './components/ui/Sidebar'; // New Sidebar
import { useOrganization } from './context/OrganizationContext';
import { useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';
import { AcceptInvitePage } from './pages/AcceptInvitePage';

import { DashboardLayout } from './views/shell/DashboardLayout';

type ViewSate = 'PROJECT_LIST' | 'THEME_LIST' | 'WORKSPACE' | 'SETTINGS' | 'ACCEPT_INVITE' | 'DASHBOARD';

function App() {
  const { session, isLoading: authLoading } = useAuth();
  const { activeOrganization, organizations, isLoading: orgLoading, refreshOrganizations } = useOrganization();
  const [view, setView] = useState<ViewSate>('DASHBOARD'); // Start at Dashboard
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedProjectName, setSelectedProjectName] = useState<string>('');
  const [selectedThemeId, setSelectedThemeId] = useState<string>('');
  const [selectedThemeName, setSelectedThemeName] = useState<string>('');

  // Check URL query params for invite code on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('code') || window.location.pathname.includes('/invite')) {
      setView('ACCEPT_INVITE');
    }
  }, []);

  const handleSelectProject = (id: string, name: string) => {
    setSelectedProjectId(id);
    setSelectedProjectName(name);
    setView('THEME_LIST');
  };

  const handleSelectTheme = (id: string, name: string) => {
    setSelectedThemeId(id);
    setSelectedThemeName(name);
    setView('WORKSPACE');
  };

  const handleNavigateProject = () => {
    setView('PROJECT_LIST');
    setSelectedProjectId(null);
  };

  const handleNavigateThemeList = () => {
    setView('THEME_LIST');
    // Keep selectedProjectId
  };

  const handleInviteSuccess = async () => {
    // Refresh organizations to show the new one
    await refreshOrganizations();
    setView('PROJECT_LIST');
    // URL is cleared in AcceptInvitePage, but good to be sure
  };

  if (authLoading) { // Removed orgLoading check for View 'ACCEPT_INVITE' potential
    return <div className="flex items-center justify-center min-h-screen text-slate-500">Laden...</div>;
  }

  if (!session) {
    return <LoginPage />;
  }

  // Special case: If accepting invite, do not block on organizations.length === 0
  if (view === 'ACCEPT_INVITE') {
    return <AcceptInvitePage onSuccess={handleInviteSuccess} />;
  }

  // Only block if not loading and no orgs
  if (!orgLoading && organizations.length === 0) {
    return <OnboardingPage />;
  }

  return (
    <div className="flex h-screen bg-canvas font-sans text-text-primary overflow-hidden">

      {/* Sidebar Navigation */}
      <Sidebar
        view={view}
        setView={setView}
        selectedProjectName={selectedProjectName}
        selectedThemeName={selectedThemeName}
        onNavigateProject={handleNavigateProject}
        onNavigateTheme={handleNavigateThemeList}
      />

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto relative flex flex-col">
        {view === 'DASHBOARD' && (
          <DashboardLayout />
        )}

        {view === 'SETTINGS' && activeOrganization && (
          <div className="p-8">
            <MemberManagement entityId={activeOrganization.id} entityType="organization" />
          </div>
        )}

        {view === 'PROJECT_LIST' && activeOrganization && (
          <div className="p-8">
            <ProjectList onSelectProject={handleSelectProject} />
          </div>
        )}

        {view === 'THEME_LIST' && selectedProjectId && (
          <div className="h-full">
            <ThemeList
              projectId={selectedProjectId}
              projectName={selectedProjectName}
              onSelectTheme={handleSelectTheme}
              onBack={handleNavigateProject}
            />
          </div>
        )}

        {view === 'WORKSPACE' && selectedProjectId && selectedThemeId && (
          <div className="h-full">
            <ValorWorkspace
              projectId={selectedProjectId}
              projectName={selectedProjectName}
              themeId={selectedThemeId}
              themeName={selectedThemeName}
              onBack={handleNavigateThemeList}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
