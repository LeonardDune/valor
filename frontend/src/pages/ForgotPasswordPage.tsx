import { useState } from 'react';
import { supabase } from '../lib/supabase';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '../components/ui/card';
import { Link } from 'react-router-dom';

export const ForgotPasswordPage = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleReset = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);
        setError(null);

        // Dynamic redirect URL based on current origin
        // This ensures it works on localhost and production
        const redirectTo = `${window.location.origin}/update-password`;

        try {
            const { error } = await supabase.auth.resetPasswordForEmail(email, {
                redirectTo,
            });

            if (error) throw error;

            setMessage('Als er een account bestaat voor dit e-mailadres, heb je een herstel-link ontvangen.');
        } catch (err: any) {
            console.error('Password reset request failed:', err);
            // Don't reveal if user exists or not for security, but usually Supabase gives generic success
            // unless rate limited.
            setError(err.message || 'Kon herstel-aanvraag niet verwerken.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle>Wachtwoord Vergeten?</CardTitle>
                    <CardDescription>
                        Vul je e-mailadres in en we sturen je een link om een nieuw wachtwoord in te stellen.
                    </CardDescription>
                </CardHeader>
                <form onSubmit={handleReset}>
                    {/* Show success message mostly, hide form if desired, but keeping form allows retry if typo */}
                    <CardContent className="space-y-4">
                        {message && (
                            <div className="bg-green-50 text-green-700 p-3 rounded text-sm mb-4">
                                {message}
                            </div>
                        )}
                        {error && (
                            <div className="bg-red-50 text-red-500 p-3 rounded text-sm mb-4">
                                {error}
                            </div>
                        )}

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
                    </CardContent>
                    <CardFooter className="flex flex-col space-y-4">
                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? 'Versturen...' : 'Stuur Herstel Link'}
                        </Button>
                        <div className="text-center text-sm">
                            <Link to="/login" className="text-primary hover:underline">
                                Terug naar Inloggen
                            </Link>
                        </div>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
};
