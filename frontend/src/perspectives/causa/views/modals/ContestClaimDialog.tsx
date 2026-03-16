import React, { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";

interface ContestClaimDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    claimLabel: string;
    onSubmit: (relationType: string, toelichting: string) => Promise<void>;
}

export const ContestClaimDialog: React.FC<ContestClaimDialogProps> = ({
    open,
    onOpenChange,
    claimLabel,
    onSubmit,
}) => {
    const [relationType, setRelationType] = useState('undermines');
    const [toelichting, setToelichting] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            await onSubmit(relationType, toelichting);
            handleClose();
        } catch (error) {
            console.error('Betwisting mislukt', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleClose = () => {
        setRelationType('undermines');
        setToelichting('');
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[420px]">
                <DialogHeader>
                    <DialogTitle>Claim betwisten</DialogTitle>
                </DialogHeader>
                <p className="text-sm text-muted-foreground">
                    <span className="font-medium text-foreground">{claimLabel}</span>
                </p>
                <form onSubmit={handleSubmit} className="space-y-4 pt-2">
                    <div className="space-y-2">
                        <Label htmlFor="relatie-type">Type bezwaar</Label>
                        <Select value={relationType} onValueChange={setRelationType}>
                            <SelectTrigger id="relatie-type">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="undermines">Ondermijnt (undermines)</SelectItem>
                                <SelectItem value="qualifies">Kwalificeert (qualifies)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="toelichting">Toelichting</Label>
                        <Textarea
                            id="toelichting"
                            placeholder="Beschrijf je bezwaar..."
                            value={toelichting}
                            onChange={(e) => setToelichting(e.target.value)}
                            rows={3}
                        />
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
                            Annuleren
                        </Button>
                        <Button type="submit" variant="destructive" disabled={isSubmitting}>
                            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Betwisten
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};
