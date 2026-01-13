import { useState } from 'react';
import { ProjectList } from './components/Dashboard/ProjectList';
import { ThemeList } from './components/Dashboard/ThemeList';
import { ValorWorkspace } from './components/Workspace/ValorWorkspace';
import { UserList } from './components/Settings/UserList';
import { Sidebar } from './components/UI/Sidebar'; // New Sidebar
import { useOrganization } from './context/OrganizationContext';
import { useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';

type ViewSate = 'PROJECT_LIST' | 'THEME_LIST' | 'WORKSPACE' | 'SETTINGS';

function App() {
  const { session, isLoading: authLoading } = useAuth();
  const { activeOrganization, organizations, isLoading: orgLoading } = useOrganization();
  const [view, setView] = useState<ViewSate>('PROJECT_LIST');
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedProjectName, setSelectedProjectName] = useState<string>('');
  const [selectedThemeId, setSelectedThemeId] = useState<string>(''); // Changed to string (not null) to satisfy TS if needed, or handle null check
  const [selectedThemeName, setSelectedThemeName] = useState<string>('');

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
    // Go to theme list of current project
    setView('THEME_LIST');
    // Keep selectedProjectId
  };

  if (authLoading || orgLoading) {
    return <div className="flex items-center justify-center min-h-screen text-slate-500">Laden...</div>;
  }

  if (!session) {
    return <LoginPage />;
  }

  if (organizations.length === 0) {
    return <OnboardingPage />;
  }

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900 overflow-hidden">

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
        {view === 'SETTINGS' && activeOrganization && (
          <div className="p-8">
            <UserList organizationId={activeOrganization.id} />
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
