import { Search, Bell, User, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface DashboardHeaderProps {
    onMenuClick?: () => void;
    onContextPanelClick?: () => void;
}

export function DashboardHeader({ onMenuClick, onContextPanelClick }: DashboardHeaderProps) {
    return (
        <header className="h-16 bg-background border-b border-border px-4 lg:px-8 flex items-center justify-between z-10 sticky top-0">
            <div className="flex items-center gap-4">
                {/* Mobile menu button */}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={onMenuClick}
                    className="lg:hidden"
                >
                    <Menu className="w-5 h-5 text-foreground" />
                </Button>

                <h1 className="font-semibold text-lg text-foreground">VALOR</h1>
            </div>

            <div className="flex items-center gap-2 lg:gap-4">
                {/* Search - hidden on mobile, shown on desktop */}
                <div className="relative hidden md:block w-80">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                        type="text"
                        placeholder="Zoek thema's, projecten..."
                        className="pl-10 bg-muted/50 border-transparent focus:bg-background transition-all"
                    />
                </div>

                {/* Mobile search button */}
                <Button variant="ghost" size="icon" className="md:hidden">
                    <Search className="w-5 h-5 text-muted-foreground" />
                </Button>

                {/* Notifications */}
                <Button variant="ghost" size="icon" className="relative">
                    <Bell className="w-5 h-5 text-muted-foreground" />
                    <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-destructive rounded-full"></span>
                </Button>

                {/* Context Panel Toggle (Mobile) - Logic moved here or in layout */}
                <Button
                    variant="outline"
                    size="sm"
                    className="hidden lg:flex"
                    onClick={onContextPanelClick}
                >
                    Context
                </Button>

                {/* User */}
                <Button size="icon" className="rounded-full bg-primary text-primary-foreground">
                    <User className="w-5 h-5" />
                </Button>
            </div>
        </header>
    );
}
