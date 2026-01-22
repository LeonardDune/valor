import React, { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { MemberManagement } from '@/components/Settings/MemberManagement';
import { AlertCircle, Archive, Plus, Settings, Users, Layers, Loader2 } from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { CreateProjectDialog } from './CreateProjectDialog';
import { CreateThemeDialog } from './CreateThemeDialog';
import { ConfirmModal } from '@/components/ui/ConfirmModal';

interface ManageEntityDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    entityId: string;
    entityType: 'organization' | 'project' | 'theme';
    initialData?: {
        name: string;
        description: string;
        role?: string;
    };
    onUpdated?: () => void;
}

export const ManageEntityDialog: React.FC<ManageEntityDialogProps> = ({
    open,
    onOpenChange,
    entityId,
    entityType,
    initialData,
    onUpdated
}) => {
    const [activeTab, setActiveTab] = useState('details');
    const [name, setName] = useState(initialData?.name || '');
    const [description, setDescription] = useState(initialData?.description || '');
    const [isSaving, setIsSaving] = useState(false);
    const [isArchiving, setIsArchiving] = useState(false);
    const [isArchiveConfirmOpen, setIsArchiveConfirmOpen] = useState(false);
    const [role, setRole] = useState(initialData?.role || 'member');

    const isAdmin = role === 'admin';

    // Reset local state when dialog opens or data changes
    useEffect(() => {
        if (open && initialData) {
            setName(initialData.name);
            setDescription(initialData.description);
            setRole(initialData.role || 'member');
        }
    }, [open, initialData]);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            if (entityType === 'organization') {
                await api.updateOrganization(entityId, name, description);
            } else if (entityType === 'project') {
                await api.updateProject(entityId, name, description);
            } else if (entityType === 'theme') {
                await api.updateTheme(entityId, name, description);
            }
            toast.success(`${getEntityLabel()} bijgewerkt`);
            onUpdated?.();
            onOpenChange(false);
        } catch (error) {
            console.error('Failed to update entity', error);
            toast.error('Fout bij het bijwerken');
        } finally {
            setIsSaving(false);
        }
    };

    const handleArchiveClick = () => {
        setIsArchiveConfirmOpen(true);
    };

    const handleArchiveConfirm = async () => {
        setIsArchiving(true);
        try {
            if (entityType === 'organization') {
                await api.archiveOrganization(entityId);
            } else if (entityType === 'project') {
                await api.archiveProject(entityId);
            } else if (entityType === 'theme') {
                await api.archiveTheme(entityId);
            }
            toast.success(`${getEntityLabel()} gearchiveerd`);
            onUpdated?.();
            onOpenChange(false);
        } catch (error) {
            console.error('Failed to archive entity', error);
            toast.error('Fout bij archiveren');
        } finally {
            setIsArchiving(false);
            setIsArchiveConfirmOpen(false);
        }
    };

    const getEntityLabel = () => {
        switch (entityType) {
            case 'organization': return 'Organisatie';
            case 'project': return 'Project';
            case 'theme': return 'Thema';
            default: return 'Item';
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col p-0">
                <DialogHeader className="p-6 pb-0">
                    <div className="flex justify-between items-center pr-8">
                        <div>
                            <DialogTitle className="text-2xl font-bold flex items-center gap-2">
                                {getEntityLabel()} Beheren: {initialData?.name}
                            </DialogTitle>
                            <DialogDescription>
                                Beheer instellingen, leden en structuur van dit {getEntityLabel().toLowerCase()}.
                            </DialogDescription>
                        </div>
                        <Badge variant={isAdmin ? "default" : "secondary"}>
                            {isAdmin ? "Beheerder" : "Lid"}
                        </Badge>
                    </div>
                </DialogHeader>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden flex flex-col">
                    <div className="px-6 border-b">
                        <TabsList className="bg-transparent h-12 gap-6 p-0">
                            <TabsTrigger
                                value="details"
                                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 h-12"
                            >
                                <Settings className="w-4 h-4 mr-2" />
                                Algemeen
                            </TabsTrigger>
                            <TabsTrigger
                                value="members"
                                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 h-12"
                            >
                                <Users className="w-4 h-4 mr-2" />
                                Leden
                            </TabsTrigger>
                            {(entityType === 'organization' || entityType === 'project') && (
                                <TabsTrigger
                                    value="structure"
                                    className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 h-12"
                                >
                                    <Layers className="w-4 h-4 mr-2" />
                                    Structuur
                                </TabsTrigger>
                            )}
                        </TabsList>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6">
                        <TabsContent value="details" className="mt-0 space-y-6">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Naam</Label>
                                    <Input
                                        id="name"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        disabled={!isAdmin}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="description">Beschrijving</Label>
                                    <Textarea
                                        id="description"
                                        className="min-h-[100px]"
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        disabled={!isAdmin}
                                    />
                                </div>
                                {isAdmin && (
                                    <div className="flex justify-end pt-2">
                                        <Button onClick={handleSave} disabled={isSaving}>
                                            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                            Wijzigingen Opslaan
                                        </Button>
                                    </div>
                                )}
                            </div>

                            <Separator />

                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-destructive flex items-center gap-2">
                                    <AlertCircle className="w-5 h-5" />
                                    Gevarenzone
                                </h3>
                                <div className="flex items-center justify-between p-4 border border-destructive/20 rounded-lg bg-destructive/5">
                                    <div>
                                        <p className="font-medium">Dit {getEntityLabel().toLowerCase()} archiveren</p>
                                        <p className="text-sm text-muted-foreground">Het item wordt verborgen maar niet definitief verwijderd.</p>
                                    </div>
                                    <Button
                                        variant="destructive"
                                        size="sm"
                                        onClick={handleArchiveClick}
                                        disabled={!isAdmin || isArchiving}
                                    >
                                        {isArchiving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Archive className="w-4 h-4 mr-2" />}
                                        Archiveren
                                    </Button>
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="members" className="mt-0">
                            {/* We wrap MemberManagement in a div that resets styles or we update MemberManagement itself */}
                            <MemberManagement entityId={entityId} entityType={entityType} />
                        </TabsContent>

                        <TabsContent value="structure" className="mt-0 space-y-6">
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-lg font-semibold">
                                        {entityType === 'organization' ? 'Projecten' : 'Thema\'s'}
                                    </h3>
                                    {isAdmin && (
                                        <>
                                            {entityType === 'organization' && (
                                                <CreateProjectDialog
                                                    organizationId={entityId}
                                                    onSuccess={() => { toast.success("Project aangemaakt"); onUpdated?.(); }}
                                                    trigger={
                                                        <Button size="sm">
                                                            <Plus className="w-4 h-4 mr-2" />
                                                            Nieuw Project
                                                        </Button>
                                                    }
                                                />
                                            )}
                                            {entityType === 'project' && (
                                                <CreateThemeDialog
                                                    projectId={entityId}
                                                    onSuccess={() => { toast.success("Thema aangemaakt"); onUpdated?.(); }}
                                                    trigger={
                                                        <Button size="sm">
                                                            <Plus className="w-4 h-4 mr-2" />
                                                            Nieuw Thema
                                                        </Button>
                                                    }
                                                />
                                            )}
                                        </>
                                    )}
                                </div>
                                <p className="text-sm text-muted-foreground italic">
                                    Lijstweergave van onderliggende structuren volgt in een volgende update.
                                </p>
                            </div>
                        </TabsContent>
                    </div>
                </Tabs>
            </DialogContent>

            <ConfirmModal
                isOpen={isArchiveConfirmOpen}
                onCancel={() => setIsArchiveConfirmOpen(false)}
                onConfirm={handleArchiveConfirm}
                title={`${getEntityLabel()} Archiveren`}
                message={`Weet je zeker dat je dit ${getEntityLabel().toLowerCase()} wilt archiveren? Alle onderliggende items worden ook gearchiveerd.`}
                isDanger={true}
                confirmLabel={isArchiving ? "Bezig..." : "Archiveren"}
            />
        </Dialog>
    );
};
