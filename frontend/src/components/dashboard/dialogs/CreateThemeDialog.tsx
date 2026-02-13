import React, { useState } from 'react';
import { useCreateTheme } from '@/hooks/queries/useThemes';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from 'sonner';

interface CreateThemeDialogProps {
    projectId: string;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
    trigger?: React.ReactNode;
    onSuccess?: () => void;
}

export const CreateThemeDialog: React.FC<CreateThemeDialogProps> = ({
    projectId,
    open,
    onOpenChange,
    trigger,
    onSuccess
}) => {
    const [internalOpen, setInternalOpen] = useState(false);
    const isControlled = open !== undefined;
    const isOpen = isControlled ? open : internalOpen;
    const setIsOpen = isControlled ? onOpenChange! : setInternalOpen;

    const [name, setName] = useState('');
    const [desc, setDesc] = useState('');
    const createMutation = useCreateTheme();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name) return;

        createMutation.mutate({ projectId, name, description: desc }, {
            onSuccess: () => {
                setIsOpen(false);
                setName('');
                setDesc('');
                toast.success("Thema succesvol toegevoegd!");
                if (onSuccess) onSuccess();
            },
            onError: (error) => {
                console.error("Failed to create theme", error);
                toast.error("Kon thema niet toevoegen.");
            }
        });
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Nieuw Thema Toevoegen</DialogTitle>
                    <DialogDescription>
                        Voeg een specifiek thema of probleem toe aan dit project.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="theme-name">Naam</Label>
                        <Input
                            id="theme-name"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="Bijv. Sneeuwoverlast"
                            autoFocus
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="theme-desc">Omschrijving</Label>
                        <Textarea
                            id="theme-desc"
                            value={desc}
                            onChange={e => setDesc(e.target.value)}
                            placeholder="Wat gaan we onderzoeken?"
                            rows={3}
                        />
                    </div>
                    <DialogFooter>
                        <Button type="submit" disabled={!name || createMutation.isPending}>
                            {createMutation.isPending ? "Bezig..." : "Aanmaken"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};
