import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MousePointer2 } from "lucide-react";
interface Cursor {
    x: number; // 0-1 normalized
    y: number; // 0-1 normalized
    userId: string;
    lastActive: number;
    color: string;
    targetNodeId?: string; // If focusing a node
}

interface PresenceLayerProps {
    projectId: string;
    currentUserId?: string;
    websocket: {
        lastMessage: any;
        sendMessage: (type: string, payload: any) => void;
    };
    containerRef: React.RefObject<HTMLDivElement | null>;
    nodes: any[]; // Nodes with current x,y positions (from local simulation)
    viewport?: { x: number; y: number; zoom: number }; // ReactFlow Viewport
}

// Tailwind colors from the design system (index.css)
// Tailwind colors from the design system (index.css)
// We define full class strings so Tailwind JIT detects them.
const COLOR_MAPS = [
    { text: 'text-chart-1', bg: 'bg-chart-1' },
    { text: 'text-chart-2', bg: 'bg-chart-2' },
    { text: 'text-chart-3', bg: 'bg-chart-3' },
    { text: 'text-chart-4', bg: 'bg-chart-4' },
    { text: 'text-chart-5', bg: 'bg-chart-5' },
    { text: 'text-blue-500', bg: 'bg-blue-500' },
    { text: 'text-green-600', bg: 'bg-green-600' },
    { text: 'text-amber-500', bg: 'bg-amber-500' },
    { text: 'text-purple-500', bg: 'bg-purple-500' },
    { text: 'text-pink-500', bg: 'bg-pink-500' }
];

const getHashIndex = (userId: string) => {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
        hash = userId.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash) % COLOR_MAPS.length;
};

export const PresenceLayer: React.FC<PresenceLayerProps> = ({ websocket, containerRef, currentUserId, nodes, viewport = { x: 0, y: 0, zoom: 1 } }) => {
    const [cursors, setCursors] = useState<Map<string, Cursor>>(new Map());
    const throttleRef = useRef<number>(0);

    // 1. Handle Outgoing Mouse Movements (Throttle 50ms)
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const handleMouseMove = (e: MouseEvent) => {
            const now = Date.now();
            if (now - throttleRef.current < 50) return;
            throttleRef.current = now;

            const rect = container.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;

            if (x >= 0 && x <= 1 && y >= 0 && y <= 1) {
                // Determine if hovering a node? 
                // That logic is usually in the Graph View (d3 hover).
                // Shell.tsx should handle "Node Hover" and call send("NODE_FOCUS")
                // Here we just send raw cursor for general presence.
                websocket.sendMessage('CURSOR', { x, y, user_id: currentUserId || 'anon' });
            }
        };

        container.addEventListener('mousemove', handleMouseMove);
        return () => container.removeEventListener('mousemove', handleMouseMove);
    }, [containerRef, websocket, currentUserId]);

    // 2. Handle Incoming Messages
    useEffect(() => {
        if (!websocket.lastMessage) return;
        const msg = websocket.lastMessage;

        const updateCursor = (userId: string, data: Partial<Cursor>) => {
            if (userId === currentUserId) return;
            setCursors(prev => {
                const newMap = new Map(prev);
                // We don't store color string anymore, we derive it from ID on render
                // But for compatibility with existing interface if needed, or just remove 'color' from state object logic
                // The interface `Cursor` on line 5 has `color: string`. We technically don't need to store it if it's deterministic.
                // But let's keep the object shape simple.
                // Actually, let's just ignore the `color` property in the state and compute it.

                const existing = newMap.get(userId) || {
                    userId, x: 0.5, y: 0.5, lastActive: 0, color: '' // dummy
                };
                newMap.set(userId, { ...existing, ...data, lastActive: Date.now() });
                return newMap;
            });
        };

        if (msg.type === 'CURSOR') {
            const { user_id, x, y } = msg.payload;
            updateCursor(user_id, { x, y });
        }
        else if (msg.type === 'NODE_FOCUS') {
            const { nodeId, user_id } = msg.payload;
            if (user_id) {
                updateCursor(user_id, { targetNodeId: nodeId });
            }
        }

    }, [websocket.lastMessage, currentUserId]);

    // 3. Cleanup Zombies
    useEffect(() => {
        const interval = setInterval(() => {
            const now = Date.now();
            setCursors(prev => {
                let changed = false;
                const newMap = new Map(prev);
                newMap.forEach((cursor, id) => {
                    if (now - cursor.lastActive > 10000) {
                        newMap.delete(id);
                        changed = true;
                    }
                });
                return changed ? newMap : prev;
            });
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    // Helper to get render position
    const getPosition = (cursor: Cursor) => {
        if (cursor.targetNodeId) {
            // Find node in LOCAL simulation (World Coords)
            const node = nodes.find(n => n.id === cursor.targetNodeId);
            if (node) {
                // 1. Get Node World Position
                const wx = node.x;
                const wy = node.y;

                // 2. Apply ReactFlow Viewport Transform
                // screen = world * zoom + pan
                const sx = wx * viewport.zoom + viewport.x;
                const sy = wy * viewport.zoom + viewport.y;

                // 3. Return absolute pixels for exact placement
                return { left: `${sx}px`, top: `${sy}px`, scale: 1.2 };
            }
        }
        // Fallback or Normal Cursor (Percentage of Container)
        return { left: `${cursor.x * 100}%`, top: `${cursor.y * 100}%`, scale: 1 };
    };

    return (
        <div className="absolute inset-0 pointer-events-none z-50 overflow-hidden">
            <AnimatePresence>
                {Array.from(cursors.values()).map(cursor => {
                    const pos = getPosition(cursor);
                    const colorIndex = getHashIndex(cursor.userId);
                    const colors = COLOR_MAPS[colorIndex];

                    return (
                        <motion.div
                            key={cursor.userId}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{
                                opacity: 1,
                                scale: pos.scale,
                                left: pos.left,
                                top: pos.top
                            }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.2, type: "spring" }} // Smoother
                            className="absolute flex flex-col items-start"
                            style={{ transform: 'translate(-50%, -50%)', zIndex: 100 }}
                        >
                            {/* Cursor Icon or Node Badge */}
                            {cursor.targetNodeId ? (
                                <div className={`text-primary-foreground text-xs px-2 py-1 rounded-full shadow-lg border-2 border-white font-bold flex items-center gap-1 ${colors.bg}`}>
                                    <Avatar className="h-4 w-4 border border-white">
                                        <AvatarFallback className="text-[8px] bg-muted text-muted-foreground">{cursor.userId.substring(0, 2).toUpperCase()}</AvatarFallback>
                                    </Avatar>
                                    {cursor.userId}
                                </div>
                            ) : (
                                <>
                                    <MousePointer2
                                        className={`h-5 w-5 fill-current ${colors.text} filter drop-shadow-md`}
                                    />
                                    <div
                                        className={`absolute left-3 top-3`}
                                    >
                                        <Avatar className={`h-6 w-6 border-2 border-white shadow-md ${colors.bg}`}>
                                            <AvatarFallback className="text-[9px] text-white bg-transparent font-bold">{cursor.userId.substring(0, 2).toUpperCase()}</AvatarFallback>
                                        </Avatar>
                                    </div>
                                </>
                            )}
                        </motion.div>
                    );
                })}
            </AnimatePresence>
        </div>
    );
};
