import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const LoginPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [isSignUp, setIsSignUp] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const { error } = await supabase.auth.signInWithPassword({
                email,
                password,
            });
            if (error) throw error;
        } catch (error: any) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSignUp = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const { error } = await supabase.auth.signUp({
                email,
                password,
            });
            if (error) throw error;
            setMessage('Registratie succesvol! Controleer je e-mail voor de bevestigingslink.');
        } catch (error: any) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-canvas flex items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-center text-primary">VALOR</CardTitle>
                    <CardDescription className="text-center">
                        {isSignUp ? 'Maak een account aan' : 'Log in op je account'}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {error && (
                        <div className="bg-destructive/15 text-destructive p-3 rounded-md mb-4 text-sm font-medium">
                            {error}
                        </div>
                    )}
                    {message && (
                        <div className="bg-green-500/15 text-green-600 p-3 rounded-md mb-4 text-sm font-medium">
                            {message}
                        </div>
                    )}

                    <form onSubmit={isSignUp ? handleSignUp : handleLogin} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">E-mailadres</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="naam@bedrijf.nl"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">Wachtwoord</Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                            <div className="text-right">
                                <Link to="/forgot-password" className="text-xs text-primary hover:underline">
                                    Wachtwoord vergeten?
                                </Link>
                            </div>
                        </div>
                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? 'Laden...' : (isSignUp ? 'Registreren' : 'Inloggen')}
                        </Button>
                    </form>

                    <div className="mt-4 text-center text-sm text-muted-foreground">
                        {isSignUp ? 'Heb je al een account?' : 'Nog geen account?'}
                        <button
                            onClick={() => { setIsSignUp(!isSignUp); setError(null); setMessage(null); }}
                            className="ml-1 text-primary hover:underline font-medium"
                        >
                            {isSignUp ? 'Login hier' : 'Maak account aan'}
                        </button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
