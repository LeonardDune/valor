import { memo, type FunctionComponent, type MouseEvent } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Wrench, Cloud, Cpu, Target, HelpCircle, MessageSquare, type LucideProps } from 'lucide-react';

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { EpistemicStatus } from '../../types';

const epistemicStatusStyles: Record<EpistemicStatus, { borderLeft: string; dot: string; label: string }> = {
    Proposed:     { borderLeft: 'border-l-slate-400',  dot: 'bg-slate-400',   label: 'Voorgesteld' },
    Contested:    { borderLeft: 'border-l-orange-400', dot: 'bg-orange-400',  label: 'Betwist' },
    Accepted:     { borderLeft: 'border-l-green-500',  dot: 'bg-green-500',   label: 'Geaccepteerd' },
    Rejected:     { borderLeft: 'border-l-red-500',    dot: 'bg-red-500',     label: 'Afgewezen' },
    Reconsidered: { borderLeft: 'border-l-purple-500', dot: 'bg-purple-500',  label: 'Heroverwogen' },
};

// Use strict Lucide types
const iconMap: Record<string, FunctionComponent<LucideProps>> = {
    middel: Wrench,
    extern: Cloud,
    systeemelement: Cpu,
    criterium: Target,
    unknown: HelpCircle
};

// Map roles to Tailwind classes
const roleStyles: Record<string, { color: string, badge: string, icon: string }> = {
    middel: {
        color: 'text-blue-600',
        badge: 'bg-blue-50 text-blue-700 hover:bg-blue-50 border-blue-200',
        icon: 'text-blue-600'
    },
    extern: {
        color: 'text-slate-500',
        badge: 'bg-slate-50 text-slate-600 hover:bg-slate-50 border-slate-200',
        icon: 'text-slate-500'
    },
    systeemelement: {
        color: 'text-violet-600',
        badge: 'bg-violet-50 text-violet-700 hover:bg-violet-50 border-violet-200',
        icon: 'text-violet-600'
    },
    criterium: {
        color: 'text-amber-600',
        badge: 'bg-amber-50 text-amber-700 hover:bg-amber-50 border-amber-200',
        icon: 'text-amber-600'
    },
    unknown: {
        color: 'text-slate-400',
        badge: 'bg-slate-50 text-slate-500 hover:bg-slate-50 border-slate-200',
        icon: 'text-slate-400'
    }
};

const CARD_WIDTH = '140px';
const CARD_HEIGHT = '100px';

const CLDNode: FunctionComponent<NodeProps> = ({ id, data, selected }) => {
    const role = (data.role || 'systeemelement').toLowerCase() as keyof typeof iconMap;
    const isReadOnly = data.isReadOnly || false;
    const epistemicStatus = (data.epistemicStatus || 'Proposed') as EpistemicStatus;
    const isInCycle = data.isInCycle === true;

    const Icon = iconMap[role] || iconMap.unknown;
    const styles = roleStyles[role] || roleStyles.unknown;
    const statusStyle = epistemicStatusStyles[epistemicStatus] || epistemicStatusStyles.Proposed;

    return (
        <div
            className={cn(
                'group bg-white rounded-panel relative hover:shadow-lg transition-all',
                'flex flex-col border border-border-standard border-l-4',
                statusStyle.borderLeft,
                selected ? 'ring-2 ring-blue-500 border-transparent' : '',
                isInCycle ? 'ring-2 ring-amber-400' : ''
            )}
            style={{
                width: CARD_WIDTH,
                height: CARD_HEIGHT,
                // boxShadow: selected ? `0 4px 20px -5px ${color}40` : undefined, // Removed custom shadow for standard ring
            }}
        >
            {/* Connection Handles - 8 handles for bidirectional connections on all sides */}
            {/* Left */}
            {/* Left */}
            <Handle id="target-left" type="target" position={Position.Left} isConnectable={!isReadOnly} className={cn("w-2 h-2 !bg-slate-400 transition-opacity", !isReadOnly ? "opacity-0 group-hover:opacity-100" : "opacity-0")} />
            <Handle id="source-left" type="source" position={Position.Left} isConnectable={!isReadOnly} className={cn("w-2 h-2 !bg-slate-400 transition-opacity", !isReadOnly ? "opacity-0 group-hover:opacity-100" : "opacity-0")} />

            {/* Right */}
            <Handle id="target-right" type="target" position={Position.Right} isConnectable={!isReadOnly} className={cn("w-2 h-2 !bg-slate-400 transition-opacity", !isReadOnly ? "opacity-0 group-hover:opacity-100" : "opacity-0")} />
            <Handle id="source-right" type="source" position={Position.Right} isConnectable={!isReadOnly} className={cn("w-2 h-2 !bg-slate-400 transition-opacity", !isReadOnly ? "opacity-0 group-hover:opacity-100" : "opacity-0")} />

            {/* Top */}
            <Handle id="target-top" type="target" position={Position.Top} isConnectable={!isReadOnly} className={cn("w-2 h-2 !bg-slate-400 transition-opacity", !isReadOnly ? "opacity-0 group-hover:opacity-100" : "opacity-0")} />
            <Handle id="source-top" type="source" position={Position.Top} isConnectable={!isReadOnly} className={cn("w-2 h-2 !bg-slate-400 transition-opacity", !isReadOnly ? "opacity-0 group-hover:opacity-100" : "opacity-0")} />

            {/* Bottom */}
            <Handle id="target-bottom" type="target" position={Position.Bottom} isConnectable={!isReadOnly} className={cn("w-2 h-2 !bg-slate-400 transition-opacity", !isReadOnly ? "opacity-0 group-hover:opacity-100" : "opacity-0")} />
            <Handle id="source-bottom" type="source" position={Position.Bottom} isConnectable={!isReadOnly} className={cn("w-2 h-2 !bg-slate-400 transition-opacity", !isReadOnly ? "opacity-0 group-hover:opacity-100" : "opacity-0")} />

            {/* Header / Tag */}
            <div className="relative flex justify-center pt-2 px-2">
                <Badge variant="outline" className={`text-[10px] px-2 py-0 h-5 border shadow-none ${styles.badge}`}>
                    {role.charAt(0).toUpperCase() + role.slice(1)}
                </Badge>

                {/* Thread Indicator */}
                {data.threadCount !== undefined && (
                    <Button
                        variant="ghost"
                        size="sm"
                        className={cn(
                            "absolute right-1 top-1 h-6 gap-1 px-1.5 rounded-full text-[10px] font-medium transition-colors hover:bg-muted",
                            data.threadCount > 0 ? "text-primary bg-primary/10" : "text-muted-foreground opacity-0 group-hover:opacity-100"
                        )}
                        onClick={(e: MouseEvent) => {
                            e.stopPropagation();
                            // Prefer version_id to attach thread to the specific version, fallback to base id (identity)
                            data.onOpenThread?.(data.version_id || id, data.label, { x: e.clientX, y: e.clientY });
                        }}
                    >
                        <MessageSquare className="w-3 h-3" />
                        {data.threadCount > 0 && <span>{data.threadCount}</span>}
                    </Button>
                )}
            </div>

            {/* Body / Title */}
            <div className="flex-1 flex items-center justify-center p-2 text-center">
                <span className="text-xs font-bold text-slate-900 line-clamp-3 leading-tight">
                    {data.label}
                </span>
            </div>

            {/* Footer: rol-icoon + status-badge */}
            <div className="absolute bottom-2 right-2 flex items-center gap-1">
                <span
                    className={cn('w-2 h-2 rounded-full', statusStyle.dot)}
                    title={statusStyle.label}
                />
                <span className={cn('opacity-50', styles.icon)}>
                    <Icon size={16} />
                </span>
            </div>
        </div>
    );
};

export default memo(CLDNode);
