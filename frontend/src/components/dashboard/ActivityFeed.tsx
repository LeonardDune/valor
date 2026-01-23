import React, { useEffect, useState } from 'react';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Panel } from '@/design-system/primitives/Panel';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api, type Proposal } from '@/services/api';

// Proposal Type imported from api

export const ActivityFeed: React.FC = () => {
    const [proposals, setProposals] = useState<Proposal[]>([]);
    const [loading, setLoading] = useState(true);

    // Simple Polling for now
    useEffect(() => {
        const fetchProposals = async () => {
            try {
                // Use centralized API service
                const data = await api.getProposals();
                setProposals(data);
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
        return <div className="p-4 text-muted-foreground text-sm">Activiteiten laden...</div>;
    }

    return (
        <div className="flex flex-col h-full">
            <h3 className="text-sm font-semibold text-primary px-4 py-2 border-b border-border">
                Activiteiten
            </h3>
            <ScrollArea className="flex-1 p-4">
                <div className="space-y-3">
                    {proposals.length === 0 ? (
                        <div className="text-sm text-muted-foreground">Geen recente activiteiten.</div>
                    ) : (
                        proposals.map((p) => (
                            <Panel key={p.id} padding="sm" className="space-y-2 hover:bg-muted/50 transition-colors cursor-pointer">
                                <div className="flex justify-between items-start">
                                    <span className="font-medium text-foreground text-sm truncate pr-2">{p.title}</span>
                                    <StatusBadge status={p.status} showLabel={false} />
                                </div>
                                {p.description && (
                                    <p className="text-xs text-muted-foreground line-clamp-2">{p.description}</p>
                                )}
                                <div className="flex justify-between items-center text-[10px] text-muted-foreground">
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
