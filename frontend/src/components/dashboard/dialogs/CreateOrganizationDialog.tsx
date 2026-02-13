import React, { useState } from 'react';
import { useCreateOrganization } from '@/hooks/queries/useOrganizations';
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

interface CreateOrganizationDialogProps {
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
    trigger?: React.ReactNode;
    onSuccess?: () => void;
}

export const CreateOrganizationDialog: React.FC<CreateOrganizationDialogProps> = ({
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
    const createMutation = useCreateOrganization();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        createMutation.mutate({ name, description: desc }, {
            onSuccess: () => {
                setIsOpen(false);
                setName('');
                setDesc('');
                toast.success("Organisatie aangemaakt!");
                if (onSuccess) onSuccess();
            },
            onError: (error) => {
                console.error("Failed to create org", error);
                toast.error("Kon organisatie niet aanmaken.");
            }
        });
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Nieuwe Organisatie</DialogTitle>
                    <DialogDescription>
                        Maak een nieuwe organisatie aan om projecten en gebruikers te beheren.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="org-name">Naam</Label>
                        <Input
                            id="org-name"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="Bijv. Gemeente Amsterdam"
                            autoFocus
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="org-desc">Omschrijving</Label>
                        <Textarea
                            id="org-desc"
                            value={desc}
                            onChange={e => setDesc(e.target.value)}
                            placeholder="Beschrijving van de organisatie..."
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
