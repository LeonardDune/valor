# Product Backlog

Dit document bevat de user stories voor toekomstige gewenste functionaliteiten binnen het Valor/CAUSA-platform. 

## User Stories

*   **[US-01] Bézier Curves weergave**: Als een modelleur, wil ik dat de relaties tussen factoren worden weergegeven als vloeiende Bézier-curves in plaats van rechte lijnen, zodat het netwerk visueel aantrekkelijker is en de structuur van complexe causale paden duidelijker zichtbaar wordt.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
    *   **Notities**: Vereist aanpassing van de rendering-engine naar Bézier-paden en optimalisatie van curvatuur om overlap met nodes te voorkomen.
*   **[US-02] Interactief verslepen van nodes**: Als een modelleur, wil ik individuele nodes kunnen verslepen waarbij de force-directed layout zich dynamisch aanpast aan de nieuwe posities, zodat ik de belangrijkste factoren centraal kan zetten zonder de rest van de structuur te verloren.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
    *   **Notities**: Vereist implementatie van drag-events in de handmatige interactie-laag en het tijdelijk fixeren (fx/fy) van nodes tijdens en na het slepen.
*   **[US-03] Hiërarchische Layout Flow**: Als een modelleur, wil ik kunnen schakelen tussen verschillende layout-vormen, specifiek een hiërarchische weergave die de flow van 'extern/systeem' naar 'middel' naar 'criterium' visualiseert, zodat de logische opbouw van het beleidsmodel direct duidelijk is.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
    *   **Notities**: Vereist een gelaagd layout-algoritme (zoals Sugiyama) dat rekening houdt met de `type` property van de factoren voor de verticale of horizontale ordening.
*   **[US-04] Contextuele Focus & Filtering**: Als een modelleur, wil ik kunnen focussen op specifieke delen van het canvas (bijv. 1 stap verwijderd, of volledige paden stroomopwaarts/afwaarts vanaf een factor) door andere factoren te dimmen of te verbergen, zodat ik complexe causale paden zonder afleiding kan analyseren.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
    *   **Notities**: Vereist graaf-traversal logica voor het bepalen van de focus-set en een visuele staat (bijv. grijswaarden/transparantie) voor niet-geselecteerde elementen.
*   **[US-05] Interactieve Relatie-creatie (Drag-and-Drop)**: Als een modelleur, wil ik met de muis een verbinding kunnen trekken van een factor naar een andere factor, zodat ik snel en intuïtief nieuwe relaties kan leggen zonder alleen afhankelijk te zijn van de sidebar.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
    *   **Notities**: Vereist de implementatie van 'anchors' op nodes en een tijdelijke 'ghost' lijn tijdens het slepen. Bij het loslaten op een doel-node moet direct het eigenschappen-formulier openen.
*   **[US-06] Informatieve Hover Cards (Tooltips)**: Als een modelleur, wilt ik bij het 'hoveren' met de muis over een node of relatie een informatief kader (tooltip) zien waarin de eigenschappen (bijv. beschrijving, argumentatie, zekerheid) overzichtelijk worden weergegeven, zodat ik snel data kan inzien zonder te hoeven klikken.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
    *   **Notities**: Vereist een dynamisch gepositioneerde overlay (portal). **Let op**: In eerdere iteraties was er een conflict tussen hover- en klik-events; de implementatie moet robuust omgaan met de hit-detection laag zonder de selectie-interactie te verstoren.

---

## Format Richtlijnen
Elke user story volgt het standaard formaat:
- **ID**: Een uniek identificatienummer (bijv. [US-01]).
- **Story**: Als een [gebruiker], wil ik [functionaliteit], zodat [doel].
- **Prioriteit**: [Laag / Medium / Hoog]
- **Status**: [Backlog / In Progress / Done]
- **Notities**: Aanvullende details of technische overwegingen.
