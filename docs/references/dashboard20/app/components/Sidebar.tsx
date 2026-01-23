import { LayoutDashboard, Layers, Eye, Building2, FolderKanban, Settings } from 'lucide-react';

interface SidebarProps {
  activeItem: string;
  onItemClick: (item: string) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ activeItem, onItemClick, isOpen = true, onClose }: SidebarProps) {
  const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'themes', icon: Layers, label: "Thema's" },
    { id: 'perspectives', icon: Eye, label: 'Perspectieven' },
    { id: 'organizations', icon: Building2, label: 'Organisaties' },
    { id: 'projects', icon: FolderKanban, label: 'Projecten' },
    { id: 'settings', icon: Settings, label: 'Instellingen' },
  ];

  const handleItemClick = (item: string) => {
    onItemClick(item);
    if (onClose) {
      onClose();
    }
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:flex w-16 bg-white border-r border-border flex-col items-center py-6 gap-4">
        {/* Logo */}
        <div className="mb-4">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-white font-semibold text-sm">V</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-2 flex-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeItem === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => handleItemClick(item.id)}
                className={`
                  w-12 h-12 rounded-lg flex items-center justify-center
                  transition-all duration-200
                  ${isActive 
                    ? 'bg-primary text-white shadow-md' 
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  }
                `}
                title={item.label}
              >
                <Icon className="w-5 h-5" />
              </button>
            );
          })}
        </nav>
      </div>

      {/* Mobile drawer */}
      <div 
        className={`
          fixed top-0 left-0 bottom-0 w-72 bg-white z-50 
          transform transition-transform duration-300 ease-in-out
          lg:hidden flex flex-col
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Logo & Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-semibold text-sm">V</span>
            </div>
            <span className="font-semibold text-foreground">VALOR</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeItem === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => handleItemClick(item.id)}
                className={`
                  w-full flex items-center gap-3 px-4 py-3 rounded-lg mb-2
                  transition-all duration-200
                  ${isActive 
                    ? 'bg-primary text-white shadow-md' 
                    : 'text-foreground hover:bg-accent'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </>
  );
}