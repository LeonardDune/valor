import React from 'react';
import { History } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { type PhaseSnapshot } from '@/services/api';

interface PhaseSelectorProps {
    snapshots: PhaseSnapshot[];
    activePhaseId: string | null;
    onSelect: (phaseId: string | null) => void;
}

export const PhaseSelector: React.FC<PhaseSelectorProps> = ({ snapshots, activePhaseId, onSelect }) => {
    if (snapshots.length === 0) return null;

    return (
        <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-muted-foreground shrink-0" />
            <Select
                value={activePhaseId ?? 'current'}
                onValueChange={(v) => onSelect(v === 'current' ? null : v)}
            >
                <SelectTrigger className="w-52 h-8 text-sm">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="current">
                        <span className="font-medium">Huidige fase</span>
                    </SelectItem>
                    {snapshots.map((s, i) => (
                        <SelectItem key={s.session_id} value={s.session_id}>
                            <div className="flex items-center gap-1.5">
                                <span>Fase {i + 1}</span>
                                <span className="text-xs text-muted-foreground">
                                    {new Date(s.created_at).toLocaleDateString('nl-NL')}
                                </span>
                                <Badge variant="secondary" className="text-xs px-1 py-0">
                                    {s.accepted_count}✓
                                </Badge>
                                <Badge variant="destructive" className="text-xs px-1 py-0">
                                    {s.rejected_count}✗
                                </Badge>
                            </div>
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
            {activePhaseId && (
                <Badge variant="outline" className="text-xs text-amber-600 border-amber-400 shrink-0">
                    Alleen-lezen
                </Badge>
            )}
        </div>
    );
};
