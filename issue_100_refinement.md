<!-- antigravity:template user-story -->

## User Story
Als **Gebruiker**  
wil ik **een context-menu kunnen openen per element op het canvas**  
zodat **ik context-specifieke acties kan uitvoeren zoals details bekijken of een AI-chat starten.**

---

## Design Intent
Het doel is om een flexibele, context-bewuste interactielaag toe te voegen aan het canvas.
**Technical Strategy**:
- Implementeer de `onNodeContextMenu` handler in `ReactFlowCanvas.tsx`.
- Introduceer een local state (of store) voor het actieve context-menu: `{ x: number, y: number, nodeId: string } | null`.
- Ontwikkel een generiek `<CanvasContextMenu />` component dat gepositioneerd wordt op basis van de muis-coördinaten.
- Dit component moet een lijst van `Action` objecten accepteren, zodat de inhoud dynamisch bepaald kan worden op basis van het type node (`Factor`, `SystemScope`, etc.).

**Extensibility**:
De architectuur moet toestaan dat latere user stories nieuwe acties (bijv. 'Verwijderen', 'Kleur wijzigen') toevoegen door enkel de actie-configuratie uit te breiden, zonder de core implementatie van het menu te wijzigen.

---

## Context en Aannames
- **Context**: De applicatie gebruikt `reactflow`. Interactie vindt plaats op nodes.
- **Dependency**: De `ChatInterface` moet bereikbaar zijn. Waarschijnlijk via een prop `onOpenChat(context: any)` die doorgegeven wordt aan de Canvas wrapper.
- **UX**: Context-menu vervangt bij 'Right Click' het standaard browser menu. Bij 'Left Click' blijft de huidige selectie-logica behouden.

---

## Features
- **Trigger**: Rechtsklik op Node (blokkeer default browser menu).
- **Component**: `CanvasContextMenu` (absolute positioned, z-index high).
- **Actie - Toon Details**: Trigger dezelfde logica als een left-click selectie (opent sidebar details).
- **Actie - Start AI Chat**: Verzend een signaal naar de AI Agent om een sessie te starten *met* de geselecteerde node als focus/context.
- **Dismissal**: Klikken buiten het menu (op canvas of andere node) sluit het menu.

---

## Acceptatiecriteria
- [ ] Rechtsklikken op een node opent custom context-menu op muispositie.
- [ ] Default browser context-menu wordt onderdrukt bij rechtsklik op node.
- [ ] Het menu toont optie 'Details tonen' (werkt identiek aan linksklik selectie).
- [ ] Het menu toont optie 'Start AI Chat'.
- [ ] 'Start AI Chat' logt/emit de intentie met de juiste node-ID en data.
- [ ] Klikken op het canvas (lege ruimte) sluit het context-menu.
- [ ] Code is gestructureerd met gescheiden component voor het menu en een definition-file voor de acties.

---

## Status
ready
