export type ConversationScope = 'global' | 'view' | 'object';
export type PerspectiveType = 'CAUSA' | 'AXIA' | 'ACTOR' | 'PRAXIS';

export interface ConversationContext {
    scope: ConversationScope;
    perspective: PerspectiveType;
    contextId?: string; // ID of the object, view, or specific context
    agentId?: string;   // Specific agent to target (optional)
    label?: string;     // Display label for the context (e.g. "Factor X")
}

export interface ConversationMessage {
    id: string;
    thread_id: string;
    user_id?: string;
    content: string;
    role: 'user' | 'assistant';
    author_name?: string;
    created_at: string;
}

export interface ConversationThread {
    id: string;
    target_id?: string;
    topic: string;
    status: 'open' | 'closed' | 'archived' | 'active';
    created_at: string;
    updated_at?: string;
    message_count?: number;
}

export type Thread = ConversationThread;
