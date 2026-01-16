/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                canvas: {
                    DEFAULT: 'var(--color-canvas-default)',
                },
                panel: {
                    DEFAULT: 'var(--color-panel-default)',
                    translucent: 'var(--color-panel-translucent)',
                },
                text: {
                    primary: 'var(--color-text-primary)',
                    secondary: 'var(--color-text-secondary)',
                    muted: 'var(--color-text-muted)',
                },
                causal: {
                    positive: 'var(--color-causal-positive)',
                    negative: 'var(--color-causal-negative)',
                    neutral: 'var(--color-causal-neutral)',
                },
                status: {
                    valid: 'var(--color-status-valid)',
                    warning: 'var(--color-status-warning)',
                    error: 'var(--color-status-error)',
                },
                border: {
                    standard: 'var(--color-border-standard)',
                }
            },
            borderRadius: {
                panel: 'var(--radius-panel)',
                overlay: 'var(--radius-overlay)',
            },
            zIndex: {
                canvas: 'var(--z-canvas)',
                panel: 'var(--z-panel)',
                overlay: 'var(--z-overlay)',
                modal: 'var(--z-modal)',
                cursor: 'var(--z-cursor)',
                system: 'var(--z-system)',
            }
        },
    },
    plugins: [],
}
