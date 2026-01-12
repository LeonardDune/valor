# Product Backlog

Dit document bevat de user stories voor toekomstige gewenste functionaliteiten binnen het Valor/CAUSA-platform. 

## User Stories

## User Stories

### Epic 1: Conversational Reasoning Foundation
Users can engage in AI-facilitated causal reasoning through natural dialogue.

*   **[US-07] Conversational Reasoning Onboarding**: Als een beleidsanalist, wil ik een duidelijke onboarding die de conversationele causale redeneerwijze uitlegt, zodat ik begrijp hoe ik claims moet formuleren en de AI-assistentie effectief kan gebruiken.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
    *   **Notities**: Inclusief voorbeelden van causale claims en uitleg over AI-responsietijden.
*   **[US-08] AI-Facilitatie met Fallback**: Als een beleidsanalist, wil ik dat de AI-assistentie betrouwbaar werkt met een fallback-mechanisme naar handmatige invoer, zodat het redeneerproces altijd door kan gaan, ook als de AI-service tijdelijk niet beschikbaar is.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
    *   **Notities**: Feedback over AI-beschikbaarheid moet duidelijk zichtbaar zijn in de chat-interface.
*   **[US-09] Conversatie Navigatie & Threading**: Als een beleidsanalist, wil ik door conversatie-draadjes kunnen navigeren en zijpaden kunnen verkennen, zodat ik de context van verschillende redeneerlijnen kan behouden zonder het overzicht te verliezen.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-20] Natuurlijke Taal Claim Invoer**: Als een beleidsanalist, wil ik causale claims in natuurlijke taal invoeren met validatie, zodat ik relaties duidelijk kan uitdrukken en directe feedback krijg.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog


### Epic 2: Collaborative Reasoning Sessions
Multiple users can collaborate in real-time reasoning sessions.

*   **[US-10] Multi-User Sessie Setup**: Als een coördinator, wil ik meerdere belanghebbenden kunnen uitnodigen voor een redeneersessie, zodat we gezamenlijk aan complexe beleidskwesties kunnen werken.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
*   **[US-11] Real-time Collaboratie Updates**: Als een deelnemer, wil ik live updates zien van andere deelnemers, zodat we synchroon kunnen samenwerken aan het causale model.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
    *   **Notities**: Vereist WebSocket-implementatie voor sub-second vertraging.
*   **[US-12] Conflict Resolutie Systeem**: Als een sessie-begeleider, wil ik conflicterende causale claims kunnen identificeren en oplossen, zodat de groep consensus kan bereiken over betwiste relaties.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-21] Rolbeheer voor Deelnemers**: Als een organisatiebeheerder, wil ik rollen toewijzen aan sessiedeelnemers, zodat toegangsrechten overeenkomen met organisatorische verantwoordelijkheden.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-22] Toegangscontrole voor Sessies**: Als een sessie-organisator, wil ik kunnen bepalen wie kan deelnemen en bijdragen, zodat gevoelige discussies veilig blijven.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog


### Epic 3: Causal Model Workspace
Users can visualize, edit, and analyze structured causal models.

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
*   **[US-13] Onzekerheid & Vertrouwen Management**: Als een beleidsanalist, wil ik onzekerheidsniveaus kunnen toekennen aan causale relaties, zodat ik de mate van vertrouwen in het model kan communiceren.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
    *   **Notities**: Heatmaps kunnen worden gebruikt om gebieden met lage zekerheid te identificeren.
*   **[US-14] Scenario Simulatie Engine**: Als een beleidsanalist, wil ik scenario-simulaties kunnen draaien, zodat ik de effecten van verschillende parameterwijzigingen op de uitkomsten kan verkennen.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-15] Geavanceerde Analyse (Leverage Points & Loops)**: Als een beleidsanalist, wil ik dat feedback-loops en hefboompunten automatisch worden geïdentificeerd, zodat ik effectieve interventies in het systeem kan voorstellen.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-23] Model Export Functionaliteit**: Als een beleidsanalist, wil ik modellen in meerdere formaten kunnen exporteren, zodat ik ze kan delen en integreren met andere tools.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog


### Epic 4: VALOR Ecosystem Integration
Integration with other VALOR agents for comprehensive analysis.

*   **[US-16] VALOR Agent Orchestratie**: Als een beleidsanalist, wil ik dat CAUSA naadloos samenwerkt met andere agenten zoals AXIA (waarden) en POLIS (governance), zodat ik gespecialiseerde inzichten uit verschillende domeinen kan integreren.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-24] Cross-Agent Data Uitwisseling**: Als een beleidsanalist, wil ik naadloze gegevensstroom tussen VALOR-agenten, zodat agenten kunnen voortbouwen op elkaars analyses.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog


### Epic 5: Enterprise Governance & Data Hub
Workspace management, compliance, and data intelligence.

*   **[US-17] Workspace Management Systeem**: Als een beheerder, wil ik meerdere werkruimtes kunnen aanmaken en beheren met specifieke privacy- en toegangsinstellingen.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-18] Compliance & Audit Framework**: Als een compliance officer, wil ik dat alle acties in het systeem gelogd worden, zodat we voldoen aan de overheidsrichtlijnen voor traceerbaarheid.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
*   **[US-19] Data Import/Export Hub**: Als een data-analist, wil ik externe data (CSV, Excel, API's) kunnen importeren om causale redeneringen te verrijken met real-world data.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-25] Gebruikersadministratie**: Als een IT-beheerder, wil ik gebruikersaccounts en machtigingen beheren, zodat de organisatorische toegangscontrole correct wordt gehandhaafd.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-26] Rapportage en Analytics**: Als een leidinggevende, wil ik organisatorisch gebruik en impact kunnen monitoren, zodat ik de waarde en effectiviteit van de implementatie kan begrijpen.
    *   **Prioriteit**: Laag
    *   **Status**: Backlog
*   **[US-27] Data Governance Beheer**: Als een datasteward, wil ik dataclassificatie en retentie beheren, zodat gevoelige overheidsinformatie goed wordt beschermd.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog


### Epic 6: Data Intelligence Hub
Data sources, search, and analytics.

*   **[US-28] Zoek- en Ontdekkingsmachine**: Als een onderzoeker, wil ik door alle redeneerinhoud kunnen zoeken, zodat ik relevante inzichten kan vinden en kan voortbouwen op bestaand werk.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-29] Programma Analytics Dashboard**: Als een programmamanager, wil ik de effectiviteit van redeneringen monitoren, zodat ik de teamprestaties kan optimaliseren en verbeterpunten kan identificeren.
    *   **Prioriteit**: Laag
    *   **Status**: Backlog
*   **[US-30] Geautomatiseerde Data-updates**: Als een beleidsanalist, wil ik geautomatiseerde data-updates, zodat causale modellen actueel blijven met de laatste informatie.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-31] Data Validatie Framework**: Als een datakwaliteitsspecialist, wil ik de data-integriteit in causale modellen waarborgen, zodat redeneringen gebaseerd zijn op betrouwbare informatie.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-32] Performance Monitoring Dashboard**: Als een systeembeheerder, wil ik de systeemprestaties monitoren, zodat ik een optimale gebruikerservaring kan garanderen en capaciteit kan plannen.
    *   **Prioriteit**: Laag
    *   **Status**: Backlog

### Epic 7: Advanced Integration & Operations
External tools, mobile support, and reliability.

*   **[US-33] Externe Tool Integratie**: Als een collaboratie-specialist, wil ik CAUSA kunnen integreren in externe tools, zodat redeneren binnen bestaande workflows kan plaatsvinden.
    *   **Prioriteit**: Medium
    *   **Status**: Backlog
*   **[US-34] Mobiele Apparaat Ondersteuning**: Als een veldonderzoeker, wil ik vanaf mobiele apparaten kunnen deelnemen, zodat ik overal kan bijdragen aan redeneersessies.
    *   **Prioriteit**: Laag
    *   **Status**: Backlog
*   **[US-35] Workflow Management**: Als een procescoördinator, wil ik redeneertemplates en workflows creëren, zodat consistente aanpakken over projecten heen kunnen worden toegepast.
    *   **Prioriteit**: Laag
    *   **Status**: Backlog
*   **[US-36] Backup en Herstel**: Als een functionaris gegevensbescherming, wil ik betrouwbare back-up en herstel mogelijkheden, zodat belangrijk redeneerwerk nooit verloren gaat.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
*   **[US-37] Cross-Device Continuïteit**: Als een gebruiker met meerdere apparaten, wil ik naadloze overgangen tussen apparaten, zodat ik mijn werk kan voortzetten waar ik ook ben.
    *   **Prioriteit**: Laag
    *   **Status**: Backlog
*   **[US-38] Operationele Betrouwbaarheid**: Als een servicemanager, wil ik hoge systeembetrouwbaarheid, zodat gebruikers op CAUSA kunnen rekenen voor kritiek redeneerwerk.
    *   **Prioriteit**: Hoog
    *   **Status**: Backlog
*   **[US-39] Template Bibliotheek Beheer**: Als een kennismanager, wil ik redeneertemplates beheren, zodat best practices kunnen worden gedeeld en hergebruikt binnen de organisatie.
    *   **Prioriteit**: Laag
    *   **Status**: Backlog

---

## Format Richtlijnen
Elke user story volgt het standaard formaat:
- **ID**: Een uniek identificatienummer (bijv. [US-01]).
- **Story**: Als een [gebruiker], wil ik [functionaliteit], zodat [doel].
- **Prioriteit**: [Laag / Medium / Hoog]
- **Status**: [Backlog / In Progress / Done]
- **Notities**: Aanvullende details of technische overwegingen.
