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
import { UpdatePasswordPage } from './pages/UpdatePasswordPage';
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

  // Public Routes (No Auth Required)
  // Check if we are on a specific public route BEFORE ensuring session
  if (location.pathname === '/login' || location.pathname === '/invite') {
    // Logic handled by Routes below if we render them, but here we return early if *not* authenticated?
    // Actually, LoginPage is rendered if !session.
  }

  if (!session) {
    // Basic protection
    return (
      <Routes>
        <Route path="/invite" element={<AcceptInvitePage onSuccess={handleInviteSuccess} />} />
        <Route path="*" element={<LoginPage />} />
      </Routes>
    );
  }

  // Determine if we should show Onboarding
  const showOnboarding =
    !orgLoading &&
    !authLoading &&
    organizations.length === 0 &&
    !location.pathname.includes('/invite') &&
    !location.pathname.includes('/update-password'); // Don't block password update!

  if (showOnboarding) {
    return <OnboardingPage />;
  }

  return (
    <div className="flex h-screen bg-canvas font-sans text-text-primary overflow-hidden">
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

          <Route path="/organizations/:orgId" element={
            <DashboardLayout>
              <OrganizationRouteWrapper />
            </DashboardLayout>
          } />

          <Route path="/projects/:projectId" element={
            <DashboardLayout>
              <div className="h-full">
                <ThemeListWrapper />
              </div>
            </DashboardLayout>
          } />

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
          <Route path="/update-password" element={<UpdatePasswordPage />} />
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
  const { organizations, isLoading } = useOrganization();

  // Find the context (Project & Theme) from the loaded structure
  // Need to traverse Org -> Project -> Theme
  const found = organizations.flatMap(org =>
    org.projects.flatMap(proj =>
      proj.themes.map(theme => ({
        project: proj,
        theme
      }))
    )
  ).find(item => item.theme.id === themeId);

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Laden...</div>;
  }

  if (!found) {
    return <div className="flex items-center justify-center h-screen">Thema niet gevonden of geen toegang.</div>;
  }

  return (
    <ValorWorkspace
      projectId={found.project.id}
      projectName={found.project.name}
      themeId={found.theme.id}
      themeName={found.theme.name}
      onBack={() => navigate(-1)} // Or navigate to project view
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
