/**
 * Domain-specific types for the Causal Perspective.
 * This ensures strict typing internal to the module.
 */

export type EpistemicStatus = 'Proposed' | 'Contested' | 'Accepted' | 'Rejected' | 'Reconsidered';

export interface CausalNode {
    id: string;
    label: string;
    type: 'factor' | 'system';
    role?: string; // e.g. 'middel', 'extern', 'criterium'
    description?: string;
    epistemicStatus?: EpistemicStatus;
    version_id?: string;
    inFeedbackLoop?: boolean;
}

export interface CausalLink {
    id: string;
    source: string;
    target: string;
    polarity: 'positive' | 'negative' | 'ambiguous';
    epistemicStatus?: EpistemicStatus;
    certainty?: number; // 0.0 - 1.0
    statement?: string;
    version_id?: string;
    evidence_text?: string;
    evidence_url?: string;
    threadCount?: number;
}
