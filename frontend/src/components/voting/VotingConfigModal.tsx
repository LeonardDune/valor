import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import type { VotingSessionConfig } from '../../types/session';

interface VotingConfigModalProps {
    isOpen: boolean;
    onClose: () => void;
    onStart: (config: VotingSessionConfig) => void;
    isLoading?: boolean;
}

export const VotingConfigModal: React.FC<VotingConfigModalProps> = ({
    isOpen,
    onClose,
    onStart,
    isLoading = false
}) => {
    const [dots, setDots] = useState<number>(3);
    const [timeLimit, setTimeLimit] = useState<number | ''>('');

    const handleStart = () => {
        onStart({
            dots_per_user: dots,
            time_limit: timeLimit === '' ? null : Number(timeLimit)
        });
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Start Stemsessie</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="dots" className="text-right">
                            Stemmen p.p.
                        </Label>
                        <Input
                            id="dots"
                            type="number"
                            value={dots}
                            onChange={(e) => setDots(Number(e.target.value))}
                            className="col-span-3"
                            min={1}
                            max={10}
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="time" className="text-right">
                            Tijdslimiet (min)
                        </Label>
                        <Input
                            id="time"
                            type="number"
                            value={timeLimit}
                            onChange={(e) => setTimeLimit(e.target.value === '' ? '' : Number(e.target.value))}
                            className="col-span-3"
                            placeholder="Optioneel"
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose} disabled={isLoading}>
                        Annuleren
                    </Button>
                    <Button onClick={handleStart} disabled={isLoading}>
                        {isLoading ? 'Starten...' : 'Start Stemmen'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};
