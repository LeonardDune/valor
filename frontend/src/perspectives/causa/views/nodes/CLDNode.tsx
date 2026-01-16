import type { FunctionComponent } from 'react';
import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Wrench, Cloud, Cpu, Target, HelpCircle, type LucideProps } from 'lucide-react';

// Use strict Lucide types
const iconMap: Record<string, FunctionComponent<LucideProps>> = {
    middel: Wrench,
    extern: Cloud,
    systeemelement: Cpu,
    criterium: Target,
    unknown: HelpCircle
};

const iconColors: Record<string, string> = {
    middel: '#3b82f6',
    extern: '#64748b',
    systeemelement: '#8b5cf6',
    criterium: '#f59e0b',
    unknown: '#94a3b8'
};

const CARD_WIDTH = '140px';
const CARD_HEIGHT = '100px';

const CLDNode: FunctionComponent<NodeProps> = ({ data, selected }) => {
    // Robust access to type from data.description? (Actually stored in 'type' field from mapper)
    // The mapper puts 'system' or 'factor' in type. BUT we need the SUBTYPE (middel, extern, etc).
    // The previous analysis showed FactorNode uses `data.type`. 
    // BUT my mapper currently puts 'system' vs 'factor' in `node.type`.
    // Wait, let's check mappers.ts again.
    // mappers.ts: type: factor.type === 'systeemelement' ? 'system' : 'factor'
    // WRONG. It loses the distinction between 'middel', 'criterium', etc.
    // I need to fix mappers.ts to pass the ORIGINAL type in data.subtype or similar.

    // For now, I will use `data.type` if it matches, otherwise fallback.
    // But `CLDView` passes `data: { label: cn.label, type: cn.type, description: cn.description }`.
    // And `cn.type` is restricted to 'factor' | 'system' by `CausalNode` interface.

    // ACTION: I must first update `CausalNode` interface and `mapper` to carry the 'role' (middel/extern...).

    // Interim Implementation (will refine after data fix):
    const role = (data.role || 'systeemelement').toLowerCase() as keyof typeof iconMap;
    // Note: I will update mapper to pass `role`. 

    const Icon = iconMap[role] || iconMap.unknown;
    const color = iconColors[role] || iconColors.unknown;

    return (
        <div
            className={`
                group bg-panel rounded-panel relative hover:shadow-lg transition-all
                flex flex-col border border-border-standard
                ${selected ? 'ring-2 ring-blue-500 border-transparent' : ''}
            `}
            style={{
                width: CARD_WIDTH,
                height: CARD_HEIGHT,
                boxShadow: selected ? `0 4px 20px -5px ${color}40` : undefined,
            }}
        >
            {/* Connection Handles - 8 handles for bidirectional connections on all sides */}
            {/* Left */}
            <Handle id="target-left" type="target" position={Position.Left} className="w-2 h-2 !bg-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            <Handle id="source-left" type="source" position={Position.Left} className="w-2 h-2 !bg-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* Right */}
            <Handle id="target-right" type="target" position={Position.Right} className="w-2 h-2 !bg-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            <Handle id="source-right" type="source" position={Position.Right} className="w-2 h-2 !bg-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* Top */}
            <Handle id="target-top" type="target" position={Position.Top} className="w-2 h-2 !bg-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            <Handle id="source-top" type="source" position={Position.Top} className="w-2 h-2 !bg-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* Bottom */}
            <Handle id="target-bottom" type="target" position={Position.Bottom} className="w-2 h-2 !bg-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            <Handle id="source-bottom" type="source" position={Position.Bottom} className="w-2 h-2 !bg-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* Header / Tag */}
            <div className="pt-2 px-2">
                <div
                    className="text-[10px] font-semibold px-2 py-0.5 rounded-md w-fit mx-auto"
                    style={{ backgroundColor: `${color}15`, color: color }}
                >
                    {role.charAt(0).toUpperCase() + role.slice(1)}
                </div>
            </div>

            {/* Body / Title */}
            <div className="flex-1 flex items-center justify-center p-2 text-center">
                <span className="text-xs font-bold text-slate-900 line-clamp-3 leading-tight">
                    {data.label}
                </span>
            </div>

            {/* Footer Icon */}
            <div className="absolute bottom-2 right-2 opacity-50">
                <Icon size={16} color={color} />
            </div>
        </div>
    );
};

export default memo(CLDNode);
