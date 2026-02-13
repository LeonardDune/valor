import React, { useState } from 'react';
import { useManagedSessions } from '@/hooks/queries/useSessions';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Shield, ArrowRight, Users, Activity } from 'lucide-react';
import { ModeratorDashboard } from '../deliberation/ModeratorDashboard';
import { Dialog, DialogContent } from '@/components/ui/dialog';

export const ModeratorSection: React.FC = () => {
    const { data: sessions, isLoading } = useManagedSessions();
    const [selectedSession, setSelectedSession] = useState<any>(null);

    if (isLoading) return (
        <div className="mb-12 space-y-4">
            <div className="h-6 w-48 bg-muted animate-pulse rounded" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="h-32 bg-muted animate-pulse rounded-xl" />
                <div className="h-32 bg-muted animate-pulse rounded-xl" />
            </div>
        </div>
    );

    if (!sessions || sessions.length === 0) return null;

    return (
        <div className="mb-12 space-y-6">
            <div className="flex items-center gap-2 text-primary">
                <Shield className="h-5 w-5" />
                <span className="text-sm font-semibold uppercase tracking-wider">Moderator Overzicht</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sessions.map((session: any) => (
                    <Card
                        key={session.id}
                        className="group relative border-primary/20 bg-primary/[0.02] hover:bg-primary/[0.05] transition-all cursor-pointer overflow-hidden"
                        onClick={() => setSelectedSession(session)}
                    >
                        {/* Decorative background element */}
                        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:scale-110 transition-transform">
                            <Activity className="h-12 w-12 text-primary" />
                        </div>

                        <CardHeader className="pb-2">
                            <div className="flex justify-between items-start">
                                <CardTitle className="text-lg font-bold group-hover:text-primary transition-colors">
                                    {session.theme_name}
                                </CardTitle>
                                <div className="px-2 py-1 rounded text-[10px] bg-primary/10 text-primary font-bold uppercase tracking-wider border border-primary/20">
                                    {session.stage}
                                </div>
                            </div>
                            <CardDescription className="text-xs line-clamp-1">{session.version_name}</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center justify-between text-sm mt-2">
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Users className="h-4 w-4" />
                                    <span className="text-xs">Beheer participatie</span>
                                </div>
                                <div className="flex items-center gap-1 text-primary font-medium text-xs">
                                    Open Dashboard
                                    <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <Dialog open={!!selectedSession} onOpenChange={(open) => !open && setSelectedSession(null)}>
                <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                    {selectedSession && (
                        <ModeratorDashboard
                            sessionId={selectedSession.id}
                            stage={selectedSession.stage}
                            onClose={() => setSelectedSession(null)}
                        />
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
};
