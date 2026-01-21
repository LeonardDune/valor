import React, { useEffect, useState } from 'react';
import axios from 'axios';
import type { LifecycleStatus } from '@/components/ui/StatusBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Panel } from '@/design-system/primitives/Panel';
import { ScrollArea } from '@/components/ui/scroll-area';

// Define Proposal Type locally for now or import from share types
interface Proposal {
    id: string;
    title: string;
    description?: string;
    status: LifecycleStatus;
    author_id: string;
    created_at: string;
}

export const ActivityFeed: React.FC = () => {
    const [proposals, setProposals] = useState<Proposal[]>([]);
    const [loading, setLoading] = useState(true);

    // Simple Polling for now
    useEffect(() => {
        const fetchProposals = async () => {
            try {
                // Hardcoded API URL for MVP dev
                const res = await axios.get('http://localhost:8000/proposals/');
                setProposals(res.data);
            } catch (error) {
                console.error("Failed to fetch proposals", error);
            } finally {
                setLoading(false);
            }
        };

        fetchProposals();
        const interval = setInterval(fetchProposals, 10000); // 10s poll
        return () => clearInterval(interval);
    }, []);

    if (loading && proposals.length === 0) {
        return <div className="p-4 text-text-muted">Loading feed...</div>;
    }

    return (
        <div className="flex flex-col h-full">
            <h3 className="text-sm font-semibold text-text-primary px-4 py-2 border-b border-border-standard">
                Activity Feed
            </h3>
            <ScrollArea className="flex-1 p-4">
                <div className="space-y-3">
                    {proposals.length === 0 ? (
                        <div className="text-sm text-text-muted">No recent activity.</div>
                    ) : (
                        proposals.map((p) => (
                            <Panel key={p.id} padding="sm" className="space-y-2 hover:bg-white/5 transition-colors cursor-pointer">
                                <div className="flex justify-between items-start">
                                    <span className="font-medium text-text-primary text-sm truncate pr-2">{p.title}</span>
                                    <StatusBadge status={p.status} showLabel={false} />
                                </div>
                                {p.description && (
                                    <p className="text-xs text-text-secondary line-clamp-2">{p.description}</p>
                                )}
                                <div className="flex justify-between items-center text-[10px] text-text-muted">
                                    <span>{p.author_id}</span>
                                    <span>{new Date(p.created_at).toLocaleTimeString()}</span>
                                </div>
                            </Panel>
                        ))
                    )}
                </div>
            </ScrollArea>
        </div>
    );
};
