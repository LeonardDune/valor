import type { ReactNode } from 'react';

/**
 * A Perspective provides a specific way to interact with the underlying Graph.
 * It defines how data is projected, what views are available, and what rules apply.
 */
export interface Perspective {
    id: string;
    name: string;
    description: string;

    /**
     * The React component that renders the shell/layout for this perspective.
     * Starts blank, will eventually manage the layout sessions.
     */
    Shell: () => ReactNode;
}
