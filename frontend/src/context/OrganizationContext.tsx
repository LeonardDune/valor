import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { api, type Organization } from '../services/api';

interface OrganizationContextType {
    organizations: Organization[];
    activeOrganization: Organization | null;
    switchOrganization: (orgId: string) => void;
    refreshOrganizations: () => Promise<void>;
    isLoading: boolean;
}

export const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const OrganizationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [activeOrganization, setActiveOrganization] = useState<Organization | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchOrganizations = async () => {
        setIsLoading(true);
        try {
            const orgs = await api.getOrganizations();
            setOrganizations(orgs);

            // Set active org logic (first available if none selected)
            if (orgs.length > 0 && !activeOrganization) {
                setActiveOrganization(orgs[0]);
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
        fetchOrganizations();
    }, []);

    const switchOrganization = (orgId: string) => {
        const org = organizations.find(o => o.id === orgId);
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
