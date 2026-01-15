import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Wrench, Cloud, Cpu, Target, HelpCircle } from 'lucide-react';

const iconMap = {
    middel: Wrench,
    extern: Cloud,
    systeemelement: Cpu,
    criterium: Target,
    unknown: HelpCircle
};

const iconColors = {
    middel: '#3b82f6',
    extern: '#64748b',
    systeemelement: '#8b5cf6',
    criterium: '#f59e0b',
    unknown: '#94a3b8'
};

const CARD_WIDTH = '140px';
const CARD_HEIGHT = '100px';

const FactorNode: React.FC<NodeProps> = ({ data, selected }) => {
    const type = (data.type || 'systeemelement').toLowerCase() as keyof typeof iconMap;
    const Icon = iconMap[type] || iconMap.unknown;
    const color = iconColors[type] || iconColors.unknown;

    return (
        <div
            className={`
                group bg-white rounded-xl relative hover:shadow-lg transition-all
                flex flex-col
            `}
            style={{
                width: CARD_WIDTH,
                height: CARD_HEIGHT,
                boxShadow: selected ? `0 4px 20px -5px ${color}40` : '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                border: `2px solid ${selected ? '#2563eb' : 'transparent'}`,
                outline: selected ? 'none' : '1px solid #e2e8f0',
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
                    {type.charAt(0).toUpperCase() + type.slice(1)}
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

export default memo(FactorNode);
