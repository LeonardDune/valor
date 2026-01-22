import { useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, useParams } from 'react-router-dom';
import { OrganizationGrid } from './components/dashboard/OrganizationGrid';
import { ProjectGrid } from './components/dashboard/ProjectGrid';
import { ThemeGrid } from './components/dashboard/ThemeGrid';
import { PerspectivesLanding } from './views/shell/PerspectivesLanding';
import { ValorWorkspace } from './components/Workspace/ValorWorkspace';
import { MemberManagement } from './components/Settings/MemberManagement';

import { useOrganization } from './context/OrganizationContext';
import { useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';
import { AcceptInvitePage } from './pages/AcceptInvitePage';
import { DashboardLayout } from './views/shell/DashboardLayout';

function App() {
  const { session, isLoading: authLoading } = useAuth();
  const { activeOrganization, organizations, isLoading: orgLoading, refreshOrganizations } = useOrganization();
  const navigate = useNavigate();
  const location = useLocation();

  // Handle Invitations
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('code') || window.location.pathname.includes('/invite')) {
      // Let the Route handle it
    }
  }, []);

  const handleInviteSuccess = async () => {
    await refreshOrganizations();
    navigate('/');
  };

  if (authLoading) {
    return <div className="flex items-center justify-center min-h-screen text-slate-500">Laden...</div>;
  }

  if (!session) {
    return <LoginPage />;
  }

  // Determine if we should show Onboarding
  const showOnboarding = !orgLoading && organizations.length === 0 && !location.pathname.includes('/invite');

  if (showOnboarding) {
    return <OnboardingPage />;
  }

  return (
    <div className="flex h-screen bg-canvas font-sans text-text-primary overflow-hidden">
      {/* Sidebar removed here, managed by DashboardLayout */}

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto relative flex flex-col">
        <Routes>
          <Route path="/" element={<DashboardLayout><ThemeGrid /></DashboardLayout>} />
          <Route path="/dashboard" element={<DashboardLayout><ThemeGrid /></DashboardLayout>} />
          <Route path="/dashboard/themes" element={<DashboardLayout><ThemeGrid /></DashboardLayout>} />

          <Route path="/dashboard/organizations" element={
            <DashboardLayout>
              <OrganizationGrid />
            </DashboardLayout>
          } />

          <Route path="/dashboard/projects" element={
            <DashboardLayout>
              <ProjectGrid />
            </DashboardLayout>
          } />

          <Route path="/dashboard/perspectives" element={
            <DashboardLayout>
              <PerspectivesLanding />
            </DashboardLayout>
          } />

          {/* Organization View (Project List) - Wrapped */}
          <Route path="/organizations/:orgId" element={
            <DashboardLayout>
              <OrganizationRouteWrapper />
            </DashboardLayout>
          } />

          {/* Project View (Theme List) - Wrapped */}
          <Route path="/projects/:projectId" element={
            <DashboardLayout>
              <div className="h-full">
                <ThemeListWrapper />
              </div>
            </DashboardLayout>
          } />

          {/* Workspace View (Theme Context) - Wrapped (Maybe? Or does workspace need full screen?) */}
          {/* Workspace usually needs its own layout or full screen. Keeping it wrapped for now for consistency, but maybe Sidebar should be collapsible there. */}
          {/* Actually Workspace likely wants full screen with its own internal nav. Let's keep it wrapped for consistency of Global Nav. */}
          <Route path="/themes/:themeId" element={
            <DashboardLayout>
              <div className="h-full">
                <WorkspaceWrapper />
              </div>
            </DashboardLayout>
          } />

          {/* Settings - Wrapped */}
          <Route path="/settings" element={
            activeOrganization ? (
              <DashboardLayout>
                <div className="p-8">
                  <MemberManagement entityId={activeOrganization.id} entityType="organization" />
                </div>
              </DashboardLayout>
            ) : <Navigate to="/" />
          } />

          <Route path="/invite" element={<AcceptInvitePage onSuccess={handleInviteSuccess} />} />
        </Routes>
      </main>
    </div>
  );
}

// Wrappers to adapt explicit ID routing to components that might need specific props
const ThemeListWrapper = () => {
  const { projectId } = useParams();
  const { organizations } = useOrganization();

  // Find project name in context data
  const project = organizations
    .flatMap(org => org.projects)
    .find(p => p.id === projectId);

  return (
    <ThemeGrid
      projectId={projectId!}
      projectName={project?.name || "Project"}
    />
  );
}

const WorkspaceWrapper = () => {
  const { themeId } = useParams();
  const navigate = useNavigate();
  return (
    <ValorWorkspace
      projectId="unknown"
      projectName="unknown"
      themeId={themeId!}
      themeName="Theme"
      onBack={() => navigate(-1)}
    />
  );
}

const OrganizationRouteWrapper = () => {
  const { orgId } = useParams();
  const { activeOrganization, switchOrganization, organizations, isLoading } = useOrganization();

  useEffect(() => {
    // Sync URL -> Context for global components (Sidebar, etc)
    if (orgId && organizations.length > 0 && activeOrganization?.id !== orgId) {
      switchOrganization(orgId);
    }
  }, [orgId, organizations, activeOrganization, switchOrganization]);

  if (isLoading) return <div className="p-8">Laden...</div>;

  // Source of truth is the URL orgId. We find the org in the loaded list.
  // This avoids rendering with a stale 'activeOrganization' from context while switching.
  const currentOrg = organizations.find(o => o.id === orgId) || activeOrganization;

  if (!currentOrg) {
    // If we have organizations but the ID is invalid
    if (organizations.length > 0) {
      return <Navigate to="/" />;
    }
    return <div className="p-8">Laden...</div>;
  }

  return (
    <ProjectGrid
      organizationId={currentOrg.id}
      organizationName={currentOrg.name}
    />
  );
};

export default App;
