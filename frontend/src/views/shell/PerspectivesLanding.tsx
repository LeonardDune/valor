import { Brain, Scale, Users, Heart } from "lucide-react";

export function PerspectivesLanding() {
    return (
        <div className="flex-1 overflow-y-auto p-4 lg:p-12 max-w-6xl mx-auto">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-bold tracking-tight mb-4">Perspectief-Gedreven Analyse</h1>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                    Valor helpt je complexe vraagstukken te ontrafelen door ze vanuit verschillende lenzen te bekijken.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
                <div className="p-8 rounded-2xl border border-border bg-card hover:border-primary/50 transition-colors group">
                    <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center mb-6 text-blue-500 group-hover:scale-110 transition-transform">
                        <Brain className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold mb-3">CAUSA</h3>
                    <p className="text-muted-foreground mb-6">
                        Analyseer oorzaak-gevolg relaties. Breng factoren, dynamieken en systeeminterventies in kaart.
                    </p>
                    <div className="flex items-center text-sm font-medium text-blue-500">
                        Beschikbaar in Workspace
                    </div>
                </div>

                <div className="p-8 rounded-2xl border border-border bg-card hover:border-primary/50 transition-colors group opacity-75">
                    <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center mb-6 text-emerald-500 group-hover:scale-110 transition-transform">
                        <Scale className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold mb-3">NORM</h3>
                    <p className="text-muted-foreground mb-6">
                        Evalueer juridische kaders, ethische richtlijnen en compliance vereisten.
                    </p>
                    <div className="flex items-center text-sm font-medium text-muted-foreground">
                        Binnenkort beschikbaar
                    </div>
                </div>

                <div className="p-8 rounded-2xl border border-border bg-card hover:border-primary/50 transition-colors group opacity-75">
                    <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center mb-6 text-purple-500 group-hover:scale-110 transition-transform">
                        <Users className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold mb-3">ACTOR</h3>
                    <p className="text-muted-foreground mb-6">
                        Begrijp de belangen, invloed en relaties van betrokken stakeholders.
                    </p>
                    <div className="flex items-center text-sm font-medium text-muted-foreground">
                        Binnenkort beschikbaar
                    </div>
                </div>

                <div className="p-8 rounded-2xl border border-border bg-card hover:border-primary/50 transition-colors group opacity-75">
                    <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center mb-6 text-amber-500 group-hover:scale-110 transition-transform">
                        <Heart className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold mb-3">VALUE</h3>
                    <p className="text-muted-foreground mb-6">
                        weeg maatschappelijke waarden en impact af tegen kosten en baten.
                    </p>
                    <div className="flex items-center text-sm font-medium text-muted-foreground">
                        Binnenkort beschikbaar
                    </div>
                </div>
            </div>

            <div className="bg-muted/30 rounded-2xl p-8 text-center border border-dashed border-border">
                <h3 className="font-semibold text-lg mb-2">Toekomstige Dashboard Functionaliteit</h3>
                <p className="text-muted-foreground text-sm max-w-lg mx-auto">
                    In de toekomst zie je hier een matrix overzicht van al jouw thema's, gegroepeerd per perspectief status. Zo zie je direct waar juridische checks nodig zijn (NORM) of waar stakeholder analyses ontbreken (ACTOR).
                </p>
            </div>
        </div>
    );
}
