import React from 'react';
import { Download, Loader2, FileImage, FileText, FileCode } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ExportMenuProps {
    onExportPng: () => void;
    onExportPdf: () => void;
    onExportSvg?: () => void;
    disabled?: boolean;
    isExporting?: boolean;
}

export const ExportMenu: React.FC<ExportMenuProps> = ({
    onExportPng,
    onExportPdf,
    onExportSvg,
    disabled = false,
    isExporting = false
}) => {
    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    disabled={disabled || isExporting}
                    title="Export"
                >
                    {isExporting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <Download className="h-4 w-4" />
                    )}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onExportPng} className="gap-2 cursor-pointer">
                    <FileImage className="h-4 w-4" />
                    <span>PNG</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onExportPdf} className="gap-2 cursor-pointer">
                    <FileText className="h-4 w-4" />
                    <span>PDF</span>
                </DropdownMenuItem>
                {onExportSvg && (
                    <DropdownMenuItem onClick={onExportSvg} className="gap-2 cursor-pointer">
                        <FileCode className="h-4 w-4" />
                        <span>SVG</span>
                    </DropdownMenuItem>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    );
};
