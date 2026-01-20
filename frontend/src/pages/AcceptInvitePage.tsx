import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { useAuth } from '../context/AuthContext';

interface AcceptInvitePageProps {
    onSuccess: () => void;
}

export const AcceptInvitePage: React.FC<AcceptInvitePageProps> = ({ onSuccess }) => {
    const [code, setCode] = useState('');
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');
    const { user } = useAuth(); // Ensure user is logged in, theoretically invited user might not be?
    // The invite flow assumes user accepts invite. If they are not logged in, they should probably log in first.
    // However, `invites.py` `accept_invite` requires `user_email`.
    // So the user MUST be logged in to accept.

    useEffect(() => {
        // Parse code from URL manually since no router
        const params = new URLSearchParams(window.location.search);
        const codeParam = params.get('code');
        if (codeParam) {
            setCode(codeParam);
        }
    }, []);

    const handleAccept = async () => {
        if (!code) return;
        setStatus('loading');
        try {
            await api.acceptInvite(code);
            setStatus('success');
            setTimeout(() => {
                // Clear query params
                window.history.replaceState({}, document.title, "/");
                onSuccess();
            }, 2000);
        } catch (error: any) {
            console.error('Failed to accept invite', error);
            setStatus('error');
            setErrorMessage(error.response?.data?.detail || "Er is iets misgegaan. Controleer de code.");
        }
    };

    if (!user) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-50">
                <Card className="w-[400px]">
                    <CardHeader>
                        <CardTitle>Inloggen vereist</CardTitle>
                        <CardDescription>Je moet ingelogd zijn om een uitnodiging te accepteren.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm text-muted-foreground mb-4">Log eerst in of registreer je, en klik dan opnieuw op de link in je e-mail.</p>
                        {/* Typically manual navigation here or relying on App.tsx to show Login */}
                        <p className="text-xs text-muted-foreground mt-4">Tip: Als je dit scherm ziet terwijl je ingelogd bent, herlaad de pagina.</p>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className="flex h-screen items-center justify-center bg-gray-50">
            <Card className="w-[400px]">
                <CardHeader>
                    <CardTitle>Uitnodiging Accepteren</CardTitle>
                    <CardDescription>Voer je uitnodigingscode in om lid te worden.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {status === 'success' ? (
                        <div className="flex flex-col items-center gap-2 p-4 text-center">
                            <CheckCircle className="h-12 w-12 text-green-500" />
                            <h3 className="font-semibold text-lg text-green-700">Succes!</h3>
                            <p className="text-sm text-muted-foreground">Je bent toegevoegd aan de organisatie. Je wordt doorgestuurd...</p>
                        </div>
                    ) : (
                        <>
                            <div className="space-y-2">
                                <Input
                                    placeholder="Uitnodigingscode"
                                    value={code}
                                    onChange={(e) => setCode(e.target.value)}
                                    disabled={status === 'loading'}
                                />
                            </div>

                            {status === 'error' && (
                                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                                    <XCircle className="h-4 w-4" />
                                    {errorMessage}
                                </div>
                            )}

                            <div className="flex justify-end">
                                <Button onClick={handleAccept} disabled={!code || status === 'loading'} className="w-full">
                                    {status === 'loading' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Accepteren & Deelnemen
                                </Button>
                            </div>
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};
