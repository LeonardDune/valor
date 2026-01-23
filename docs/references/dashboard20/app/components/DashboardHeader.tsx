import { Search, Bell, User, Menu } from 'lucide-react';

interface DashboardHeaderProps {
  onMenuClick?: () => void;
}

export function DashboardHeader({ onMenuClick }: DashboardHeaderProps) {
  return (
    <header className="h-16 bg-white border-b border-border px-4 lg:px-8 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <button 
          onClick={onMenuClick}
          className="lg:hidden w-10 h-10 rounded-lg flex items-center justify-center hover:bg-accent transition-colors"
        >
          <Menu className="w-5 h-5 text-foreground" />
        </button>
        
        <h1 className="font-semibold text-foreground">VALOR Dashboard</h1>
      </div>

      <div className="flex items-center gap-2 lg:gap-4">
        {/* Search - hidden on mobile, shown on desktop */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Zoek thema's, projecten..."
            className="pl-10 pr-4 py-2 w-60 lg:w-80 bg-accent rounded-lg border border-transparent focus:border-primary/20 focus:bg-white transition-all outline-none"
          />
        </div>

        {/* Mobile search button */}
        <button className="md:hidden w-10 h-10 rounded-lg flex items-center justify-center hover:bg-accent transition-colors">
          <Search className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* Notifications */}
        <button className="w-10 h-10 rounded-lg flex items-center justify-center hover:bg-accent transition-colors relative">
          <Bell className="w-5 h-5 text-muted-foreground" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-destructive rounded-full"></span>
        </button>

        {/* User */}
        <button className="w-10 h-10 rounded-lg bg-primary text-white flex items-center justify-center hover:bg-primary/90 transition-colors">
          <User className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}