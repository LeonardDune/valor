import { useState, useEffect } from 'react';
import type { CausalNode, CausalLink } from '../types';

/**
 * Detecteert feedback-loops (cycli) in het causale model via DFS.
 * Geeft een Set terug van node-IDs die deel uitmaken van een cyclus.
 * Detectie wordt asynchroon uitgevoerd (niet-blokkerend) na elke mutatie.
 */
export const useFeedbackLoopDetection = (
    nodes: CausalNode[],
    links: CausalLink[]
): Set<string> => {
    const [loopNodeIds, setLoopNodeIds] = useState<Set<string>>(new Set());

    useEffect(() => {
        if (nodes.length === 0) {
            setLoopNodeIds(new Set());
            return;
        }

        // Voer detectie uit buiten de render-cyclus
        const timeoutId = setTimeout(() => {
            const result = detectFeedbackLoops(nodes, links);
            setLoopNodeIds(result);
        }, 0);

        return () => clearTimeout(timeoutId);
    }, [nodes, links]);

    return loopNodeIds;
};

/**
 * Bouwt een adjacency list en detecteert cycli via DFS.
 * Geeft een Set terug van alle node-IDs die in een cyclus zitten.
 */
function detectFeedbackLoops(nodes: CausalNode[], links: CausalLink[]): Set<string> {
    const nodeIds = new Set(nodes.map(n => n.id));

    // Bouw adjacency list
    const adjacency = new Map<string, string[]>();
    for (const node of nodes) {
        adjacency.set(node.id, []);
    }
    for (const link of links) {
        if (nodeIds.has(link.source) && nodeIds.has(link.target)) {
            adjacency.get(link.source)?.push(link.target);
        }
    }

    const inCycle = new Set<string>();
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    // DFS vanuit elke node
    for (const nodeId of nodeIds) {
        if (!visited.has(nodeId)) {
            dfs(nodeId, adjacency, visited, recursionStack, inCycle);
        }
    }

    return inCycle;
}

function dfs(
    nodeId: string,
    adjacency: Map<string, string[]>,
    visited: Set<string>,
    recursionStack: Set<string>,
    inCycle: Set<string>
): void {
    visited.add(nodeId);
    recursionStack.add(nodeId);

    const neighbors = adjacency.get(nodeId) || [];
    for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
            dfs(neighbor, adjacency, visited, recursionStack, inCycle);
        } else if (recursionStack.has(neighbor)) {
            // Cyclus gevonden: markeer alle nodes in de huidige recursie-stack
            // die deel uitmaken van de cyclus
            markCycleNodes(neighbor, nodeId, adjacency, inCycle);
        }
    }

    recursionStack.delete(nodeId);
}

/**
 * Markeert alle nodes in een cyclus van `cycleStart` terug naar zichzelf via `cycleEnd`.
 */
function markCycleNodes(
    cycleStart: string,
    cycleEnd: string,
    adjacency: Map<string, string[]>,
    inCycle: Set<string>
): void {
    // Zoek het pad van cycleStart naar cycleEnd via BFS/DFS en markeer alle nodes
    const pathNodes = findCycleNodes(cycleStart, cycleEnd, adjacency);
    for (const nodeId of pathNodes) {
        inCycle.add(nodeId);
    }
    inCycle.add(cycleStart);
    inCycle.add(cycleEnd);
}

function findCycleNodes(
    start: string,
    end: string,
    adjacency: Map<string, string[]>
): Set<string> {
    const result = new Set<string>();
    const stack: string[] = [start];
    const parent = new Map<string, string | null>([[start, null]]);

    while (stack.length > 0) {
        const current = stack.pop()!;
        if (current === end) {
            // Herstel pad
            let node: string | null = current;
            while (node !== null) {
                result.add(node);
                node = parent.get(node) ?? null;
            }
            break;
        }
        for (const neighbor of adjacency.get(current) || []) {
            if (!parent.has(neighbor)) {
                parent.set(neighbor, current);
                stack.push(neighbor);
            }
        }
    }

    return result;
}
