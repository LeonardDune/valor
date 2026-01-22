import React, { useRef, useEffect } from 'react';
import { api, type Claim } from '../../services/api';
import {
    ThreadPrimitive,
    ComposerPrimitive,
    MessagePrimitive,
    AssistantRuntimeProvider,
    useLocalRuntime,
    useThreadRuntime,
    type ChatModelAdapter,
    type ThreadMessage
} from "@assistant-ui/react";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import { Send } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatInterfaceProps {
    topicLabel: string;
    topicId?: string;
    onClaimsUpdate: (claims: Claim[]) => void;
}

const MarkdownTextAdapter = (props: any) => <MarkdownTextPrimitive {...props} />;

const MyMessage: React.FC = () => {
    return (
        <MessagePrimitive.Root className="flex mb-4 w-full">
            <div className="flex w-full data-[role=user]:justify-end data-[role=assistant]:justify-start">
                <div className="max-w-[85%] rounded-2xl p-4 shadow-sm text-sm leading-relaxed overflow-hidden data-[role=user]:bg-primary data-[role=user]:text-primary-foreground data-[role=user]:rounded-br-none data-[role=assistant]:bg-muted data-[role=assistant]:text-muted-foreground data-[role=assistant]:rounded-bl-none">
                    <MessagePrimitive.Content components={{ Text: MarkdownTextAdapter }} />
                </div>
            </div>
        </MessagePrimitive.Root>
    )
}

const ChatInitializer: React.FC<{
    topicLabel: string,
    topicId?: string,
    onClaimsUpdate: (claims: Claim[]) => void,
    conversationIdRef: React.MutableRefObject<string | undefined>
}> = ({ topicLabel, topicId, onClaimsUpdate, conversationIdRef }) => {
    const thread = useThreadRuntime();
    const hasInitializedRef = useRef<string | null>(null);

    useEffect(() => {
        const initKey = topicId || topicLabel;
        if (hasInitializedRef.current === initKey) return;

        const initChat = async () => {
            hasInitializedRef.current = initKey;
            try {
                // For the API we prefer topicId if available
                const apiTopic = topicId || topicLabel;

                // Initial greeting request - using the friendly label
                const response = await api.chat(
                    `Ik wil graag aan de slag met het thema "${topicLabel}". Heb je suggesties voor relevante factoren?`,
                    undefined,
                    apiTopic
                );
                conversationIdRef.current = response.conversation_id;

                if (response.extracted_claims && response.extracted_claims.length > 0) {
                    onClaimsUpdate(response.extracted_claims);
                }

                let replyText = response.reply;
                if (response.agent_responses && response.agent_responses.length > 0) {
                    replyText = response.agent_responses.map(agent => (
                        `### ${agent.agent_name}\n${agent.reply}`
                    )).join("\n\n---\n\n");
                }

                // Append the initial greeting to the runtime
                thread.append({
                    role: "assistant",
                    content: [{ type: "text", text: replyText }]
                });
            } catch (error) {
                console.error("Initial chat error:", error);
                thread.append({
                    role: "assistant",
                    content: [{ type: "text", text: "Er is een fout opgetreden bij het verbinden met de agent." }]
                });
            }
        };

        // Only run if the thread is empty to avoid duplicates on re-renders if distinct from topic change
        if (thread.getState().messages.length === 0) {
            initChat();
        }
    }, [topicLabel, topicId, thread, onClaimsUpdate, conversationIdRef]);

    return null;
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ topicLabel, topicId, onClaimsUpdate }) => {
    const conversationIdRef = useRef<string | undefined>(undefined);

    const adapter: ChatModelAdapter = {
        run: async ({ messages }: { messages: readonly ThreadMessage[] }) => {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.content[0]?.type !== 'text') return { content: [] };

            const text = lastMessage.content[0].text;

            try {
                const apiTopic = topicId || topicLabel;
                const response = await api.chat(text, conversationIdRef.current, apiTopic);
                conversationIdRef.current = response.conversation_id;

                if (response.extracted_claims) {
                    onClaimsUpdate(response.extracted_claims);
                }

                let replyText = response.reply;
                if (response.agent_responses && response.agent_responses.length > 0) {
                    replyText = response.agent_responses.map(agent => (
                        `### ${agent.agent_name}\n${agent.reply}`
                    )).join("\n\n---\n\n");
                }

                return {
                    content: [{ type: "text", text: replyText }],
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

    // Reset conversation ID when topic changes
    useEffect(() => {
        conversationIdRef.current = undefined;
    }, [topicId, topicLabel]);

    return (
        <div className="h-full w-full bg-background border-r border-border flex flex-col items-stretch">
            <AssistantRuntimeProvider runtime={runtime}>
                <ThreadPrimitive.Root className="flex flex-col h-full">
                    <ChatInitializer
                        topicLabel={topicLabel}
                        topicId={topicId}
                        onClaimsUpdate={onClaimsUpdate}
                        conversationIdRef={conversationIdRef}
                    />
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
