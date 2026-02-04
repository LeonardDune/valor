export type ConversationScope = 'global' | 'view' | 'object';
export type PerspectiveType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

export interface ConversationContext {
    scope: ConversationScope;
    perspective: PerspectiveType;
    contextId?: string; // ID of the object, view, or specific context
    agentId?: string;   // Specific agent to target (optional)
    label?: string;     // Display label for the context (e.g. "Factor X")
}

export interface Thread {
    id: string;
    topic: string;
    status: 'active' | 'archived' | 'closed';
    created_at: string;
    target_id?: string; // Polymorphic reference
}

export interface ConversationMessage {
    id: string;
    content: string;
    created_at: string;
    user_id: string;
    author_name?: string;
}
