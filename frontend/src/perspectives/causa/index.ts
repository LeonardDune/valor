import type { Perspective } from '../types';

export const CausalPerspective: Perspective = {
    id: 'causa',
    name: 'Causal Analyst',
    description: 'Analyze cause-and-effect relationships with strict validation.',

    // Placeholder - will be implemented in subsequent US
    // Shell: () => null, // We updated the Interface to allow Props? No, we need to fix this.
    // For now, we export the Shell separately and the Workspace will need to import it explicitly
    // or we wrap it.
    Shell: () => null, // Keeping this null for now to avoid breaking strict type if it expects no props
};

export { CausaShell } from './Shell';


export * from './views/registry';
export * from './layout/session';
export * from './layout/runner';
export * from './views/CLDView';
