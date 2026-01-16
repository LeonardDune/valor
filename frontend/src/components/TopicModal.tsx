import React, { useState } from 'react';
import { Target } from 'lucide-react';

interface TopicModalProps {
    onSubmit: (topic: string) => void;
}

import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

const TopicModal: React.FC<TopicModalProps> = ({ onSubmit }) => {
    const [topic, setTopic] = useState('');
    const [open, setOpen] = useState(true);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (topic.trim()) {
            onSubmit(topic.trim());
            setOpen(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <div className="mx-auto w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                        <Target className="w-6 h-6 text-primary" />
                    </div>
                    <DialogTitle className="text-center text-xl">Nieuwe Sessie Starten</DialogTitle>
                    <DialogDescription className="text-center">
                        Definieer het centrale probleem of thema voor deze analyse.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4 pt-4">
                    <div className="space-y-2">
                        <Label>Centraal Thema / Probleem</Label>
                        <Textarea
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder="bijv. Te veel stikstof in het milieu"
                            className="min-h-[100px] resize-none"
                            autoFocus
                        />
                    </div>

                    <Button
                        type="submit"
                        disabled={!topic.trim()}
                        className="w-full"
                    >
                        Start Analyse
                    </Button>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default TopicModal;
