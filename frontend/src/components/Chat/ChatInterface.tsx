import React, { useRef, useEffect } from 'react';
import { api, type Claim, type AgentResponse } from '../../services/api';
import {
    ThreadPrimitive,
    ComposerPrimitive,
    MessagePrimitive,
    AssistantRuntimeProvider,
    useLocalRuntime,
    useAssistantApi,    // New
    useAssistantState,  // New
    type ChatModelAdapter,
    type ThreadMessage
} from "@assistant-ui/react";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import { Send, Shield, AlertTriangle } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import ReactMarkdown from 'react-markdown';

interface ChatInterfaceProps {
    topic: string;
    onClaimsUpdate: (claims: Claim[]) => void;
}

const MarkdownTextAdapter = (props: any) => <MarkdownTextPrimitive {...props} />;

const AgentBlock: React.FC<{ agent: AgentResponse }> = ({ agent }) => {
    const isNormative = agent.role_type === 'NORMATIVE';
    const bgColor = isNormative ? 'bg-purple-50/50' : 'bg-blue-50/50';
    const borderColor = isNormative ? 'border-purple-200' : 'border-blue-200';
    const textColor = isNormative ? 'text-purple-900' : 'text-blue-900';
    const Icon = isNormative ? AlertTriangle : Shield;

    return (
        <div className={`mb-4 rounded-lg border ${bgColor} ${borderColor} p-4 text-sm`}>
            <div className={`flex items-center gap-2 font-semibold mb-2 ${textColor}`}>
                <Icon className="w-4 h-4" />
                <span>{agent.agent_name}</span>
                <span className="text-xs opacity-70 px-2 py-0.5 rounded-full border border-current">
                    {agent.role_type || 'DESCRIPTIVE'}
                </span>
            </div>
            <div className="prose prose-sm max-w-none text-muted-foreground">
                <ReactMarkdown>{agent.reply}</ReactMarkdown>
            </div>
        </div>
    );
};

const MyMessage: React.FC = () => {
    const messageState = useAssistantState(state => state.message);
    const metadata = (messageState as any).metadata?.custom;
    const agentResponses = metadata?.agent_responses as AgentResponse[] | undefined;

    return (
        <MessagePrimitive.Root className="flex mb-4 w-full">
            <div className="flex w-full data-[role=user]:justify-end data-[role=assistant]:justify-start">
                <div className={`max-w-[85%] rounded-2xl shadow-sm text-sm leading-relaxed overflow-hidden 
                    data-[role=user]:bg-primary data-[role=user]:text-primary-foreground data-[role=user]:rounded-br-none data-[role=user]:p-4
                    data-[role=assistant]:bg-transparent data-[role=assistant]:text-foreground data-[role=assistant]:rounded-bl-none data-[role=assistant]:w-full`}
                >
                    {agentResponses ? (
                        <div className="flex flex-col gap-2 w-full">
                            {agentResponses.map((agent, step) => (
                                <AgentBlock key={step} agent={agent} />
                            ))}
                        </div>
                    ) : (
                        <div className="bg-muted p-4 rounded-2xl rounded-bl-none text-muted-foreground">
                            <MessagePrimitive.Content components={{ Text: MarkdownTextAdapter }} />
                        </div>
                    )}
                </div>
            </div>
        </MessagePrimitive.Root>
    )
}

const ChatInitializer: React.FC<{ topic: string, onClaimsUpdate: (claims: Claim[]) => void, conversationIdRef: React.MutableRefObject<string | undefined> }> = ({ topic, onClaimsUpdate, conversationIdRef }) => {
    const assistant = useAssistantApi();
    const threadMessagesLength = useAssistantState(state => state.thread.messages.length);
    const hasInitializedRef = useRef<string | null>(null);

    useEffect(() => {
        if (hasInitializedRef.current === topic) return;

        const initChat = async () => {
            hasInitializedRef.current = topic;
            try {
                // Initial greeting request
                const response = await api.chat(
                    `Ik wil graag aan de slag met het thema "${topic}". Heb je suggesties voor relevante factoren?`,
                    undefined,
                    topic
                );
                conversationIdRef.current = response.conversation_id;

                if (response.extracted_claims && response.extracted_claims.length > 0) {
                    onClaimsUpdate(response.extracted_claims);
                }

                // Append the initial greeting to the runtime
                assistant.thread().append({
                    role: "assistant",
                    content: [{ type: "text", text: response.reply }],
                    metadata: {
                        custom: {
                            agent_responses: response.agent_responses
                        }
                    }
                });
            } catch (error) {
                console.error("Initial chat error:", error);
                assistant.thread().append({
                    role: "assistant",
                    content: [{ type: "text", text: "Er is een fout opgetreden bij het verbinden met de agent." }]
                });
            }
        };

        // Only run if the thread is empty to avoid duplicates on re-renders if distinct from topic change
        if (threadMessagesLength === 0) {
            initChat();
        }
    }, [topic, assistant, onClaimsUpdate, conversationIdRef, threadMessagesLength]);

    return null;
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ topic, onClaimsUpdate }) => {
    const conversationIdRef = useRef<string | undefined>(undefined);

    const adapter: ChatModelAdapter = {
        run: async ({ messages }: { messages: readonly ThreadMessage[] }) => {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.content[0]?.type !== 'text') return { content: [] };

            const text = lastMessage.content[0].text;

            try {
                const response = await api.chat(text, conversationIdRef.current, topic);
                conversationIdRef.current = response.conversation_id;

                if (response.extracted_claims) {
                    onClaimsUpdate(response.extracted_claims);
                }

                return {
                    content: [{ type: "text", text: response.reply }],
                    metadata: {
                        custom: {
                            agent_responses: response.agent_responses
                        }
                    }
                };
            } catch (error) {
                console.error("Chat error:", error);
                return {
                    content: [{ type: "text", text: "Er is een fout opgetreden bij het verbinden met de agent." }],
                };
            }
        }
    };

    const runtime = useLocalRuntime(adapter);

    // Reset conversation ID when topic changes (handled by new instance of runtime usually, but safe to clear)
    useEffect(() => {
        conversationIdRef.current = undefined;
    }, [topic]);

    return (
        <div className="h-full w-full bg-background border-r border-border flex flex-col items-stretch">
            <AssistantRuntimeProvider runtime={runtime}>
                <ThreadPrimitive.Root className="flex flex-col h-full">
                    <ChatInitializer topic={topic} onClaimsUpdate={onClaimsUpdate} conversationIdRef={conversationIdRef} />
                    <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto p-4 scroll-smooth">
                        <ThreadPrimitive.Empty>
                            <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-8 text-center">
                                <p className="animate-pulse">Agent initialiseren...</p>
                            </div>
                        </ThreadPrimitive.Empty>

                        <ThreadPrimitive.Messages components={{ Message: MyMessage }} />
                    </ThreadPrimitive.Viewport>

                    <ComposerPrimitive.Root className="p-4 border-t border-border bg-background flex items-end gap-2">
                        <ComposerPrimitive.Input asChild>
                            <Textarea
                                placeholder="Stel een vraag..."
                                className="min-h-[2.5rem] max-h-[10rem] resize-none"
                                rows={1}
                            />
                        </ComposerPrimitive.Input>
                        <ComposerPrimitive.Send asChild>
                            <Button size="icon">
                                <Send className="h-4 w-4" />
                                <span className="sr-only">Verzenden</span>
                            </Button>
                        </ComposerPrimitive.Send>
                    </ComposerPrimitive.Root>
                </ThreadPrimitive.Root>
            </AssistantRuntimeProvider>
        </div>
    );
};

export default ChatInterface;
