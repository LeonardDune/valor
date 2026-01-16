import React, { useState } from 'react';
import { api } from '../services/api';
import { useOrganization } from '../context/OrganizationContext';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const OnboardingPage: React.FC = () => {
    const { refreshOrganizations } = useOrganization();
    const { user: _ } = useAuth(); // Prefixed with _ to silence unused warning, or just remove if truly unused.
    const [step, setStep] = useState(1);
    const [isLoading, setIsLoading] = useState(false);

    // Profile State
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [username, setUsername] = useState('');

    // Org State
    const [orgName, setOrgName] = useState('');
    const [orgDesc, setOrgDesc] = useState('');

    const handleProfileSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await api.updateUserProfile(firstName, lastName, username);
            setStep(2);
        } catch (error) {
            console.error("Failed to update profile", error);
            alert("Er ging iets mis bij het opslaan van je profiel.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleOrgSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await api.createOrganization(orgName, orgDesc);
            await refreshOrganizations();
            // App.tsx logic will handle redirection once orgs are loaded
        } catch (error) {
            console.error("Failed to create org", error);
            alert("Er ging iets mis bij het aanmaken van de organisatie.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <Card className="max-w-md w-full">
                <CardHeader>
                    <CardTitle className="text-center text-3xl font-extrabold text-gray-900">
                        {step === 1 ? "Welkom bij CAUSA" : "Maak je Organisatie"}
                    </CardTitle>
                    <CardDescription className="text-center">
                        {step === 1
                            ? "Laten we beginnen met je profiel gegevens."
                            : "Bijna klaar! Maak een workspace voor je team."}
                    </CardDescription>
                </CardHeader>
                <CardContent>

                    {step === 1 ? (
                        <form className="mt-8 space-y-6" onSubmit={handleProfileSubmit}>
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="first-name">Voornaam</Label>
                                        <Input
                                            id="first-name"
                                            type="text"
                                            required
                                            placeholder="Voornaam"
                                            value={firstName}
                                            onChange={(e) => setFirstName(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="last-name">Achternaam</Label>
                                        <Input
                                            id="last-name"
                                            type="text"
                                            required
                                            placeholder="Achternaam"
                                            value={lastName}
                                            onChange={(e) => setLastName(e.target.value)}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="username">Gebruikersnaam</Label>
                                    <Input
                                        id="username"
                                        type="text"
                                        required
                                        placeholder="Gebruikersnaam"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                    />
                                </div>
                            </div>

                            <Button
                                type="submit"
                                disabled={isLoading}
                                className="w-full"
                            >
                                {isLoading ? 'Opslaan...' : 'Volgende'}
                            </Button>
                        </form>
                    ) : (
                        <form className="mt-8 space-y-6" onSubmit={handleOrgSubmit}>
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="org-name">Organisatie Naam</Label>
                                    <Input
                                        id="org-name"
                                        type="text"
                                        required
                                        placeholder="Organisatie Naam (bijv. Mijn Bedrijf)"
                                        value={orgName}
                                        onChange={(e) => setOrgName(e.target.value)}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="org-desc">Beschrijving</Label>
                                    <Textarea
                                        id="org-desc"
                                        placeholder="Korte beschrijving (optioneel)"
                                        value={orgDesc}
                                        onChange={(e) => setOrgDesc(e.target.value)}
                                    />
                                </div>
                            </div>

                            <Button
                                type="submit"
                                disabled={isLoading}
                                className="w-full"
                            >
                                {isLoading ? 'Aanmaken...' : 'Starten!'}
                            </Button>
                        </form>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default OnboardingPage;
