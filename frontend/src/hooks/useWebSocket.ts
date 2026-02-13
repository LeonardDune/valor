import { useEffect, useRef, useState, useCallback } from 'react';
import { supabase } from '../lib/supabase';

const SOCKET_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export type WebSocketMessage = {
    type: string;
    payload: any;
};

export const useWebSocket = (projectId: string | null) => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
    const socketRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<any>(null);

    const connect = useCallback(async () => {
        if (!projectId) return;

        // cleanup previous
        if (socketRef.current) {
            socketRef.current.onclose = null; // Prevent reconnect trigger
            socketRef.current.close();
        }

        // Get Token
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token || '';

        // Pass token in query param (common pattern for WS auth)
        const wsUrl = `${SOCKET_URL}/${projectId}?token=${token}`;
        console.log('Connecting to WebSocket with Token...');

        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
            console.log('WebSocket Connected');
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setLastMessage(data);
            } catch (e) {
                console.error('WebSocket message parse error:', e);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket Disconnected');
            setIsConnected(false);
            // Reconnect logic with jitter
            const timeout = 1000 + Math.random() * 2000;
            reconnectTimeoutRef.current = setTimeout(() => {
                if (projectId) connect();
            }, timeout);
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
            ws.close();
        };

    }, [projectId]);

    useEffect(() => {
        connect();
        return () => {
            if (socketRef.current) {
                socketRef.current.onclose = null; // Prevent reconnect trigger
                socketRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [connect]);

    const sendMessage = useCallback((type: string, payload: any) => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type, payload }));
        }
    }, []);

    return { isConnected, lastMessage, sendMessage };
};
