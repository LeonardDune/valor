import React from 'react';
import { useTheme } from '../../context/ThemeContext';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from '@/components/ui/badge';
import { History, Clock, CheckCircle2 } from 'lucide-react';

export const ThemeContextPanel: React.FC = () => {
    const {
        activeVersion,
        currentViewedVersion,
        versions,
        switchVersion,
        isReadOnly
    } = useTheme();

    if (!activeVersion || !currentViewedVersion) return null;

    // Filter out the active version from the history list to avoid duplication if it's in the list
    const historicalVersions = versions.filter(v => v.id !== activeVersion.id);

    return (
        <div className="flex items-center gap-2">
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant={isReadOnly ? "secondary" : "outline"} size="sm" className="gap-2 border-dashed">
                        {isReadOnly ? <History className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4 text-green-500" />}
                        <span className="hidden md:inline">
                            {isReadOnly ? `Versie: ${currentViewedVersion.name}` : `Actief: ${activeVersion.name}`}
                        </span>
                        {isReadOnly && <Badge variant="secondary" className="text-[10px] h-5 px-1">ALLEEN-LEZEN</Badge>}
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-64">
                    <DropdownMenuLabel>Huidige Context</DropdownMenuLabel>
                    <div className="px-2 py-1.5 text-xs text-muted-foreground bg-muted/50 rounded-md mx-1 mb-2">
                        <div className="flex justify-between">
                            <span>Status:</span>
                            <span className={isReadOnly ? "text-orange-500 font-medium" : "text-green-500 font-medium"}>
                                {isReadOnly ? "Historisch (Alleen-lezen)" : "Actief (Bewerkbaar)"}
                            </span>
                        </div>
                        <div className="flex justify-between mt-1">
                            <span>Geldig Vanaf:</span>
                            <span>{currentViewedVersion.valid_from ? new Date(currentViewedVersion.valid_from).toLocaleDateString("nl-NL") : 'Begin'}</span>
                        </div>
                    </div>

                    <DropdownMenuSeparator />

                    <DropdownMenuItem onClick={() => switchVersion(activeVersion.id)} className="cursor-pointer">
                        <CheckCircle2 className="mr-2 h-4 w-4 text-green-500" />
                        <div className="flex flex-col">
                            <span className="font-medium">Actieve Versie</span>
                            <span className="text-[10px] text-muted-foreground">Huidige Staat</span>
                        </div>
                        {activeVersion.id === currentViewedVersion.id && <CheckCircle2 className="ml-auto h-3 w-3" />}
                    </DropdownMenuItem>

                    <DropdownMenuSeparator />
                    <DropdownMenuLabel>Versiegeschiedenis</DropdownMenuLabel>

                    <div className="max-h-[300px] overflow-y-auto">
                        {historicalVersions.length === 0 ? (
                            <div className="px-2 py-4 text-center text-xs text-muted-foreground">
                                Geen geschiedenis beschikbaar.
                            </div>
                        ) : (
                            historicalVersions.map((version) => (
                                <DropdownMenuItem
                                    key={version.id}
                                    onClick={() => switchVersion(version.id)}
                                    className="cursor-pointer"
                                >
                                    <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
                                    <div className="flex flex-col">
                                        <span className="font-medium">{version.name}</span>
                                        <span className="text-[10px] text-muted-foreground">
                                            {version.valid_from ? new Date(version.valid_from).toLocaleDateString("nl-NL") : 'Initieel'}
                                        </span>
                                    </div>
                                    {version.id === currentViewedVersion.id && <CheckCircle2 className="ml-auto h-3 w-3" />}
                                </DropdownMenuItem>
                            ))
                        )}
                    </div>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
};
