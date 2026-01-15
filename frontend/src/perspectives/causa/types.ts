/**
 * Domain-specific types for the Causal Perspective.
 * This ensures strict typing internal to the module.
 */

export interface CausalNode {
    id: string;
    label: string;
    type: 'factor' | 'system';
    // Future: status, confidence, evidence
}

export interface CausalLink {
    id: string;
    source: string;
    target: string;
    polarity: 'positive' | 'negative' | 'ambiguous';
    // Future: weight, status
}
