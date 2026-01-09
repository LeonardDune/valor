import { useState } from 'react';
import { ProjectList } from './components/Dashboard/ProjectList';
import { ThemeList } from './components/Dashboard/ThemeList';
import { ValorWorkspace } from './components/Workspace/ValorWorkspace';

type ViewSate = 'PROJECT_LIST' | 'THEME_LIST' | 'WORKSPACE';

function App() {
  const [view, setView] = useState<ViewSate>('PROJECT_LIST');
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedProjectName, setSelectedProjectName] = useState<string>('');
  const [selectedThemeId, setSelectedThemeId] = useState<string | null>(null);
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

  const handleBackToProjects = () => {
    setView('PROJECT_LIST');
    setSelectedProjectId(null);
  };

  const handleBackToThemes = () => {
    setView('THEME_LIST');
    setSelectedThemeId(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {view === 'PROJECT_LIST' && (
        <ProjectList onSelectProject={handleSelectProject} />
      )}

      {view === 'THEME_LIST' && selectedProjectId && (
        <ThemeList
          projectId={selectedProjectId}
          projectName={selectedProjectName}
          onSelectTheme={handleSelectTheme}
          onBack={handleBackToProjects}
        />
      )}

      {view === 'WORKSPACE' && selectedProjectId && selectedThemeId && (
        <ValorWorkspace
          projectId={selectedProjectId}
          projectName={selectedProjectName}
          themeId={selectedThemeId}
          themeName={selectedThemeName}
          onBack={handleBackToThemes}
        />
      )}
    </div>
  );
}

export default App;
