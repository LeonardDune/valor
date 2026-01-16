# VALOR Design System Blueprint

## 1. Doel en reikwijdte

Het VALOR Design System is het normatieve kader voor alle gebruikersinterfaces binnen het VALOR-ecosysteem.  
Het doel is **consistente expressie van betekenis, interactie en status** over meerdere tools, perspectieven en agents heen.

Het design system:
- is geen visuele stijl alleen
- is geen componentbibliotheek op zichzelf
- is een **infrastructuur voor semantische consistentie**

---

## 2. Ontwerpprincipes

### 2.1. Betekenis vóór vorm
Visuele keuzes zijn altijd semantisch gemotiveerd. Decoratieve styling zonder betekenis is uitgesloten.

### 2.2. Scheiding van verantwoordelijkheden
- Semantiek: backend en domeinmodellen
- Interactie: frontend logic
- Presentatie: design tokens en theming

### 2.3. Progressive formalization
Het design system ondersteunt verschillende stadia van formalisering:
- exploratief
- voorlopig
- gevalideerd
- formeel

### 2.4. Ecosysteem-consistentie
Alle VALOR-tools volgen dezelfde:
- interaction patterns
- iconografische conventies
- semantische kleurregels

---

## 3. Architectuur-overzicht

Design Tokens
↓
Theme Composition
↓
Primitive Components (headless)
↓
Tool-specific Components
↓
Application Logic

---

## 4. Design Tokens (fundament)

### 4.1. Token-categorieën

#### Kleuren
- functioneel
- semantisch (causal, status)
- status-gebaseerd

#### Typografie
- schaal
- hiërarchie
- leesbaarheid

#### Spacing en layout
- grid
- margins
- gutters

#### Radius en elevation
- panels
- overlays
- canvas-elementen

#### Z-index lagen
- canvas
- overlay
- modal
- system

---

### 4.2. Voorbeeld tokens (JSON)

```json
{
  "color": {
    "semantic": {
      "causal": {
        "positive": "#2563eb",
        "negative": "#dc2626",
        "uncertain": "#a3a3a3"
      },
      "status": {
        "valid": "#16a34a",
        "warning": "#f59e0b",
        "error": "#dc2626"
      }
    }
  },
  "radius": {
    "panel": "8px",
    "overlay": "12px"
  },
  "zIndex": {
    "canvas": 0,
    "overlay": 10,
    "modal": 100,
    "system": 1000
  }
}
```

## 5. Theming-strategie
### 5.1. Token-first theming

Geen hardcoded waarden in componenten. Alle styling verwijst naar tokens.

### 5.2. Theme compositie

Themes zijn composities, geen vervangingen:
- Core theme
- Context theme (bijv. modelleren, analyseren)
- Role-based overrides
- Accessibility overrides

### 5.3. CSS Variables als runtime-mechanisme
```css
:root {
  --valor-color-causal-positive: #2563eb;
  --valor-radius-panel: 8px;
}
```

## 6. Component-primitieven
### 6.1. Definitie

Primitieven zijn interactionele bouwstenen, geen UI-patronen.

### 6.2. Canonieke primitieven

- Panel
- Drawer
- Modal
- Inspector
- Toolbar
- ContextMenu
- CanvasOverlay
- SemanticIndicator

Elke primitief:
- is headless
- heeft vast gedrag
- wordt gestyled via tokens

## 7. Interaction patterns
### 7.1. Canvas-interactie
- selecteren
- pannen
- zoomen
- contextmenu’s
- edge creation

### 7.2. Overlays en modals
- altijd via portals
- altijd cancellable
- focus-trap verplicht

### 7.3. Keyboard interaction
- consistente shortcuts
- canvas en UI shortcuts gescheiden

## 8. Semantische visualisatieconventies
### 8.1. Iconografie

Iconen zijn semantische dragers, geen decoratie.

Voorbeelden:
- causale polariteit
- onzekerheid
- conflict
- validatiestatus

Icons worden gedefinieerd als tokens:
- `icons.causality.positive`
- `icons.causality.negative`
- `icons.status.conflict`

### 8.2. Kleurgebruik

- kleur communiceert status, niet esthetiek
- kleurblind-vriendelijke combinaties verplicht

## 9. Canvas-specifieke richtlijnen (React Flow)
### 9.1. Scheiding canvas en UI
- canvas = expressie
- UI = controle en interpretatie

### 9.2. Edge-visualisatie
- richting altijd zichtbaar
- iconen boven labels
- schaalgedrag expliciet gedefinieerd

### 9.3. Layer discipline
- canvas laag is neutraal
- overlays expliciet gelaagd

## 10. Tooling en libraries
### 10.1. Aanbevolen stack
- React
- React Flow
- Tailwind CSS (token-driven)
- Radix UI (headless primitives)
- lucide-react (iconografie)
- Storybook (documentatie en governance)

### 10.2. Design token tooling
- Style Dictionary (optioneel, of eigen JSON map)
- JSON / TypeScript exports
- CSS variable output

## 11. Storybook als normatief platform
Storybook is de canon, het discussiedocument en de regressietest voor UX.

## 12. Governance en evolutie
### 12.1. Wijzigingsdiscipline
- tokens wijzigen vóór componenten
- semantiek eerst, stijl daarna

## 14. Samenvatting
Het VALOR Design System is betekenisgedreven, ecosysteem-breed, en technisch afdwingbaar.