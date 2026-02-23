import type { Factor, Claim } from '../../../services/api';
import type { CausalNode, CausalLink } from '../types';

/**
 * Maps API Factor to Internal CausalNode
 */
export const mapFactorToNode = (factor: Factor): CausalNode => {
    return {
        id: factor.id,
        label: factor.name,
        type: factor.type === 'systeemelement' ? 'system' : 'factor',
        role: factor.type,
        description: factor.description,
        version_id: factor.version_id
    };
};

/**
 * Maps API Claim to Internal CausalLink
 */
export const mapClaimToLink = (claim: Claim): CausalLink => {
    // Map polarity string to strict type
    let polarity: 'positive' | 'negative' | 'ambiguous' = 'positive';
    if (claim.polarity === '-') polarity = 'negative';
    if (claim.polarity === '?') polarity = 'ambiguous';

    return {
        id: claim.id,
        source: claim.source_id || '',
        target: claim.target_id || '',
        polarity: polarity,
        // Using US-CAUSA-05 default logic for now until backend supports it
        status: 'validated',
        certainty: claim.confidence || 1.0,
        statement: claim.statement,
        version_id: claim.version_id,
        evidence_text: claim.evidence_text,
        evidence_url: claim.evidence_url
    };
};

export const mapFactors = (factors: Factor[]) => factors.map(mapFactorToNode);
export const mapClaims = (claims: Claim[]) => {
    return claims
        .filter(c => (c.source_id || c.source_node) && (c.target_id || c.target_node))
        .map(mapClaimToLink);
};
