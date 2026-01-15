Ik zal dit in twee lagen benaderen:

wat er technisch misgaat in jouw huidige hook, en

een structureel betere architectuur voor meerdere layouts die elkaar niet “besmetten”.

Ik blijf dicht bij jouw code en aannames; dit is geen React Flow-basics antwoord.

1. Wat gaat hier inhoudelijk mis?
Kernprobleem in één zin

Je Free-layout start niet vanuit een schone, autonome state, maar vanuit gemuteerde D3-node objecten die eerder door de System-layout zijn gefixeerd en gepositioneerd.

Dat gebeurt op meerdere, elkaar versterkende plekken.

1.1 D3 nodes zijn mutable en worden hergebruikt

Dit is de belangrijkste oorzaak.

const simulation = forceSimulation(d3Nodes as any);


d3Nodes is een array van objecten

D3-force muteert die objecten in-place (x, y, vx, vy, fx, fy)

Bij layout switch gebruik je dezelfde objectidentiteiten opnieuw

Zelfs al:

stop je de simulation

remount je de hook

verander je forces

Dan nog zijn:

fx / fy

snelheden

eindposities

al “ingebrand” in de node-objecten.

Dat verklaart exact dit symptoom:

de posities van de System layout worden meegenomen naar Free layout

1.2 useMemo beschermt je hier niet
const d3Nodes = useMemo(() => { ... }, [nodes.length, layoutMode]);


Dit suggereert “nieuwe nodes”, maar feitelijk:

Bij gelijke nodes.length en gelijke layoutMode

blijven dezelfde objectreferenties bestaan

inclusief alle D3-mutaties

Bovendien:

bij switch System → Free

neem je expliciet n.position.x als startpositie
→ dat is exact de System-layout

Je scramble-logica helpt hier maar beperkt.

1.3 fx en fy zijn niet hard gereset

Je doet dit:

d3Nodes.forEach((n: any) => { n.fx = undefined; n.fy = undefined; });


Maar:

D3 beschouwt fx / fy semantisch

undefined is niet hetzelfde als afwezig

oude krachten, snelheden en links blijven bestaan

Best practice is expliciet:

delete n.fx;
delete n.fy;
n.vx = 0;
n.vy = 0;


Maar zelfs dat is hier niet genoeg.

1.4 React Flow nodes en D3 nodes zijn te sterk gekoppeld

Je gebruikt React Flow nodes als:

bron van waarheid voor startposities

target voor elke tick

impliciete opslag van layoutresultaat

Daardoor:

“lekt” elke layout zijn eindtoestand door

naar elke volgende layout

Je layouts zijn dus niet onafhankelijk, maar sequentieel afhankelijk.

2. Waarom “canvas opnieuw opbouwen” niet lukt

Zelfs als je:

key={layoutMode} gebruikt

hook remount

simulation stopt

blijft dit waar:

React Flow bewaart node positions als state
en jij hergebruikt die posities als input

Dus je “nieuw opgebouwde canvas” is semantisch:

een nieuwe simulation

bovenop oude layoutdata

Je reset het mechanisme, niet de bron van waarheid.

3. Structureel betere aanpak (aanbevolen)
Principe: Layout = pure functie

Een layout moet zijn:

(nodes, edges) → positions


En niet:

een muterend proces dat voortbouwt op vorige layouts

Daaruit volgen drie concrete strategieën.

Oplossing A – Separate layout states (meest robuust)

Behandel layouts als parallelle werelden.

type LayoutPositions = Record<string, { x: number; y: number }>;

const layoutCache = useRef<{
  force?: LayoutPositions;
  system?: LayoutPositions;
}>({});

Werking

Elke layout schrijft naar zijn eigen positie-map

Bij switch:

laad je expliciet de posities van die layout

of initialiseert opnieuw

setNodes(nodes =>
  nodes.map(n => ({
    ...n,
    position: layoutCache.current.force?.[n.id] ?? random()
  }))
);


Voordelen:

layouts beïnvloeden elkaar niet

je kunt layouts onthouden of resetten

mentaal model is helder

Nadeel:

iets meer code

maar conceptueel veel schoner

Oplossing B – Force-layout altijd starten vanuit neutrale seed

Als je per se live-force wilt:

const seedNodes = nodes.map(n => ({
  id: n.id,
  x: (Math.random() - 0.5) * scopeW,
  y: (Math.random() - 0.5) * scopeH
}));


En nooit:

n.position.x

of vorige d3Nodes

gebruiken als startpunt voor Free-layout.

Belangrijk:

ook links opnieuw instantiëren

geen objectreferenties hergebruiken

Oplossing C – Precompute layouts buiten React Flow (conceptueel sterk)

Voor complexere modellen (CLD, systeemdiagrammen):

laat D3 offline layout berekenen

converteer resultaat naar React Flow nodes

render statisch

optioneel: animate interpolatie

Dit sluit goed aan bij:

formele modellen

reproduceerbare diagrammen

“layout als betekenisdrager”

Denk aan:

Graphviz-achtig denken

minder “physics”, meer semantiek

4. Concreet advies voor jouw code

Als ik minimaal ingrijp, zou ik:

D3 nodes nooit hergebruiken

const d3Nodes = nodes.map(n => ({
  id: n.id,
  x: randomX(),
  y: randomY()
}));


Free-layout nooit initialiseren vanuit React Flow positions

fx / fy altijd verwijderen

delete n.fx;
delete n.fy;
n.vx = 0;
n.vy = 0;


Per layout een eigen lifecycle afdwingen

aparte hook

aparte simulationRef

aparte state

5. Conceptuele afsluiting

Wat je nu voelt (“dit zou eenvoudiger moeten kunnen”) klopt.
Het spanningsveld is:

React Flow is state-first

D3-force is mutation-first

Zodra je meerdere layouts wilt die semantisch verschillend zijn
(clustering versus systeempositie), moet je kiezen:

of je laat state leidend zijn
of je laat physics leidend zijn

maar niet allebei tegelijk.