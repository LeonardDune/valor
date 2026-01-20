import React, { useState, useEffect } from 'react';
import { api, type Theme } from '../../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, ArrowLeft, Settings } from "lucide-react";
import { MemberManagement } from '../Settings/MemberManagement';

interface ThemeListProps {
    projectId: string;
    projectName: string;
    onSelectTheme: (themeId: string, themeName: string) => void;
    onBack: () => void;
}

export const ThemeList: React.FC<ThemeListProps> = ({ projectId, projectName, onSelectTheme, onBack }) => {
    const [themes, setThemes] = useState<Theme[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [newThemeName, setNewThemeName] = useState('');
    const [newThemeDesc, setNewThemeDesc] = useState('');
    const [activeTab, setActiveTab] = useState("themes");

    useEffect(() => {
        fetchThemes();
    }, [projectId]);

    const fetchThemes = async () => {
        try {
            const data = await api.getProjectThemes(projectId);
            setThemes(data);
        } catch (error) {
            console.error('Failed to fetch themes', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newThemeName) return;

        try {
            await api.createTheme(projectId, newThemeName, newThemeDesc);
            setNewThemeName('');
            setNewThemeDesc('');
            setIsDialogOpen(false);
            fetchThemes();
        } catch (error) {
            console.error('Failed to create theme', error);
        }
    };

    if (isLoading) return <div className="p-8 text-muted-foreground">Thema's laden...</div>;

    return (
        <div className="max-w-5xl mx-auto p-8 space-y-8">
            <Button
                variant="ghost"
                onClick={onBack}
                className="text-muted-foreground hover:text-foreground pl-0 gap-2"
            >
                <ArrowLeft className="h-4 w-4" />
                Terug naar Projecten
            </Button>

            <div className="space-y-1">
                <h2 className="text-lg font-medium text-muted-foreground">Project</h2>
                <h1 className="text-3xl font-bold tracking-tight">{projectName}</h1>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
                    <TabsTrigger value="themes">Thema's</TabsTrigger>
                    <TabsTrigger value="settings" className="gap-2">
                        <Settings className="h-4 w-4" />
                        Instellingen & Leden
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="themes" className="space-y-8 mt-6">
                    <div className="flex justify-between items-end">
                        <p className="text-muted-foreground">Selecteer een thema om te verkennen.</p>
                        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                            <DialogTrigger asChild>
                                <Button className="gap-2">
                                    <Plus className="h-4 w-4" />
                                    Nieuw Thema
                                </Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Nieuw Thema Toevoegen</DialogTitle>
                                    <DialogDescription>
                                        Voeg een specifiek thema of probleem toe aan dit project.
                                    </DialogDescription>
                                </DialogHeader>
                                <form onSubmit={handleCreate} className="space-y-4 py-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="name">Naam</Label>
                                        <Input
                                            id="name"
                                            value={newThemeName}
                                            onChange={e => setNewThemeName(e.target.value)}
                                            placeholder="Bijv. Sneeuwoverlast"
                                            autoFocus
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="desc">Omschrijving</Label>
                                        <Textarea
                                            id="desc"
                                            value={newThemeDesc}
                                            onChange={e => setNewThemeDesc(e.target.value)}
                                            placeholder="Wat gaan we onderzoeken?"
                                            rows={3}
                                        />
                                    </div>
                                    <DialogFooter>
                                        <Button type="submit" disabled={!newThemeName}>
                                            Aanmaken
                                        </Button>
                                    </DialogFooter>
                                </form>
                            </DialogContent>
                        </Dialog>
                    </div>

                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {themes.map(theme => (
                            <Card
                                key={theme.id}
                                className="hover:border-primary/50 transition-colors cursor-pointer group relative overflow-hidden"
                                onClick={() => onSelectTheme(theme.id, theme.name)}
                            >
                                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <CardTitle className="group-hover:text-primary transition-colors">{theme.name}</CardTitle>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <CardDescription className="line-clamp-3">
                                        {theme.description || "Geen omschrijving."}
                                    </CardDescription>
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    {themes.length === 0 && (
                        <Card className="border-dashed">
                            <CardContent className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                                <p>Nog geen thema's in dit project.</p>
                                <Button variant="link" onClick={() => setIsDialogOpen(true)}>
                                    Maak je eerste thema aan
                                </Button>
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>

                <TabsContent value="settings" className="mt-6">
                    <MemberManagement entityId={projectId} entityType="project" />
                </TabsContent>
            </Tabs>
        </div>
    );
};
