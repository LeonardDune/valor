import { useCallback, useState } from 'react';
import * as htmlToImage from 'html-to-image';
import { jsPDF } from 'jspdf';

export interface ExportOptions {
    width?: number;
    height?: number;
    style?: any;
    element?: HTMLElement; // Allow targeting a specific element
}

interface UseDomExportReturn {
    exportAsPng: (filename: string, options?: ExportOptions) => Promise<void>;
    exportAsPdf: (filename: string, options?: ExportOptions) => Promise<void>;
    exportAsSvg: (filename: string, options?: ExportOptions) => Promise<void>;
    isExporting: boolean;
}

/**
 * A generic hook to export a DOM element as PNG, PDF, or SVG.
 * Uses html-to-image for rasterization/vectorization (supports modern CSS like oklch).
 */
export const useDomExport = (ref: React.RefObject<HTMLElement | null>): UseDomExportReturn => {
    const [isExporting, setIsExporting] = useState(false);

    // Filter Logic shared across all exporters
    // Note: html-to-image 'filter' option is powerful.
    const filterNode = (node: HTMLElement) => {
        // Ignore elements with specific class
        if (node.classList && node.classList.contains('no-export')) {
            return false;
        }
        return true;
    };

    const captureToDataUrl = useCallback(async (format: 'png' | 'svg' = 'png', options: ExportOptions = {}) => {
        const targetNode = options.element || ref.current;
        if (!targetNode) throw new Error('Reference element is null');

        const { element, ...configOptions } = options;

        const config = {
            cacheBust: true,
            backgroundColor: '#ffffff', // Ensure white background
            pixelRatio: 2, // High resolution
            filter: filterNode,
            ...configOptions
        };

        if (format === 'svg') {
            return await htmlToImage.toSvg(targetNode, config);
        }
        return await htmlToImage.toPng(targetNode, config);

    }, [ref]);

    const exportAsPng = useCallback(async (filename: string, options?: ExportOptions) => {
        setIsExporting(true);
        try {
            const dataUrl = await captureToDataUrl('png', options);
            const link = document.createElement('a');
            link.download = `${filename}.png`;
            link.href = dataUrl;
            link.click();
        } catch (error) {
            console.error('Export PNG failed', error);
        } finally {
            setIsExporting(false);
        }
    }, [captureToDataUrl]);

    const exportAsSvg = useCallback(async (filename: string, options?: ExportOptions) => {
        setIsExporting(true);
        try {
            const dataUrl = await captureToDataUrl('svg', options);
            const link = document.createElement('a');
            link.download = `${filename}.svg`;
            link.href = dataUrl;
            link.click();
        } catch (error) {
            console.error('Export SVG failed', error);
        } finally {
            setIsExporting(false);
        }
    }, [captureToDataUrl]);

    const exportAsPdf = useCallback(async (filename: string, options?: ExportOptions) => {
        setIsExporting(true);
        try {
            const dataUrl = await captureToDataUrl('png', options);

            // Load image to get dimensions
            const img = new Image();
            img.src = dataUrl;
            await new Promise((resolve) => { img.onload = resolve; });

            // PDF Setup
            const imgWidth = img.width;
            const imgHeight = img.height;

            // Create PDF with orientation based on aspect ratio
            const orientation = imgWidth > imgHeight ? 'l' : 'p';

            // Using mm units and A4 format
            const pdf = new jsPDF(orientation, 'mm', 'a4');
            const pageWidth = pdf.internal.pageSize.getWidth();
            const pageHeight = pdf.internal.pageSize.getHeight();

            // Calculate ratios to fit image on page
            const ratioX = pageWidth / imgWidth;
            const ratioY = pageHeight / imgHeight;
            const ratio = Math.min(ratioX, ratioY);

            // Center the image
            const finalWidth = imgWidth * ratio;
            const finalHeight = imgHeight * ratio;
            const x = (pageWidth - finalWidth) / 2;
            const y = (pageHeight - finalHeight) / 2;

            pdf.addImage(dataUrl, 'PNG', x, y, finalWidth, finalHeight);
            pdf.save(`${filename}.pdf`);

        } catch (error) {
            console.error('Export PDF failed', error);
        } finally {
            setIsExporting(false);
        }
    }, [captureToDataUrl]);

    return { exportAsPng, exportAsPdf, exportAsSvg, isExporting };
};
