import React, { useState, useEffect } from 'react';
import { api, type User } from '../../services/api';
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
import { Plus, Trash2, Pencil, Check, X, Loader2 } from "lucide-react";

interface UserListProps {
    organizationId: string;
}

export const UserList: React.FC<UserListProps> = ({ organizationId }) => {
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isInviting, setIsInviting] = useState(false);
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteRole, setInviteRole] = useState('member');
    const [editingUserId, setEditingUserId] = useState<string | null>(null);
    const [editRole, setEditRole] = useState('member');
    const [editName, setEditName] = useState('');
    const [activeTab, setActiveTab] = useState<'users' | 'details'>('users');
    const [orgName, setOrgName] = useState('');
    const [orgDesc, setOrgDesc] = useState('');

    // Auth Check
    const { user: currentUser } = useAuth();
    const [isAdmin, setIsAdmin] = useState(false);

    useEffect(() => {
        fetchUsers();
        fetchOrgDetails();
    }, [organizationId]);

    const fetchOrgDetails = async () => {
        try {
            const orgs = await api.getOrganizations();
            const current = orgs.find(o => o.id === organizationId);
            if (current) {
                setOrgName(current.name);
                setOrgDesc(current.description || '');
            }
        } catch (error) {
            console.error('Failed to fetch org details', error);
        }
    };

    const fetchUsers = async () => {
        setIsLoading(true);
        try {
            const data = await api.getOrganizationUsers(organizationId);
            setUsers(data);

            if (currentUser) {
                const myMembership = data.find(u => u.email === currentUser.email);
                if (myMembership && myMembership.role === 'admin') {
                    setIsAdmin(true);
                } else {
                    setIsAdmin(false);
                }
            }
        } catch (error) {
            console.error('Failed to fetch users', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleInvite = async () => {
        if (!inviteEmail) return;

        try {
            await api.addOrganizationUser(organizationId, inviteEmail, inviteRole);
            setInviteEmail('');
            setInviteRole('member');
            setIsInviting(false);
            fetchUsers();
        } catch (error) {
            console.error('Failed to invite user', error);
        }
    };

    const startEditing = (user: User) => {
        setEditingUserId(user.id);
        setEditRole(user.role || 'member');
        setEditName(user.name || '');
    };

    const saveEdit = async (userId: string) => {
        try {
            await api.updateOrgMember(organizationId, userId, editRole, editName);
            setEditingUserId(null);
            fetchUsers();
        } catch (error) {
            console.error('Failed to update user', error);
        }
    };

    const deleteUser = async (userId: string) => {
        // Check if confirm modal is needed or using browsers confirm
        // For consistency let's stick to browser confirm or implement a modal later
        // The original code used window.confirm
        if (!confirm('Weet je zeker dat je deze gebruiker wilt verwijderen uit de organisatie?')) return;
        try {
            await api.removeOrgMember(organizationId, userId);
            fetchUsers();
        } catch (error) {
            console.error('Failed to remove user', error);
        }
    };

    return (
        <div className="max-w-5xl mx-auto p-8 space-y-8">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight">Instellingen</h1>
                <p className="text-muted-foreground">Beheer je organisatie, leden en rechten.</p>
            </div>

            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'users' | 'details')} className="w-full">
                <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
                    <TabsTrigger value="users">Gebruikers</TabsTrigger>
                    <TabsTrigger value="details">Organisatie Details</TabsTrigger>
                </TabsList>

                <TabsContent value="users" className="space-y-4 mt-6">
                    <div className="flex justify-between items-center">
                        <div className="space-y-1">
                            <h2 className="text-xl font-semibold tracking-tight">Leden</h2>
                            <p className="text-sm text-muted-foreground">Beheer wie toegang heeft tot deze organisatie.</p>
                        </div>
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
                                        Stuur een uitnodiging naar een nieuw lid via hun e-mailadres.
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4 py-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="email">E-mailadres</Label>
                                        <Input
                                            id="email"
                                            placeholder="naam@organisatie.nl"
                                            value={inviteEmail}
                                            onChange={(e) => setInviteEmail(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="role">Rol</Label>
                                        <Select value={inviteRole} onValueChange={setInviteRole}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Selecteer een rol" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="member">Lid</SelectItem>
                                                <SelectItem value="admin">Beheerder</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button variant="outline" onClick={() => setIsInviting(false)}>Annuleren</Button>
                                    <Button onClick={handleInvite} disabled={!inviteEmail}>Uitnodigen</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </div>

                    <Card>
                        <CardContent className="p-0">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Naam</TableHead>
                                        <TableHead>E-mail</TableHead>
                                        <TableHead>Rol</TableHead>
                                        <TableHead>Lid Sinds</TableHead>
                                        <TableHead className="text-right">Acties</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {isLoading ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="h-24 text-center">
                                                <div className="flex items-center justify-center gap-2 text-muted-foreground">
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                    Laden...
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ) : users.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
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
                                                    {editingUserId === user.id ? (
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
                                                        <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                                                            {user.role === 'admin' ? 'Beheerder' : 'Lid'}
                                                        </Badge>
                                                    )}
                                                </TableCell>
                                                <TableCell className="text-muted-foreground">
                                                    {user.joined_at ? new Date(user.joined_at).toLocaleDateString() : '-'}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    {editingUserId === user.id ? (
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
                                                    )}
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

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
                                    value={orgName}
                                    onChange={(e) => setOrgName(e.target.value)}
                                    disabled={!isAdmin}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="orgDesc">Beschrijving</Label>
                                <Textarea
                                    id="orgDesc"
                                    value={orgDesc}
                                    onChange={(e) => setOrgDesc(e.target.value)}
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
            </Tabs>
        </div>
    );
};
