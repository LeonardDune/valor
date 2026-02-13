import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { api, type ThemeVersion } from '../services/api';
import { type VotingSession } from '../types/session';
import { useActiveSession } from '../hooks/queries/useSessions';

interface ThemeContextType {
    themeId: string | null;
    activeVersion: ThemeVersion | null;
    currentViewedVersion: ThemeVersion | null;
    versions: ThemeVersion[];
    isReadOnly: boolean;
    isLoading: boolean;
    activeVotingSession: VotingSession | null;
    setActiveVotingSession: React.Dispatch<React.SetStateAction<VotingSession | null>>;
    switchVersion: (versionId: string) => void;
    refreshVersions: () => Promise<void>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
    themeId: string;
    children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ themeId, children }) => {
    const [activeVersion, setActiveVersion] = useState<ThemeVersion | null>(null);
    const [currentViewedVersion, setCurrentViewedVersion] = useState<ThemeVersion | null>(null);
    const [versions, setVersions] = useState<ThemeVersion[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const { data: activeVotingSession } = useActiveSession(activeVersion?.id || null);

    const fetchThemeData = useCallback(async () => {
        setIsLoading(true);
        try {
            // Parallel fetch for efficiency
            const [fetchedActive, fetchedVersions] = await Promise.all([
                api.getThemeActiveVersion(themeId),
                api.getThemeVersions(themeId)
            ]);

            setActiveVersion(fetchedActive);
            setVersions(fetchedVersions);

            // If we haven't selected a version yet, or if the selection is invalid, default to Active
            if (!currentViewedVersion || !fetchedVersions.find(v => v.id === currentViewedVersion.id)) {
                setCurrentViewedVersion(fetchedActive);
            } else {
                // Determine if we need to update the current viewed object to latest ref
                const updatedViewed = fetchedVersions.find(v => v.id === currentViewedVersion.id);
                if (updatedViewed) setCurrentViewedVersion(updatedViewed);
            }

        } catch (error) {
            console.error("Failed to fetch theme context data", error);
        } finally {
            setIsLoading(false);
        }
    }, [themeId, currentViewedVersion]); // logic slightly complex on viewed update, simplified below

    // Initial load
    useEffect(() => {
        fetchThemeData();
    }, [themeId]);

    const refreshVersions = async () => {
        await fetchThemeData();
    };

    const switchVersion = (versionId: string) => {
        const found = versions.find(v => v.id === versionId);
        if (found) {
            setCurrentViewedVersion(found);
        }
    };

    // Read Only if the viewed version ID is different from the Active Version ID
    const isReadOnly = activeVersion && currentViewedVersion
        ? activeVersion.id !== currentViewedVersion.id
        : false;

    return (
        <ThemeContext.Provider value={{
            themeId,
            activeVersion,
            currentViewedVersion,
            versions,
            isReadOnly,
            isLoading,
            activeVotingSession: activeVotingSession || null,
            setActiveVotingSession: () => {
                console.warn("setActiveVotingSession is deprecated. Session state is now managed by React Query.");
            },
            switchVersion,
            refreshVersions
        }}>
            {children}
        </ThemeContext.Provider>
    );
};

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error("useTheme must be used within a ThemeProvider");
    }
    return context;
};
