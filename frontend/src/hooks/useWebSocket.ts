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
    const isMounted = useRef(true);
    const retryCountRef = useRef(0);
    const MAX_RETRIES = 5;

    const connect = useCallback(async () => {
        if (!projectId) return;

        // Cleanup existing socket and timeout
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (socketRef.current) {
            // Unbind handler to prevent reconnect loop during intentional close
            socketRef.current.onclose = null;
            socketRef.current.close();
            socketRef.current = null;
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
            retryCountRef.current = 0; // Reset retries on successful connection
            if (isMounted.current) setIsConnected(true);
        };

        ws.onmessage = (event) => {
            if (!isMounted.current) return;
            try {
                const data = JSON.parse(event.data);
                setLastMessage(data);
            } catch (e) {
                console.error('WebSocket message parse error:', e);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket Disconnected');
            if (isMounted.current) setIsConnected(false);

            // Only reconnect if mounted and the close wasn't intentional
            if (isMounted.current) {
                if (retryCountRef.current < MAX_RETRIES) {
                    retryCountRef.current += 1;
                    // Exponential backoff: 1s, 2s, 4s, 8s, 16s... up to 30s
                    const jitter = Math.random() * 1000;
                    const backoff = Math.min(1000 * Math.pow(2, retryCountRef.current) + jitter, 30000);

                    console.log(`Scheduling reconnect attempt ${retryCountRef.current}/${MAX_RETRIES} in ${Math.round(backoff)}ms`);

                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, backoff);
                } else {
                    console.error('WebSocket Max Retries Exceeded. Stopping reconnection attempts.');
                }
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
            // Closing here will trigger onclose, which handles reconnect
            ws.close();
        };

    }, [projectId]);

    useEffect(() => {
        isMounted.current = true;
        connect();
        return () => {
            isMounted.current = false;
            if (socketRef.current) {
                socketRef.current.onclose = null; // Prevent reconnect
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
