export type ConversationScope = 'global' | 'view' | 'object';
export type PerspectiveType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

export interface ConversationContext {
    scope: ConversationScope;
    perspective: PerspectiveType;
    contextId?: string; // ID of the object, view, or specific context
    agentId?: string;   // Specific agent to target (optional)
    label?: string;     // Display label for the context (e.g. "Factor X")
}
