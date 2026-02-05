/**
 * Domain-specific types for the Causal Perspective.
 * This ensures strict typing internal to the module.
 */

export interface CausalNode {
    id: string;
    label: string;
    type: 'factor' | 'system';
    role?: string; // e.g. 'middel', 'extern', 'criterium'
    description?: string;
    // Future: status, confidence, evidence
    version_id?: string;
}

export interface CausalLink {
    id: string;
    source: string;
    target: string;
    polarity: 'positive' | 'negative' | 'ambiguous';
    // Visualization properties (US-CAUSA-05/06)
    status?: 'proposed' | 'validated' | 'rejected';
    certainty?: number; // 0.0 - 1.0
    statement?: string;
    version_id?: string;
    threadCount?: number;
}
