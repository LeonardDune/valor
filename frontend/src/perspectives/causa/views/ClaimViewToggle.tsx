import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { ClaimViewType } from "@/services/api";

interface ClaimViewToggleProps {
    value: ClaimViewType | null;
    onChange: (value: ClaimViewType | null) => void;
}

export const ClaimViewToggle = ({ value, onChange }: ClaimViewToggleProps) => {
    const handleChange = (val: string) => {
        if (!val || val === 'all') {
            onChange(null);
        } else {
            onChange(val as ClaimViewType);
        }
    };

    return (
        <ToggleGroup
            type="single"
            size="sm"
            variant="outline"
            value={value ?? 'all'}
            onValueChange={handleChange}
            className="h-8"
        >
            <ToggleGroupItem value="all" className="h-8 px-3 text-xs">
                Alles
            </ToggleGroupItem>
            <ToggleGroupItem value="AsIsType" className="h-8 px-3 text-xs">
                As-is
            </ToggleGroupItem>
            <ToggleGroupItem value="ToBeType" className="h-8 px-3 text-xs">
                To-be
            </ToggleGroupItem>
        </ToggleGroup>
    );
};
