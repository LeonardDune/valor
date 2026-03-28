import React from 'react';
import { useDesignSpace } from '../../context/DesignSpaceContext';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Target } from 'lucide-react';

export const ThemeContextPanel: React.FC = () => {
    const {
        activeVersion,
        isReadOnly,
        activeVotingSession
    } = useDesignSpace();

    if (!activeVersion) return null;

    return (
        <div className="flex items-center gap-2">
            <Button variant={isReadOnly ? "secondary" : "outline"} size="sm" className="gap-2 border-dashed" disabled>
                {activeVotingSession ? (
                    <Target className="h-4 w-4 text-orange-500 animate-pulse" />
                ) : (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                )}
                <span className="hidden md:inline">
                    {activeVotingSession ? `Stemming: ${activeVersion.name}` : `Actief: ${activeVersion.name}`}
                </span>
            </Button>
        </div>
    );
};
