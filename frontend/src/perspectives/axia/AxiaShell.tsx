import { useState } from 'react';
import { ValueCanvas } from './ValueCanvas';
import { ValueChain } from './ValueChain';
import { ValueTensionView } from './ValueTensionView';

type AxiaTab = 'canvas' | 'keten' | 'spanningen';

interface AxiaShellProps {
    designSpaceId: string;
}

export function AxiaShell({ designSpaceId }: AxiaShellProps) {
    const [tab, setTab] = useState<AxiaTab>('canvas');

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center gap-1 px-4 py-2 border-b border-border bg-background shrink-0">
                <TabButton active={tab === 'canvas'} onClick={() => setTab('canvas')}>Waardeclaims</TabButton>
                <TabButton active={tab === 'keten'} onClick={() => setTab('keten')}>Waardeketen</TabButton>
                <TabButton active={tab === 'spanningen'} onClick={() => setTab('spanningen')}>Spanningen</TabButton>
            </div>
            <div className="flex-1 overflow-hidden">
                {tab === 'canvas' && <ValueCanvas designSpaceId={designSpaceId} />}
                {tab === 'keten' && <ValueChain designSpaceId={designSpaceId} />}
                {tab === 'spanningen' && <ValueTensionView designSpaceId={designSpaceId} />}
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
