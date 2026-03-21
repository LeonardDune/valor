import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { MessageSquare, Plus, MessageCircle, ArrowRight } from 'lucide-react';
import { api, type ConversationThread } from '../services/api';
import { Button } from '@/components/ui/button';

export const VersionDashboard: React.FC = () => {
    // Check for versionId first, then spaceId fallback
    const params = useParams();
    const versionId = params.dsId || params.versionId || params.spaceId;

    const navigate = useNavigate();
    const [threads, setThreads] = useState<ConversationThread[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (versionId) {
            api.getVersionThreads(versionId)
                .then(setThreads)
                .catch(err => console.error("Failed to load threads for dashboard", err))
                .finally(() => setIsLoading(false));
        }
    }, [versionId]);

    return (
        <div className="p-6 space-y-6">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Version Dashboard</h1>
                    <p className="text-muted-foreground">Beheer de conversaties en claims voor deze versie. Version ID: {versionId}</p>
                </div>
                <Button onClick={() => navigate(`/designspace/${versionId}/chat`)}>
                    <MessageSquare className="mr-2 h-4 w-4" />
                    Open Chat
                </Button>
            </header>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <Card className="lg:col-span-2">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <div className="space-y-1">
                            <CardTitle>Gesprekken</CardTitle>
                            <CardDescription>Recente parallelle conversaties in deze versie.</CardDescription>
                        </div>
                        <Button variant="outline" size="sm" onClick={() => navigate(`/designspace/${versionId}/chat`)}>
                            <Plus className="h-4 w-4 mr-1" /> Nieuw
                        </Button>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <div className="py-8 text-center text-muted-foreground">Laden...</div>
                        ) : threads.length === 0 ? (
                            <div className="py-8 text-center text-muted-foreground">
                                <MessageCircle className="h-12 w-12 mx-auto mb-2 opacity-10" />
                                <p>Nog geen gesprekken gestart.</p>
                                <Button variant="link" onClick={() => navigate(`/designspace/${versionId}/chat`)}>
                                    Start je eerste gesprek
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {threads.slice(0, 5).map(thread => (
                                    <div
                                        key={thread.id}
                                        className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/50 cursor-pointer transition-colors"
                                        onClick={() => navigate(`/designspace/${versionId}/chat`)}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-full bg-primary/10 text-primary">
                                                <MessageSquare className="h-4 w-4" />
                                            </div>
                                            <div>
                                                <div className="font-medium text-sm">{thread.topic}</div>
                                                <div className="text-[10px] text-muted-foreground">
                                                    {thread.created_at ? new Date(thread.created_at).toLocaleDateString() : 'Recent'}
                                                </div>
                                            </div>
                                        </div>
                                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                ))}
                                {threads.length > 5 && (
                                    <Button variant="ghost" className="w-full text-xs mt-2" onClick={() => navigate(`/designspace/${versionId}/chat`)}>
                                        Bekijk alle {threads.length} gesprekken
                                    </Button>
                                )}
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Claims Overview</CardTitle>
                        <CardDescription>Status van geëxtraheerde factoren.</CardDescription>
                    </CardHeader >
                    <CardContent>
                        <p className="text-sm text-muted-foreground">Ga naar de Claims tab om factoren te valideren en toe te voegen aan het thema.</p>
                        <Button variant="outline" className="w-full mt-4" onClick={() => navigate(`/designspace/${versionId}/claims`)}>
                            Bekijk Claims
                        </Button>
                    </CardContent>
                </Card >
            </div >
        </div >
    );
};
