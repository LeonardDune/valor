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
import { History, Clock, CheckCircle2, GitBranch } from 'lucide-react';
import { type ThemeVersion } from '../../services/api';

// --- Tree Logic ---
type TreeNode = ThemeVersion & { children: TreeNode[] };

const buildTree = (allVersions: ThemeVersion[]): TreeNode[] => {
    const nodeMap = new Map<string, TreeNode>();
    const roots: TreeNode[] = [];

    // 1. Initialize map
    allVersions.forEach(v => {
        nodeMap.set(v.id, { ...v, children: [] });
    });

    // 2. Build relationships
    allVersions.forEach(v => {
        const node = nodeMap.get(v.id)!;
        if (v.derived_from_id && nodeMap.has(v.derived_from_id)) {
            nodeMap.get(v.derived_from_id)!.children.push(node);
        } else {
            roots.push(node);
        }
    });

    // 3. Sort by created_at desc (newest first)
    const sortNodes = (nodes: TreeNode[]) => {
        nodes.sort((a, b) => {
            const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
            const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
            return dateB - dateA;
        });
        nodes.forEach(n => sortNodes(n.children));
    };

    sortNodes(roots);
    return roots;
};

export const ThemeContextPanel: React.FC = () => {
    const {
        activeVersion,
        currentViewedVersion,
        versions,
        switchVersion,
        isReadOnly
    } = useTheme();

    if (!activeVersion || !currentViewedVersion) return null;

    const tree = buildTree(versions);

    const renderNode = (node: TreeNode, depth: number = 0) => {
        const isCurrent = node.id === currentViewedVersion.id;
        const isActive = node.id === activeVersion.id;

        return (
            <React.Fragment key={node.id}>
                <DropdownMenuItem
                    onClick={() => switchVersion(node.id)}
                    className="cursor-pointer"
                    style={{ marginLeft: `${depth * 16}px` }}
                >
                    {depth > 0 ? (
                        <GitBranch className="mr-2 h-4 w-4 text-muted-foreground rotate-90" />
                    ) : (
                        <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
                    )}

                    <div className="flex flex-col">
                        <span className="font-medium flex items-center gap-2">
                            {node.name}
                            {isActive && <Badge variant="outline" className="text-[10px] h-4 px-1 py-0 text-green-600 border-green-200">Actief</Badge>}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                            {node.valid_from ? new Date(node.valid_from).toLocaleDateString("nl-NL") : 'Initieel'}
                        </span>
                    </div>
                    {isCurrent && <CheckCircle2 className="ml-auto h-3 w-3 text-primary" />}
                </DropdownMenuItem>
                {node.children.map(child => renderNode(child, depth + 1))}
            </React.Fragment>
        );
    };

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
                <DropdownMenuContent align="end" className="w-80">
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
                        {currentViewedVersion.derived_from_id && (
                            <div className="flex justify-between mt-1">
                                <span>Afgeleid van:</span>
                                <span className="font-mono text-[10px]">{versions.find(v => v.id === currentViewedVersion.derived_from_id)?.name || 'Onbekend'}</span>
                            </div>
                        )}
                    </div>

                    <DropdownMenuSeparator />
                    <DropdownMenuLabel>Lineage & Geschiedenis</DropdownMenuLabel>

                    <div className="max-h-[400px] overflow-y-auto">
                        {tree.length === 0 ? (
                            <div className="px-2 py-4 text-center text-xs text-muted-foreground">
                                Geen geschiedenis beschikbaar.
                            </div>
                        ) : (
                            tree.map(node => renderNode(node))
                        )}
                    </div>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
};
