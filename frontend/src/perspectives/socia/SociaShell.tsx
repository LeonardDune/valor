import { useState, useCallback, useEffect } from 'react';
import { StakeholderMap } from './views/StakeholderMap';
import { StakeholderClaimsPanel } from './views/StakeholderClaimsPanel';
import { StakeholderGroupPanel } from './views/StakeholderGroupPanel';
import { api, type StakeholderActor } from '@/services/api';

type SociaTab = 'kaart' | 'claims' | 'groepen';

interface SociaShellProps {
    dsId: string;
}

export function SociaShell({ dsId }: SociaShellProps) {
    const [tab, setTab] = useState<SociaTab>('kaart');
    const [actors, setActors] = useState<StakeholderActor[]>([]);

    const loadActors = useCallback(async () => {
        try {
            const map = await api.getStakeholderMap(dsId);
            setActors(map.actors);
        } catch {
            // niet kritiek — panel degradeert graceful
        }
    }, [dsId]);

    useEffect(() => { loadActors(); }, [loadActors]);

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center gap-1 px-4 py-2 border-b border-border bg-background shrink-0">
                <TabButton active={tab === 'kaart'} onClick={() => setTab('kaart')}>Stakeholderkaart</TabButton>
                <TabButton active={tab === 'claims'} onClick={() => setTab('claims')}>Claims</TabButton>
                <TabButton active={tab === 'groepen'} onClick={() => setTab('groepen')}>Groepen</TabButton>
            </div>
            <div className="flex-1 overflow-auto">
                {tab === 'kaart' && <StakeholderMap dsId={dsId} />}
                {tab === 'claims' && <StakeholderClaimsPanel dsId={dsId} actors={actors} />}
                {tab === 'groepen' && <StakeholderGroupPanel dsId={dsId} />}
            </div>
        </div>
    );
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                active
                    ? 'bg-primary text-primary-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            }`}
        >
            {children}
        </button>
    );
}
