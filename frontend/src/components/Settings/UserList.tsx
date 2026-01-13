import React, { useState, useEffect } from 'react';
import { api, type User } from '../../services/api';

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
    const [activeTab, setActiveTab] = useState<'users' | 'details'>('users');
    const [orgName, setOrgName] = useState('');
    const [orgDesc, setOrgDesc] = useState('');

    useEffect(() => {
        fetchUsers();
        fetchOrgDetails();
    }, [organizationId]);

    const fetchOrgDetails = async () => {
        try {
            // Since we don't have getOrganization(id), we list all and find (not efficient but checking API limits)
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
        } catch (error) {
            console.error('Failed to fetch users', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleInvite = async (e: React.FormEvent) => {
        e.preventDefault();
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
    };

    const saveEdit = async (userId: string) => {
        try {
            await api.updateOrgMember(organizationId, userId, editRole);
            setEditingUserId(null);
            fetchUsers();
        } catch (error) {
            console.error('Failed to update user', error);
        }
    };

    const deleteUser = async (userId: string) => {
        if (!confirm('Weet je zeker dat je deze gebruiker wilt verwijderen uit de organisatie?')) return;
        try {
            await api.removeOrgMember(organizationId, userId);
            fetchUsers();
        } catch (error) {
            console.error('Failed to remove user', error);
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-8">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 mb-2">Instellingen</h1>
                    <div className="flex gap-4 border-b border-slate-200">
                        <button
                            onClick={() => setActiveTab('users')}
                            className={`pb-2 text-sm font-medium transition-colors ${activeTab === 'users' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-500 hover:text-slate-800'}`}
                        >
                            Gebruikers
                        </button>
                        <button
                            onClick={() => setActiveTab('details')}
                            className={`pb-2 text-sm font-medium transition-colors ${activeTab === 'details' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-500 hover:text-slate-800'}`}
                        >
                            Organisatie Details
                        </button>
                    </div>
                </div>
                {activeTab === 'users' && (
                    <button
                        onClick={() => setIsInviting(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors self-start mt-2"
                    >
                        + Gebruiker Uitnodigen
                    </button>
                )}
            </div>

            {activeTab === 'details' && (
                <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 animate-fade-in">
                    <h2 className="text-xl font-bold text-slate-900 mb-6">Organisatie Informatie</h2>
                    <div className="grid grid-cols-1 gap-6 max-w-lg">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Organisatie Naam</label>
                            <input
                                type="text"
                                value={orgName}
                                onChange={(e) => setOrgName(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Beschrijving</label>
                            <textarea
                                value={orgDesc}
                                onChange={(e) => setOrgDesc(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none h-24 resize-none"
                            />
                        </div>
                        <div className="pt-4">
                            <button className="bg-slate-900 text-white px-4 py-2 rounded-lg font-medium hover:bg-slate-800 transition-colors">
                                Opslaan
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'users' && (
                <>

                    {isInviting && (
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-8 animate-fade-in">
                            <h3 className="text-lg font-semibold mb-4">Nieuw Lid Toevoegen</h3>
                            <form onSubmit={handleInvite} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">E-mailadres</label>
                                    <input
                                        type="email"
                                        value={inviteEmail}
                                        onChange={e => setInviteEmail(e.target.value)}
                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                        placeholder="naam@organisatie.nl"
                                        autoFocus
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Rol</label>
                                    <select
                                        value={inviteRole}
                                        onChange={e => setInviteRole(e.target.value)}
                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                    >
                                        <option value="member">Lid</option>
                                        <option value="admin">Beheerder</option>
                                    </select>
                                </div>
                                <div className="flex justify-end gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setIsInviting(false)}
                                        className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                                    >
                                        Annuleren
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={!inviteEmail}
                                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                                    >
                                        Toevoegen
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 text-sm font-semibold">
                                    <th className="px-6 py-4">Naam</th>
                                    <th className="px-6 py-4">E-mail</th>
                                    <th className="px-6 py-4">Rol</th>
                                    <th className="px-6 py-4">Lid Sinds</th>
                                    <th className="px-6 py-4 text-right">Acties</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {users.map(user => (
                                    <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-slate-800">{user.name || "-"}</td>
                                        <td className="px-6 py-4 text-slate-600">{user.email}</td>
                                        <td className="px-6 py-4">
                                            {editingUserId === user.id ? (
                                                <div className="flex items-center gap-2">
                                                    <select
                                                        value={editRole}
                                                        onChange={e => setEditRole(e.target.value)}
                                                        className="bg-white border border-slate-300 rounded text-sm px-2 py-1"
                                                    >
                                                        <option value="member">Lid</option>
                                                        <option value="admin">Beheerder</option>
                                                    </select>
                                                    <button onClick={() => saveEdit(user.id)} className="text-green-600 hover:text-green-800 text-xs font-bold">OK</button>
                                                    <button onClick={() => setEditingUserId(null)} className="text-slate-400 hover:text-slate-600 text-xs">X</button>
                                                </div>
                                            ) : (
                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${user.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                                                    }`}>
                                                    {user.role === 'admin' ? 'Beheerder' : 'Lid'}
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-slate-500 text-sm">
                                            {user.joined_at ? new Date(user.joined_at).toLocaleDateString() : '-'}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => startEditing(user)}
                                                className="text-slate-400 hover:text-blue-600 mr-3"
                                                title="Bewerken"
                                            >
                                                ✎
                                            </button>
                                            <button
                                                onClick={() => deleteUser(user.id)}
                                                className="text-slate-400 hover:text-red-600"
                                                title="Verwijderen"
                                            >
                                                🗑
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {users.length === 0 && !isLoading && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                                            Geen gebruikers gevonden.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                    {isLoading && <div className="mt-4 text-center text-slate-500">Laden...</div>}
                </>
            )}
        </div>
    );
};
