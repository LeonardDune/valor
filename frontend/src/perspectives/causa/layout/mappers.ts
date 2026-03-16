import type { Factor, Claim } from '../../../services/api';
import type { CausalNode, CausalLink, EpistemicStatus } from '../types';

const VALID_EPISTEMIC_STATUSES: EpistemicStatus[] = ['Proposed', 'Contested', 'Accepted', 'Rejected', 'Reconsidered'];

function normalizeEpistemicStatus(raw?: string): EpistemicStatus {
    if (!raw) return 'Proposed';
    const normalized = raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase() as EpistemicStatus;
    return VALID_EPISTEMIC_STATUSES.includes(normalized) ? normalized : 'Proposed';
}

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
        epistemicStatus: normalizeEpistemicStatus(factor.epistemic_status),
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
        epistemicStatus: normalizeEpistemicStatus(claim.status),
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
