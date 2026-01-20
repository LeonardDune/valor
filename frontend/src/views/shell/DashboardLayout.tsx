import React from 'react';
import { PerspectiveShell } from '@/views/shell/PerspectiveShell';

export const DashboardLayout: React.FC = () => {
    return (
        <PerspectiveShell>
            <div className="p-8 h-full overflow-y-auto">
                <div className="max-w-4xl mx-auto space-y-8">
                    <header>
                        <h1 className="text-3xl font-bold text-text-primary">Collaborative Dashboard</h1>
                        <p className="text-text-secondary mt-2">
                            Overview of active proposals, tensions, and agent insights across the system.
                        </p>
                    </header>

                    {/* Placeholder for future widgets like "Global Health", "Recent Conflicts" */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="p-6 rounded-lg bg-panel border border-border-standard">
                            <h2 className="text-lg font-semibold mb-4">System Status</h2>
                            <div className="text-sm text-text-muted">No critical alerts detected.</div>
                        </div>
                        <div className="p-6 rounded-lg bg-panel border border-border-standard">
                            <h2 className="text-lg font-semibold mb-4">My Actions</h2>
                            <div className="text-sm text-text-muted">You have no pending reviews.</div>
                        </div>
                    </div>
                </div>
            </div>
        </PerspectiveShell>
    );
};
