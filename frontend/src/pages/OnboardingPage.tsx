import React, { useState } from 'react';
import { api } from '../services/api';
import { useOrganization } from '../context/OrganizationContext';
import { useAuth } from '../context/AuthContext';

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
            <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        {step === 1 ? "Welkom bij CAUSA" : "Maak je Organisatie"}
                    </h2>
                    <p className="mt-2 text-center text-sm text-gray-600">
                        {step === 1
                            ? "Laten we beginnen met je profiel gegevens."
                            : "Bijna klaar! Maak een workspace voor je team."}
                    </p>
                </div>

                {step === 1 ? (
                    <form className="mt-8 space-y-6" onSubmit={handleProfileSubmit}>
                        <div className="rounded-md shadow-sm -space-y-px">
                            <div className="mb-4">
                                <label htmlFor="first-name" className="sr-only">Voornaam</label>
                                <input
                                    id="first-name"
                                    type="text"
                                    required
                                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                    placeholder="Voornaam"
                                    value={firstName}
                                    onChange={(e) => setFirstName(e.target.value)}
                                />
                            </div>
                            <div className="mb-4">
                                <label htmlFor="last-name" className="sr-only">Achternaam</label>
                                <input
                                    id="last-name"
                                    type="text"
                                    required
                                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                    placeholder="Achternaam"
                                    value={lastName}
                                    onChange={(e) => setLastName(e.target.value)}
                                />
                            </div>
                            <div>
                                <label htmlFor="username" className="sr-only">Gebruikersnaam</label>
                                <input
                                    id="username"
                                    type="text"
                                    required
                                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                    placeholder="Gebruikersnaam"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                />
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                            >
                                {isLoading ? 'Opslaan...' : 'Volgende'}
                            </button>
                        </div>
                    </form>
                ) : (
                    <form className="mt-8 space-y-6" onSubmit={handleOrgSubmit}>
                        <div className="rounded-md shadow-sm -space-y-px">
                            <div className="mb-4">
                                <label htmlFor="org-name" className="sr-only">Organisatie Naam</label>
                                <input
                                    id="org-name"
                                    type="text"
                                    required
                                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                    placeholder="Organisatie Naam (bijv. Mijn Bedrijf)"
                                    value={orgName}
                                    onChange={(e) => setOrgName(e.target.value)}
                                />
                            </div>
                            <div>
                                <label htmlFor="org-desc" className="sr-only">Beschrijving</label>
                                <textarea
                                    id="org-desc"
                                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                    placeholder="Korte beschrijving (optioneel)"
                                    value={orgDesc}
                                    onChange={(e) => setOrgDesc(e.target.value)}
                                />
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                            >
                                {isLoading ? 'Aanmaken...' : 'Starten!'}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
};

export default OnboardingPage;
