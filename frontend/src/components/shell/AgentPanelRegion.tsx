import React from 'react';
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from '@radix-ui/react-accordion';
import { cn } from '@/lib/utils';
import { Panel } from '@/design-system/primitives/Panel';
import { ActivityFeed } from '@/components/dashboard/ActivityFeed';

// Placeholder for other agents
const PlaceholderAgent = ({ name }: { name: string }) => (
    <div className="p-4 text-sm text-muted-foreground italic">
        {name} interface laden...
    </div>
);

export const AgentPanelRegion: React.FC<{ className?: string }> = ({ className }) => {
    return (
        <Panel variant="plain" padding="none" className={cn("flex flex-col h-full border-l border-border-standard bg-background-secondary", className)}>
            <div className="p-4 font-bold text-foreground border-b border-border">
                Agent Samenwerking
            </div>
            <Accordion type="multiple" defaultValue={['proposals']} className="flex-1 overflow-y-auto w-full">

                <AccordionItem value="proposals" className="border-b border-border">
                    <AccordionTrigger className="w-full flex items-center justify-between p-4 text-sm font-medium text-foreground hover:bg-muted/50 transition-all">
                        Activiteiten & Voorstellen
                        {/* Add chevron icon here if desired */}
                    </AccordionTrigger>
                    <AccordionContent className="bg-background-tertiary">
                        <ActivityFeed />
                    </AccordionContent>
                </AccordionItem>

                <AccordionItem value="causa" className="border-b border-border-subtle">
                    <AccordionTrigger className="w-full flex items-center justify-between p-4 text-sm font-medium text-text-primary hover:bg-white/5">
                        Causal Analyst (CAUSA)
                    </AccordionTrigger>
                    <AccordionContent className="bg-background-tertiary">
                        <PlaceholderAgent name="CAUSA" />
                    </AccordionContent>
                </AccordionItem>

                <AccordionItem value="themis" className="border-b border-border-subtle">
                    <AccordionTrigger className="w-full flex items-center justify-between p-4 text-sm font-medium text-text-primary hover:bg-white/5">
                        Legal Guardian (THEMIS)
                    </AccordionTrigger>
                    <AccordionContent className="bg-background-tertiary">
                        <PlaceholderAgent name="THEMIS" />
                    </AccordionContent>
                </AccordionItem>

            </Accordion>
        </Panel>
    );
};
