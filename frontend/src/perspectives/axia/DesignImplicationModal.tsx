import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { api } from '@/services/api';
import { useAxiaSchema } from './hooks/useAxiaSchema';

interface DesignImplicationModalProps {
    /** URI van de Tessera waaraan de implicatie wordt gekoppeld (bijv. een CausalClaim of Factor) */
    tesseraUri: string | null;
    /** Leesbare naam van de Tessera — voor de dialog-titel */
    tesseraLabel: string;
    designSpaceId: string;
    onClose: () => void;
    onCreated: () => void;
}

export function DesignImplicationModal({
    tesseraUri,
    tesseraLabel,
    designSpaceId,
    onClose,
    onCreated,
}: DesignImplicationModalProps) {
    const { schema } = useAxiaSchema();
    const [valueTypeUri, setValueTypeUri] = useState('');
    const [polarityUri, setPolarityUri] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (!tesseraUri) {
            setValueTypeUri('');
            setPolarityUri('');
        }
    }, [tesseraUri]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!tesseraUri || !valueTypeUri || !polarityUri) return;
        setIsSaving(true);
        try {
            await api.createDesignImplication(designSpaceId, {
                tessera_uri: tesseraUri,
                value_type_uri: valueTypeUri,
                polarity_uri: polarityUri,
            });
            toast.success('Waarde-implicatie gekoppeld.');
            onCreated();
            onClose();
        } catch {
            toast.error('Koppelen mislukt.');
        } finally {
            setIsSaving(false);
        }
    };

    const valueTypes = schema?.value_types ?? [];
    const polarities = schema?.claim_polarities ?? [];

    return (
        <Dialog open={!!tesseraUri} onOpenChange={(open) => { if (!open) onClose(); }}>
            <DialogContent className="sm:max-w-[400px]">
                <DialogHeader>
                    <DialogTitle>Waarde-implicatie koppelen</DialogTitle>
                    <DialogDescription>
                        Koppel een waardetype aan <span className="font-medium">"{tesseraLabel}"</span>
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="grid gap-4 py-2">
                    <div className="grid gap-2">
                        <Label>Waardetype</Label>
                        <Select value={valueTypeUri} onValueChange={setValueTypeUri}>
                            <SelectTrigger>
                                <SelectValue placeholder="Kies een waardetype" />
                            </SelectTrigger>
                            <SelectContent>
                                {valueTypes.map((v) => (
                                    <SelectItem key={v.uri} value={v.uri}>
                                        {v.label_nl || v.label_en}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid gap-2">
                        <Label>Polariteit</Label>
                        <Select value={polarityUri} onValueChange={setPolarityUri}>
                            <SelectTrigger>
                                <SelectValue placeholder="Kies een polariteit" />
                            </SelectTrigger>
                            <SelectContent>
                                {polarities.map((p) => (
                                    <SelectItem key={p.uri} value={p.uri}>
                                        {p.label_nl || p.label_en}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={onClose} disabled={isSaving}>
                            Annuleren
                        </Button>
                        <Button type="submit" disabled={!valueTypeUri || !polarityUri || isSaving}>
                            {isSaving ? 'Opslaan...' : 'Koppelen'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
