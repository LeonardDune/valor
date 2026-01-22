import { Building2, FolderKanban, ChevronRight, X } from 'lucide-react';

interface Organization {
  id: string;
  name: string;
  themesCount: number;
  color: string;
}

interface Project {
  id: string;
  name: string;
  organization: string;
  status: string;
}

interface RightPanelProps {
  organizations: Organization[];
  projects: Project[];
  isOpen?: boolean;
  onClose?: () => void;
}

export function RightPanel({ organizations, projects, isOpen = true, onClose }: RightPanelProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Panel */}
      <div className={`
        fixed lg:static top-0 right-0 bottom-0 w-80 bg-white border-l border-border 
        p-6 overflow-y-auto z-50
        transform transition-transform duration-300 ease-in-out lg:transform-none
        ${isOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
      `}>
        {/* Mobile close button */}
        <button
          onClick={onClose}
          className="lg:hidden absolute top-4 right-4 w-8 h-8 rounded-lg flex items-center justify-center hover:bg-accent transition-colors"
        >
          <X className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* Organizations Section */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="w-5 h-5 text-muted-foreground" />
            <h2 className="font-semibold text-foreground">Mijn Organisaties</h2>
          </div>
          <div className="space-y-2">
            {organizations.map((org) => (
              <button
                key={org.id}
                className="w-full p-3 rounded-lg border border-border hover:border-primary/20 hover:bg-accent/50 transition-all text-left group"
              >
                <div className="flex items-center gap-3">
                  <div 
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-medium"
                    style={{ backgroundColor: org.color }}
                  >
                    {org.name.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-foreground truncate">{org.name}</div>
                    <div className="text-xs text-muted-foreground">{org.themesCount} thema's</div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Projects Section */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <FolderKanban className="w-5 h-5 text-muted-foreground" />
            <h2 className="font-semibold text-foreground">Mijn Projecten</h2>
          </div>
          <div className="space-y-2">
            {projects.map((project) => (
              <button
                key={project.id}
                className="w-full p-3 rounded-lg border border-border hover:border-primary/20 hover:bg-accent/50 transition-all text-left group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="font-medium text-sm text-foreground truncate">{project.name}</div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="text-xs text-muted-foreground mb-2">{project.organization}</div>
                <div className="flex items-center gap-2">
                  <div className={`
                    px-2 py-0.5 rounded text-xs
                    ${project.status === 'actief' ? 'bg-green-100 text-green-700' : ''}
                    ${project.status === 'planning' ? 'bg-blue-100 text-blue-700' : ''}
                    ${project.status === 'afgerond' ? 'bg-gray-100 text-gray-700' : ''}
                  `}>
                    {project.status}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}