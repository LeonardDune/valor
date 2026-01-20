import React, { useState, useEffect } from 'react';
import { api, type User, type Invite } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2, Pencil, Check, X, Loader2, ShieldCheck } from "lucide-react";
import { Separator } from "@/components/ui/separator";

interface MemberManagementProps {
    entityId: string;
    entityType: 'organization' | 'project' | 'theme' | 'global';
}

export const MemberManagement: React.FC<MemberManagementProps> = ({ entityId, entityType }) => {
    const [users, setUsers] = useState<User[]>([]);
    const [invites, setInvites] = useState<Invite[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isInviting, setIsInviting] = useState(false);
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteRole, setInviteRole] = useState('member');
    const [inviteDays, setInviteDays] = useState('7');
    const [editingUserId, setEditingUserId] = useState<string | null>(null);
    const [editRole, setEditRole] = useState('member');
    const [editName, setEditName] = useState('');
    const [activeTab, setActiveTab] = useState<'users' | 'details'>('users');
    const [entityName, setEntityName] = useState('');
    const [entityDesc, setEntityDesc] = useState('');

    // Auth Check
    const { user: currentUser } = useAuth();
    const [isAdmin, setIsAdmin] = useState(false);

    useEffect(() => {
        fetchUsers();
        if (entityType === 'organization') {
            fetchOrgDetails();
        }
    }, [entityId, entityType]);

    const fetchOrgDetails = async () => {
        try {
            const orgs = await api.getOrganizations();
            const current = orgs.find(o => o.id === entityId);
            if (current) {
                setEntityName(current.name);
                setEntityDesc(current.description || '');
            }
        } catch (error) {
            console.error('Failed to fetch org details', error);
        }
    };

    const fetchUsers = async () => {
        setIsLoading(true);
        try {
            let data: User[] = [];
            if (entityType === 'organization') {
                data = await api.getOrganizationUsers(entityId);
            } else if (entityType === 'project') {
                data = await api.getProjectUsers(entityId);
            } else if (entityType === 'theme') {
                data = await api.getThemeUsers(entityId);
            } else if (entityType === 'global') {
                data = await api.getAllUsers();
            }
            setUsers(data);

            // Determine if current user is admin
            // For global, we check checks platform admin status separately or assume if they can access this page they are admin
            // But we should also check scoped roles. 
            if (currentUser) {
                if (entityType === 'global') {
                    // For global view, if we successfully fetched, we are implicitly admin (enforced by backend)
                    setIsAdmin(true);
                } else {
                    const myMembership = data.find(u => u.email === currentUser.email);
                    if (myMembership && myMembership.role === 'admin') {
                        setIsAdmin(true);
                        // Fetch invites if admin
                        fetchInvites();
                    } else if (currentUser.role === 'admin') { // Check global role maybe? 
                        // Actually, currentUser context might not have the correct context-aware role.
                        // Rely on fetched membership.
                        setIsAdmin(false);
                    } else {
                        setIsAdmin(false);
                    }
                }

                // Always try to fetch invites if we think we might be admin? 
                // Or just if we found we are admin.
                // Re-check invites logic below.
            }
        } catch (error) {
            console.error('Failed to fetch users', error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchInvites = async () => {
        if (entityType === 'global') return; // No global invites yet
        try {
            const data = await api.getPendingInvites(entityId, entityType as any);
            setInvites(data);
        } catch (error) {
            console.error('Failed to fetch invites', error);
        }
    }

    const handleInvite = async () => {
        if (!inviteEmail) return;

        try {
            await api.createInvite(inviteEmail, entityId, inviteRole, parseInt(inviteDays));
            setInviteEmail('');
            setInviteRole('member');
            setIsInviting(false);
            fetchUsers(); // If direct add
            fetchInvites(); // If pending
        } catch (error) {
            console.error('Failed to invite user', error);
            alert("Er is iets misgegaan bij het uitnodigen.");
        }
    };

    const startEditing = (user: User) => {
        setEditingUserId(user.id);
        setEditRole(user.role || 'member');
        setEditName(user.name || '');
    };

    const saveEdit = async (userId: string) => {
        try {
            // Update logic depends on entity type. 
            // Currently only api.updateOrgMember exists.
            // Need updateProjectMember / updateThemeMember etc.
            // For now, only Org updates are supported by backend?
            if (entityType === 'organization') {
                await api.updateOrgMember(entityId, userId, editRole, editName);
            } else {
                alert("Rol aanpassen is alleen beschikbaar voor organisaties in deze versie.");
                return;
            }
            setEditingUserId(null);
            fetchUsers();
        } catch (error) {
            console.error('Failed to update user', error);
        }
    };

    const deleteUser = async (userId: string) => {
        if (!confirm('Weet je zeker dat je deze gebruiker wilt verwijderen?')) return;
        try {
            if (entityType === 'organization') {
                await api.removeOrgMember(entityId, userId);
            } else {
                alert("Verwijderen is alleen beschikbaar voor organisaties in deze versie.");
                return;
            }
            fetchUsers();
        } catch (error) {
            console.error('Failed to remove user', error);
        }
    };

    // Helper for labels
    const getEntityLabel = () => {
        switch (entityType) {
            case 'organization': return 'Organisatie';
            case 'project': return 'Project';
            case 'theme': return 'Thema';
            case 'global': return 'Platform';
            default: return 'Entity';
        }
    }

    return (
        <div className="space-y-8">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight">Ledenbeheer - {getEntityLabel()}</h1>
                <p className="text-muted-foreground">Beheer wie toegang heeft tot dit {getEntityLabel().toLowerCase()}.</p>
            </div>

            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'users' | 'details')} className="w-full">
                <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
                    <TabsTrigger value="users">Gebruikers</TabsTrigger>
                    {entityType === 'organization' && <TabsTrigger value="details">Details</TabsTrigger>}
                </TabsList>

                <TabsContent value="users" className="space-y-8 mt-6">
                    {/* Active Members Section */}
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <div className="space-y-1">
                                <h2 className="text-xl font-semibold tracking-tight">Leden</h2>
                                <p className="text-sm text-muted-foreground">Lijst van actieve leden.</p>
                            </div>
                            {entityType !== 'global' && (isAdmin &&
                                <Dialog open={isInviting} onOpenChange={setIsInviting}>
                                    <DialogTrigger asChild>
                                        <Button>
                                            <Plus className="mr-2 h-4 w-4" />
                                            Nieuw Lid
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader>
                                            <DialogTitle>Nieuw Lid Uitnodigen</DialogTitle>
                                            <DialogDescription>
                                                Nodig iemand uit voor dit {getEntityLabel().toLowerCase()}.
                                            </DialogDescription>
                                        </DialogHeader>
                                        <div className="space-y-4 py-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="email">E-mailadres</Label>
                                                <Input
                                                    id="email"
                                                    placeholder="naam@voorbeeld.nl"
                                                    value={inviteEmail}
                                                    onChange={(e) => setInviteEmail(e.target.value)}
                                                />
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-2">
                                                    <Label htmlFor="role">Rol</Label>
                                                    <Select value={inviteRole} onValueChange={setInviteRole}>
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Selecteer een rol" />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="member">Lid</SelectItem>
                                                            <SelectItem value="viewer">Kijker</SelectItem>
                                                            <SelectItem value="admin">Beheerder</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                                <div className="space-y-2">
                                                    <Label htmlFor="days">Geldigheidsduur (dagen)</Label>
                                                    <Input
                                                        id="days"
                                                        type="number"
                                                        min="1"
                                                        value={inviteDays}
                                                        onChange={(e) => setInviteDays(e.target.value)}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                        <DialogFooter>
                                            <Button variant="outline" onClick={() => setIsInviting(false)}>Annuleren</Button>
                                            <Button onClick={handleInvite} disabled={!inviteEmail}>Uitnodigen</Button>
                                        </DialogFooter>
                                    </DialogContent>
                                </Dialog>
                            )}
                        </div>

                        <Card>
                            <CardContent className="p-0">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Naam</TableHead>
                                            <TableHead>E-mail</TableHead>
                                            <TableHead>Rol</TableHead>
                                            {entityType === 'global' && <TableHead>Status</TableHead>}
                                            <TableHead>Lid Sinds</TableHead>
                                            <TableHead className="text-right">Acties</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {isLoading ? (
                                            <TableRow>
                                                <TableCell colSpan={6} className="h-24 text-center">
                                                    <div className="flex items-center justify-center gap-2 text-muted-foreground">
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                        Laden...
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        ) : users.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                                                    Geen gebruikers gevonden.
                                                </TableCell>
                                            </TableRow>
                                        ) : (
                                            users.map((user) => (
                                                <TableRow key={user.id}>
                                                    <TableCell className="font-medium">
                                                        {editingUserId === user.id ? (
                                                            <Input
                                                                value={editName}
                                                                onChange={(e) => setEditName(e.target.value)}
                                                                className="h-8 w-[150px]"
                                                            />
                                                        ) : (
                                                            user.name || "-"
                                                        )}
                                                    </TableCell>
                                                    <TableCell>{user.email}</TableCell>
                                                    <TableCell>
                                                        {editingUserId === user.id && entityType === 'organization' ? (
                                                            <Select value={editRole} onValueChange={setEditRole}>
                                                                <SelectTrigger className="h-8 w-[130px]">
                                                                    <SelectValue />
                                                                </SelectTrigger>
                                                                <SelectContent>
                                                                    <SelectItem value="member">Lid</SelectItem>
                                                                    <SelectItem value="admin">Beheerder</SelectItem>
                                                                </SelectContent>
                                                            </Select>
                                                        ) : (
                                                            <div className="flex gap-2">
                                                                <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                                                                    {user.role === 'admin' ? 'Beheerder' : (user.role || 'Lid')}
                                                                </Badge>
                                                                {user.is_platform_admin && (
                                                                    <Badge variant="outline" className="border-blue-500 text-blue-500 flex items-center gap-1">
                                                                        <ShieldCheck className="h-3 w-3" />
                                                                        Global
                                                                    </Badge>
                                                                )}
                                                            </div>
                                                        )}
                                                    </TableCell>
                                                    {entityType === 'global' && (
                                                        <TableCell>
                                                            {/* Status placeholder */}
                                                            <Badge variant="outline">Actief</Badge>
                                                        </TableCell>
                                                    )}
                                                    <TableCell className="text-muted-foreground">
                                                        {user.joined_at ? new Date(user.joined_at).toLocaleDateString() : '-'}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        {entityType === 'organization' && isAdmin && (
                                                            editingUserId === user.id ? (
                                                                <div className="flex justify-end gap-2">
                                                                    <Button size="icon" variant="ghost" onClick={() => saveEdit(user.id)} className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-50">
                                                                        <Check className="h-4 w-4" />
                                                                    </Button>
                                                                    <Button size="icon" variant="ghost" onClick={() => setEditingUserId(null)} className="h-8 w-8 text-muted-foreground hover:text-foreground">
                                                                        <X className="h-4 w-4" />
                                                                    </Button>
                                                                </div>
                                                            ) : (
                                                                <div className="flex justify-end gap-2">
                                                                    <Button size="icon" variant="ghost" onClick={() => startEditing(user)} className="h-8 w-8 text-muted-foreground hover:text-primary">
                                                                        <Pencil className="h-4 w-4" />
                                                                    </Button>
                                                                    <Button size="icon" variant="ghost" onClick={() => deleteUser(user.id)} className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10">
                                                                        <Trash2 className="h-4 w-4" />
                                                                    </Button>
                                                                </div>
                                                            )
                                                        )}
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        )}
                                    </TableBody>
                                </Table>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Pending Invites Section - Only for Org/Project/Theme */}
                    {entityType !== 'global' && invites.length > 0 && (
                        <div className="space-y-4">
                            <Separator />
                            <div className="space-y-1">
                                <h2 className="text-xl font-semibold tracking-tight">Openstaande Uitnodigingen</h2>
                                <p className="text-sm text-muted-foreground">Deze personen hebben hun uitnodiging nog niet geaccepteerd.</p>
                            </div>
                            <Card>
                                <CardContent className="p-0">
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead>E-mail</TableHead>
                                                <TableHead>Rol</TableHead>
                                                <TableHead>Verzonden Op</TableHead>
                                                <TableHead>Verloopt Op</TableHead>
                                                <TableHead>Status</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {invites.map((invite) => (
                                                <TableRow key={invite.id}>
                                                    <TableCell>{invite.email}</TableCell>
                                                    <TableCell>
                                                        <Badge variant="outline">{invite.role}</Badge>
                                                    </TableCell>
                                                    <TableCell className="text-muted-foreground">
                                                        {invite.created_at ? new Date(invite.created_at).toLocaleDateString() : '-'}
                                                    </TableCell>
                                                    <TableCell className="text-muted-foreground">
                                                        {invite.expires_at ? new Date(invite.expires_at).toLocaleDateString() : '-'}
                                                    </TableCell>
                                                    <TableCell className="font-mono text-xs text-muted-foreground">
                                                        In afwachting
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </CardContent>
                            </Card>
                        </div>
                    )}
                </TabsContent>

                {entityType === 'organization' && (
                    <TabsContent value="details" className="mt-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Organisatie Informatie</CardTitle>
                                <CardDescription>Pas de algemene gegevens van je organisatie aan.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6 max-w-lg">
                                <div className="space-y-2">
                                    <Label htmlFor="orgName">Organisatie Naam</Label>
                                    <Input
                                        id="orgName"
                                        value={entityName}
                                        onChange={(e) => setEntityName(e.target.value)}
                                        disabled={!isAdmin}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="orgDesc">Beschrijving</Label>
                                    <Textarea
                                        id="orgDesc"
                                        value={entityDesc}
                                        onChange={(e) => setEntityDesc(e.target.value)}
                                        disabled={!isAdmin}
                                        className="min-h-[100px]"
                                    />
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between border-t px-6 py-4">
                                {!isAdmin ? (
                                    <p className="text-sm text-muted-foreground italic">
                                        Alleen beheerders kunnen deze gegevens wijzigen.
                                    </p>
                                ) : (
                                    <div className="flex-1 flex justify-end">
                                        <Button>Opslaan</Button>
                                    </div>
                                )}
                            </CardFooter>
                        </Card>
                    </TabsContent>
                )}
            </Tabs>
        </div>
    );
};
