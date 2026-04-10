import { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';
import type { DesignImplicationCount } from '@/services/api';

interface NodePosition {
    id: string;
    x: number;
    y: number;
    width?: number;
    height?: number;
}

interface HeatmapOverlayProps {
    designSpaceId: string;
    /** ReactFlow instance — used to get node screen positions */
    rfInstance: any | null;
    /** Array of node ids present in the graph */
    nodeIds: string[];
}

/**
 * Legt een oranje intensiteitsoverlay over de Causa-nodes op basis van
 * het aantal axia:DesignImplication relaties per factor-URI.
 *
 * De overlay toont een knop om te activeren/deactiveren. Wanneer actief
 * worden de nodes ingekleurd op basis van hun implication-count
 * (0 = transparant, max = oranje-rood).
 */
export function HeatmapOverlay({ designSpaceId, rfInstance, nodeIds }: HeatmapOverlayProps) {
    const [active, setActive] = useState(false);
    const [implications, setImplications] = useState<DesignImplicationCount[]>([]);
    const [nodePositions, setNodePositions] = useState<NodePosition[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchImplications = useCallback(async () => {
        setLoading(true);
        try {
            const data = await api.getValueImplications(designSpaceId);
            setImplications(data);
        } catch {
            setImplications([]);
        } finally {
            setLoading(false);
        }
    }, [designSpaceId]);

    // Laad implications wanneer overlay geactiveerd wordt
    useEffect(() => {
        if (active) {
            fetchImplications();
        }
    }, [active, fetchImplications]);

    // Sync node posities vanuit rfInstance
    useEffect(() => {
        if (!active || !rfInstance) return;

        const updatePositions = () => {
            try {
                const rfNodes = rfInstance.getNodes?.() ?? [];
                const positions: NodePosition[] = rfNodes
                    .filter((n: any) => nodeIds.includes(n.id))
                    .map((n: any) => ({
                        id: n.id,
                        x: n.position.x,
                        y: n.position.y,
                        width: n.width ?? 140,
                        height: n.height ?? 100,
                    }));
                setNodePositions(positions);
            } catch {
                // rfInstance nog niet klaar
            }
        };

        updatePositions();
        // Periodiek updaten zodat posities meebewegen na drag
        const interval = setInterval(updatePositions, 500);
        return () => clearInterval(interval);
    }, [active, rfInstance, nodeIds]);

    // Normaliseer counts → intensiteit 0..1
    const maxCount = Math.max(1, ...implications.map((i) => i.implication_count));

    // Map factor_uri → count (gebruik het trailing segment als node-id lookup)
    const countByFactorUri = new Map<string, number>(
        implications.map((i) => [i.tessera_uri, i.implication_count])
    );

    // Zoek count voor een node-id: probeer directe match, dan URI-suffix match
    const countForNode = (nodeId: string): number => {
        if (countByFactorUri.has(nodeId)) return countByFactorUri.get(nodeId)!;
        // Factor-URI kan er zo uitzien: urn:valor:factor:abc123 — match suffix
        for (const [uri, count] of countByFactorUri) {
            if (uri.endsWith(nodeId) || uri.endsWith(`:${nodeId}`)) return count;
        }
        return 0;
    };

    const intensityToColor = (count: number): string => {
        if (count === 0) return 'transparent';
        const t = count / maxCount;
        // Oranje-gradient: licht oranje → oranje-rood
        const r = Math.round(255);
        const g = Math.round(165 * (1 - t * 0.7));
        const b = 0;
        const a = 0.15 + t * 0.45;
        return `rgba(${r},${g},${b},${a})`;
    };

    return (
        <>
            <Button
                size="sm"
                variant={active ? 'default' : 'outline'}
                className="h-8 px-3 text-xs"
                onClick={() => setActive((v) => !v)}
                disabled={loading}
                title="Waarde-implicaties heatmap"
            >
                {loading ? 'Laden...' : active ? 'Heatmap uit' : 'Heatmap aan'}
            </Button>

            {active && nodePositions.length > 0 && (
                <HeatmapLayer
                    nodePositions={nodePositions}
                    countForNode={countForNode}
                    intensityToColor={intensityToColor}
                    rfInstance={rfInstance}
                />
            )}
        </>
    );
}

interface HeatmapLayerProps {
    nodePositions: NodePosition[];
    countForNode: (nodeId: string) => number;
    intensityToColor: (count: number) => string;
    rfInstance: any | null;
}

function HeatmapLayer({ nodePositions, countForNode, intensityToColor, rfInstance }: HeatmapLayerProps) {
    // Zet ReactFlow-coördinaten om naar schermcoördinaten
    const getScreenPos = (x: number, y: number): { x: number; y: number } => {
        if (!rfInstance?.flowToScreenPosition) return { x, y };
        return rfInstance.flowToScreenPosition({ x, y });
    };

    return (
        <div
            className="absolute inset-0 pointer-events-none"
            style={{ zIndex: 10 }}
            aria-hidden
        >
            {nodePositions.map((node) => {
                const count = countForNode(node.id);
                const color = intensityToColor(count);
                if (color === 'transparent') return null;

                const w = node.width ?? 140;
                const h = node.height ?? 100;

                // node.position is center-based (ReactFlow nodeOrigin [0.5, 0.5])
                const screenPos = getScreenPos(node.x - w / 2, node.y - h / 2);

                return (
                    <div
                        key={node.id}
                        style={{
                            position: 'absolute',
                            left: screenPos.x,
                            top: screenPos.y,
                            width: w,
                            height: h,
                            backgroundColor: color,
                            borderRadius: 6,
                            transition: 'background-color 0.3s',
                            boxShadow: `0 0 12px 4px ${color}`,
                        }}
                    />
                );
            })}
        </div>
    );
}
