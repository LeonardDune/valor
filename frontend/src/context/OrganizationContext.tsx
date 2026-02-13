import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { api, type DashboardEnvironment } from '../services/api';

import { useAuth } from './AuthContext';

interface OrganizationContextType {
    organizations: DashboardEnvironment[];
    activeOrganization: DashboardEnvironment | null;
    switchOrganization: (orgId: string) => void;
    refreshOrganizations: () => Promise<void>;
    isLoading: boolean;
}

export const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const OrganizationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { session, isLoading: authLoading } = useAuth();
    const [organizations, setOrganizations] = useState<DashboardEnvironment[]>([]);
    const [activeOrganization, setActiveOrganization] = useState<DashboardEnvironment | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchOrganizations = async () => {
        if (!session) return; // Don't fetch if no session

        if (organizations.length === 0) setIsLoading(true);
        try {
            const orgs = await api.getDashboardEnvironments();
            setOrganizations(orgs);

            // Set active org logic (first available if none selected)
            if (orgs.length > 0) {
                if (!activeOrganization) {
                    setActiveOrganization(orgs[0]);
                } else {
                    // Refresh current active org from new list to get updated counts/projects
                    const updated = orgs.find((o: DashboardEnvironment) => o.id === activeOrganization.id);
                    if (updated) setActiveOrganization(updated);
                }
            }
        } catch (error) {
            console.error("Failed to fetch organizations", error);
        } finally {
            setIsLoading(false);
        }
    };

    const refreshOrganizations = async () => {
        await fetchOrganizations();
    };

    useEffect(() => {
        if (authLoading) return; // Wait for auth to initialize

        if (session) {
            fetchOrganizations();
        } else {
            // Reset if no session
            setOrganizations([]);
            setActiveOrganization(null);
            setIsLoading(false);
        }
    }, [session, authLoading]);

    const switchOrganization = (orgId: string) => {
        const org = organizations.find((o: DashboardEnvironment) => o.id === orgId);
        if (org) {
            setActiveOrganization(org);
        }
    };

    return (
        <OrganizationContext.Provider value={{
            organizations,
            activeOrganization,
            switchOrganization,
            isLoading,
            refreshOrganizations
        }}>
            {children}
        </OrganizationContext.Provider>
    );
};

export const useOrganization = () => {
    const context = useContext(OrganizationContext);
    if (!context) {
        throw new Error("useOrganization must be used within an OrganizationProvider");
    }
    return context;
};
