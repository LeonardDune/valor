import { useSociaOntology } from '../../hooks/useSociaOntology';

interface ActorNodeProps {
    label: string;
    actor_type_uri: string;
    role_uri?: string;
}

export function ActorNode({ label, actor_type_uri, role_uri }: ActorNodeProps) {
    const { ontology } = useSociaOntology();

    const actorType = ontology?.actor_types.find((t) => t.uri === actor_type_uri);
    const role = role_uri ? ontology?.roles.find((r) => r.uri === role_uri) : null;

    return (
        <div className="flex flex-col items-center gap-1 px-3 py-2 rounded-lg border border-border bg-card text-card-foreground shadow-sm min-w-[120px]">
            <span className="text-sm font-medium truncate max-w-[160px]">{label}</span>
            {actorType && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                    {actorType.label_nl}
                </span>
            )}
            {role && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                    {role.label_nl}
                </span>
            )}
        </div>
    );
}
