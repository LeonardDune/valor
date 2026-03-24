import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { api, type ThemeVersion } from '../services/api';
import { type VotingSession } from '../types/session';
import { useActiveSession } from '../hooks/queries/useSessions';

interface DesignSpaceContextType {
    dsId: string | null;
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

export const DesignSpaceContext = createContext<DesignSpaceContextType | undefined>(undefined);

interface DesignSpaceProviderProps {
    dsId: string;
    children: ReactNode;
}

export const DesignSpaceProvider: React.FC<DesignSpaceProviderProps> = ({ dsId, children }) => {
    const [activeVersion, setActiveVersion] = useState<ThemeVersion | null>(null);
    const [currentViewedVersion, setCurrentViewedVersion] = useState<ThemeVersion | null>(null);
    const [versions, setVersions] = useState<ThemeVersion[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const { data: activeVotingSession } = useActiveSession(activeVersion?.id || null);

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        try {
            const [fetchedActive, fetchedVersions] = await Promise.all([
                api.getThemeActiveVersion(dsId),
                api.getThemeVersions(dsId)
            ]);

            setActiveVersion(fetchedActive);
            setVersions(fetchedVersions);

            if (!currentViewedVersion || !fetchedVersions.find(v => v.id === currentViewedVersion.id)) {
                setCurrentViewedVersion(fetchedActive);
            } else {
                const updatedViewed = fetchedVersions.find(v => v.id === currentViewedVersion.id);
                if (updatedViewed) setCurrentViewedVersion(updatedViewed);
            }

        } catch (error) {
            console.error("Failed to fetch DesignSpace context data", error);
        } finally {
            setIsLoading(false);
        }
    }, [dsId, currentViewedVersion]);

    useEffect(() => {
        fetchData();
    }, [dsId]);

    const refreshVersions = async () => {
        await fetchData();
    };

    const switchVersion = (versionId: string) => {
        const found = versions.find(v => v.id === versionId);
        if (found) {
            setCurrentViewedVersion(found);
        }
    };

    const isReadOnly = activeVersion && currentViewedVersion
        ? activeVersion.id !== currentViewedVersion.id
        : false;

    return (
        <DesignSpaceContext.Provider value={{
            dsId,
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
        </DesignSpaceContext.Provider>
    );
};

export const useDesignSpace = () => {
    const context = useContext(DesignSpaceContext);
    if (!context) {
        throw new Error("useDesignSpace must be used within a DesignSpaceProvider");
    }
    return context;
};
