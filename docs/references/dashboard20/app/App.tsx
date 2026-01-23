import { useState } from 'react';
import { Sidebar } from '@/app/components/Sidebar';
import { DashboardHeader } from '@/app/components/DashboardHeader';
import { ThemeCard, Theme } from '@/app/components/ThemeCard';
import { RightPanel } from '@/app/components/RightPanel';
import { Layers } from 'lucide-react';

// Perspective colors
const PERSPECTIVE_COLORS = {
  CAUSA: '#3B82F6',
  NORM: '#10B981',
  ACTOR: '#8B5CF6',
  VALUE: '#F59E0B',
};

// Mock data
const mockThemes: Theme[] = [
  {
    id: '1',
    name: 'Duurzaamheid in de publieke sector',
    description: 'Onderzoek naar duurzame praktijken en beleid binnen gemeentelijke organisaties.',
    organization: 'Gemeente Amsterdam',
    project: 'Klimaattransitie 2030',
    perspectives: [
      { name: 'CAUSA', color: PERSPECTIVE_COLORS.CAUSA, progress: 75 },
      { name: 'NORM', color: PERSPECTIVE_COLORS.NORM, progress: 60 },
      { name: 'ACTOR', color: PERSPECTIVE_COLORS.ACTOR, progress: 85 },
      { name: 'VALUE', color: PERSPECTIVE_COLORS.VALUE, progress: 45 },
    ],
    activity: {
      comments: 24,
      members: 8,
      lastUpdate: '2 uur geleden',
    },
  },
  {
    id: '2',
    name: 'Digitale transformatie zorgverlening',
    description: 'Analyse van digitalisering in de gezondheidszorg en impact op patiëntenzorg.',
    organization: 'Ministerie VWS',
    perspectives: [
      { name: 'CAUSA', color: PERSPECTIVE_COLORS.CAUSA, progress: 90 },
      { name: 'NORM', color: PERSPECTIVE_COLORS.NORM, progress: 70 },
      { name: 'ACTOR', color: PERSPECTIVE_COLORS.ACTOR, progress: 55 },
      { name: 'VALUE', color: PERSPECTIVE_COLORS.VALUE, progress: 80 },
    ],
    activity: {
      comments: 15,
      members: 5,
      lastUpdate: '1 dag geleden',
    },
  },
  {
    id: '3',
    name: 'Participatie in stedelijke ontwikkeling',
    description: 'Evaluatie van burgerparticipatie methoden bij grote infrastructuurprojecten.',
    organization: 'Provincie Utrecht',
    project: 'Ruimtelijke Ordening',
    perspectives: [
      { name: 'CAUSA', color: PERSPECTIVE_COLORS.CAUSA, progress: 40 },
      { name: 'NORM', color: PERSPECTIVE_COLORS.NORM, progress: 85 },
      { name: 'ACTOR', color: PERSPECTIVE_COLORS.ACTOR, progress: 90 },
      { name: 'VALUE', color: PERSPECTIVE_COLORS.VALUE, progress: 65 },
    ],
    activity: {
      comments: 31,
      members: 12,
      lastUpdate: '3 uur geleden',
    },
  },
  {
    id: '4',
    name: 'Inclusief onderwijsbeleid',
    description: 'Onderzoek naar effectiviteit van inclusief onderwijs en sociale gelijkheid.',
    organization: 'Onderwijsraad',
    perspectives: [
      { name: 'CAUSA', color: PERSPECTIVE_COLORS.CAUSA, progress: 65 },
      { name: 'NORM', color: PERSPECTIVE_COLORS.NORM, progress: 75 },
      { name: 'ACTOR', color: PERSPECTIVE_COLORS.ACTOR, progress: 70 },
      { name: 'VALUE', color: PERSPECTIVE_COLORS.VALUE, progress: 90 },
    ],
    activity: {
      comments: 18,
      members: 6,
      lastUpdate: '5 uur geleden',
    },
  },
  {
    id: '5',
    name: 'Circulaire economie in de bouw',
    description: 'Verkenning van circulaire principes in de bouwsector en materiaalkringlopen.',
    organization: 'Gemeente Amsterdam',
    project: 'Duurzame Stad',
    perspectives: [
      { name: 'CAUSA', color: PERSPECTIVE_COLORS.CAUSA, progress: 80 },
      { name: 'NORM', color: PERSPECTIVE_COLORS.NORM, progress: 50 },
      { name: 'ACTOR', color: PERSPECTIVE_COLORS.ACTOR, progress: 60 },
      { name: 'VALUE', color: PERSPECTIVE_COLORS.VALUE, progress: 70 },
    ],
    activity: {
      comments: 27,
      members: 9,
      lastUpdate: '4 uur geleden',
    },
  },
  {
    id: '6',
    name: 'Energietransitie en leefbaarheid',
    description: 'Impact van duurzame energie-initiatieven op lokale gemeenschappen.',
    organization: 'Provincie Utrecht',
    perspectives: [
      { name: 'CAUSA', color: PERSPECTIVE_COLORS.CAUSA, progress: 55 },
      { name: 'NORM', color: PERSPECTIVE_COLORS.NORM, progress: 65 },
      { name: 'ACTOR', color: PERSPECTIVE_COLORS.ACTOR, progress: 75 },
      { name: 'VALUE', color: PERSPECTIVE_COLORS.VALUE, progress: 85 },
    ],
    activity: {
      comments: 22,
      members: 7,
      lastUpdate: '6 uur geleden',
    },
  },
];

const mockOrganizations = [
  { id: '1', name: 'Gemeente Amsterdam', themesCount: 12, color: '#3B82F6' },
  { id: '2', name: 'Ministerie VWS', themesCount: 8, color: '#10B981' },
  { id: '3', name: 'Provincie Utrecht', themesCount: 15, color: '#8B5CF6' },
  { id: '4', name: 'Onderwijsraad', themesCount: 6, color: '#F59E0B' },
];

const mockProjects = [
  { id: '1', name: 'Klimaattransitie 2030', organization: 'Gemeente Amsterdam', status: 'actief' },
  { id: '2', name: 'Ruimtelijke Ordening', organization: 'Provincie Utrecht', status: 'actief' },
  { id: '3', name: 'Duurzame Stad', organization: 'Gemeente Amsterdam', status: 'planning' },
  { id: '4', name: 'Zorg Innovatie', organization: 'Ministerie VWS', status: 'actief' },
  { id: '5', name: 'Onderwijsvernieuwing', organization: 'Onderwijsraad', status: 'afgerond' },
];

export default function App() {
  const [activeNav, setActiveNav] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(false);

  return (
    <div className="h-screen flex bg-background overflow-hidden">
      {/* Left Sidebar */}
      <Sidebar 
        activeItem={activeNav} 
        onItemClick={setActiveNav}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <DashboardHeader onMenuClick={() => setIsSidebarOpen(true)} />

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Theme Grid */}
          <div className="flex-1 overflow-y-auto p-4 lg:p-8">
            <div className="mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="mb-1">Mijn Thema's</h2>
                  <p className="text-sm text-muted-foreground">
                    {mockThemes.length} actieve thema's in {mockOrganizations.length} organisaties
                  </p>
                </div>
                {/* Mobile button to show organizations/projects */}
                <button
                  onClick={() => setIsRightPanelOpen(true)}
                  className="lg:hidden w-10 h-10 rounded-lg bg-accent flex items-center justify-center hover:bg-accent/80 transition-colors"
                >
                  <Layers className="w-5 h-5 text-foreground" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-4 lg:gap-6">
              {mockThemes.map((theme) => (
                <ThemeCard key={theme.id} theme={theme} />
              ))}
            </div>
          </div>

          {/* Right Panel */}
          <RightPanel 
            organizations={mockOrganizations} 
            projects={mockProjects}
            isOpen={isRightPanelOpen}
            onClose={() => setIsRightPanelOpen(false)}
          />
        </div>
      </div>
    </div>
  );
}