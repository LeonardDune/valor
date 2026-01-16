import React, { useState } from 'react';
import {
    ChevronsLeft, ChevronsRight, Home,
    Settings, LogOut, ChevronRight, Layout, Folder
} from 'lucide-react';
import { useOrganization } from '../../context/OrganizationContext';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
    view: string;
    setView: (view: any) => void;
    selectedProjectName: string;
    selectedThemeName: string;
    onNavigateProject: () => void;
    onNavigateTheme: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
    view, setView, selectedProjectName, selectedThemeName,
    onNavigateProject, onNavigateTheme
}) => {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const { activeOrganization, organizations, switchOrganization } = useOrganization();
    const { signOut, user } = useAuth();

    return (
        <div
            className={`
        h-screen bg-slate-900 text-slate-300 flex flex-col transition-all duration-300 z-panel relative
        ${isCollapsed ? 'w-16' : 'w-64'}
      `}
        >
            {/* Header / Org Switcher */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                {!isCollapsed && (
                    <div className="font-bold text-white text-xl tracking-tight">VALOR</div>
                )}
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                >
                    {isCollapsed ? <ChevronsRight size={18} /> : <ChevronsLeft size={18} />}
                </button>
            </div>

            {/* Org Selector (Collapsed = Icon, Expanded = Dropdown) */}
            <div className="p-4 border-b border-slate-800">
                {!isCollapsed ? (
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase">Organisatie</label>
                        <select
                            value={activeOrganization?.id || ''}
                            onChange={(e) => switchOrganization(e.target.value)}
                            className="w-full bg-slate-800 border-none rounded-md px-3 py-2 text-sm text-white focus:ring-1 focus:ring-indigo-500 outline-none cursor-pointer hover:bg-slate-700 transition"
                        >
                            {organizations.map(org => (
                                <option key={org.id} value={org.id}>{org.name}</option>
                            ))}
                        </select>
                    </div>
                ) : (
                    <div className="flex justify-center" title={activeOrganization?.name}>
                        <div className="w-8 h-8 rounded bg-indigo-600 flex items-center justify-center text-white font-bold text-xs">
                            {activeOrganization?.name.substring(0, 2).toUpperCase()}
                        </div>
                    </div>
                )}
            </div>

            {/* Navigation Links */}
            <div className="flex-1 overflow-y-auto py-4 space-y-1 px-2">

                <NavItem
                    icon={<Home size={20} />}
                    label="Projecten"
                    isActive={view === 'PROJECT_LIST'}
                    onClick={() => setView('PROJECT_LIST')}
                    isCollapsed={isCollapsed}
                />

                {selectedProjectName && (
                    <div className="my-2 border-l border-slate-700 ml-4 pl-3 space-y-1">
                        {!isCollapsed && <div className="text-xs text-slate-500 mb-1">Actief Project</div>}
                        <NavItem
                            icon={<Folder size={18} />}
                            label={selectedProjectName}
                            isActive={view === 'THEME_LIST'}
                            onClick={onNavigateProject}
                            isCollapsed={isCollapsed}
                            subItem
                        />
                    </div>
                )}

                {selectedThemeName && view === 'WORKSPACE' && (
                    <div className="my-2 border-l-2 border-indigo-500 ml-4 pl-3 space-y-1">
                        {!isCollapsed && <div className="text-xs text-indigo-400 mb-1">Actief Thema</div>}
                        <NavItem
                            icon={<Layout size={18} />}
                            label={selectedThemeName}
                            isActive={true}
                            onClick={onNavigateTheme}
                            isCollapsed={isCollapsed}
                            subItem
                        />
                    </div>
                )}

            </div>

            {/* Footer / User */}
            <div className="p-4 border-t border-slate-800 space-y-2">
                <NavItem
                    icon={<Settings size={20} />}
                    label="Instellingen"
                    isActive={view === 'SETTINGS'}
                    onClick={() => setView('SETTINGS')}
                    isCollapsed={isCollapsed}
                />
                <button
                    onClick={() => signOut()}
                    className={`
                w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors
                text-red-400 hover:bg-slate-800 hover:text-red-300
                ${isCollapsed ? 'justify-center' : ''}
            `}
                    title="Uitloggen"
                >
                    <LogOut size={20} />
                    {!isCollapsed && <span>Uitloggen</span>}
                </button>
            </div>

            {!isCollapsed && user && (
                <div className="px-6 pb-4 text-xs text-slate-600 text-center">
                    Ingelogd als <br /> <span className="text-slate-500">{user.email}</span>
                </div>
            )}
        </div>
    );
};

const NavItem = ({ icon, label, isActive, onClick, isCollapsed, subItem }: any) => (
    <button
        onClick={onClick}
        className={`
            w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all
            ${isActive
                ? 'bg-indigo-600/10 text-indigo-400'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}
            ${isCollapsed ? 'justify-center' : ''}
            ${subItem ? 'text-sm' : ''}
        `}
        title={label}
    >
        {icon}
        {!isCollapsed && <span className="truncate">{label}</span>}
        {!isCollapsed && isActive && !subItem && <ChevronRight size={14} className="ml-auto opacity-50" />}
    </button>
);
