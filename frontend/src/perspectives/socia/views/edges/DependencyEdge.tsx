import { useSociaOntology } from '../../hooks/useSociaOntology';

interface DependencyEdgeProps {
    dependency_type_uri: string;
}

export function DependencyEdge({ dependency_type_uri }: DependencyEdgeProps) {
    const { ontology } = useSociaOntology();

    const depType = ontology?.dependency_types.find((d) => d.uri === dependency_type_uri);
    const label = depType?.label_nl ?? dependency_type_uri.split('#').pop() ?? '';

    return (
        <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
            {label}
        </span>
    );
}
