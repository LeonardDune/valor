import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot } from 'lucide-react';
import { api } from '../../services/api';
import type { Claim } from '../../services/api';

interface Message {
    role: 'user' | 'agent';
    content: string;
}

interface ChatInterfaceProps {
    onClaimsUpdate: (claims: Claim[]) => void;
    topic: string | null;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onClaimsUpdate, topic }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | undefined>(undefined);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const hasInitialized = useRef(false);

    // Initial Active Greeting when topic is set
    useEffect(() => {
        if (topic && !hasInitialized.current) {
            hasInitialized.current = true;
            const initChat = async () => {
                setLoading(true);
                try {
                    const response = await api.chat(
                        `[SYSTEM_START] Het thema is: "${topic}". Geef een korte introductie en doe 3 suggesties voor concrete factoren om mee te beginnen. (Belangrijk: leg nog geen verbindingen in de data en voeg nog geen factoren toe, geef ze alleen als suggestie in tekst zodat de gebruiker zelf kan kiezen).`,
                        undefined,
                        topic
                    );
                    setConversationId(response.conversation_id);
                    setMessages([{ role: 'agent', content: response.reply }]);
                } catch (error) {
                    console.error("Failed to init chat:", error);
                    setMessages([{ role: 'agent', content: "Hoi! Ik ben klaar om te beginnen. Wat is je eerste ingeving over dit thema?" }]);
                } finally {
                    setLoading(false);
                }
            };
            initChat();
        }
    }, [topic]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [input]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [messages]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e as any);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = input.trim();
        setInput('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';

        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        try {
            const response = await api.chat(userMsg, conversationId, topic || undefined);
            setConversationId(response.conversation_id);
            setMessages(prev => [...prev, { role: 'agent', content: response.reply }]);

            if (response.extracted_claims.length > 0) {
                onClaimsUpdate(response.extracted_claims);
            }
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'agent', content: "Excuus, er is een fout opgetreden bij de verbinding met de server." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white rounded-xl shadow-sm border border-slate-200">
            <div className="p-4 border-b border-slate-100 bg-slate-50 rounded-t-xl">
                <h2 className="font-semibold text-slate-700 flex items-center gap-2">
                    <Bot className="w-5 h-5 text-indigo-600" />
                    CAUSA Agent
                </h2>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-br-none'
                            : 'bg-slate-100 text-slate-800 rounded-bl-none'
                            }`}>
                            {msg.role === 'agent' ? (
                                <div className="prose prose-sm">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                            ) : (
                                <p className="whitespace-pre-wrap">{msg.content}</p>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-100 rounded-2xl p-4 rounded-bl-none animate-pulse">
                            <span className="text-slate-400">Aan het denken...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSubmit} className="p-4 border-t border-slate-100">
                <div className="relative flex items-end gap-2 bg-slate-50 border-slate-200 border rounded-xl focus-within:ring-2 focus-within:ring-indigo-500 focus-within:bg-white transition-all shadow-sm pr-2">
                    <textarea
                        ref={textareaRef}
                        rows={1}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Typ je causale bewering of argument..."
                        className="w-full pl-4 py-3 bg-transparent border-none focus:outline-none resize-none min-h-[48px] max-h-[200px] text-sm overflow-y-auto"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || loading}
                        className="mb-1.5 p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ChatInterface;
