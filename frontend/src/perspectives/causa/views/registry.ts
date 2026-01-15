import type { FunctionComponent } from 'react';

/**
 * Registry of available views within the Causal Perspective.
 * Currently empty, will hold 'cld', 'list', 'matrix', etc.
 */
export const ViewRegistry: Record<string, FunctionComponent<any>> = {
    // To be populated:
    // 'cld': CLDView,
};
