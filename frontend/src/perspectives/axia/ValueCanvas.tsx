import { useCallback, useEffect, useRef, useState, type MutableRefObject } from 'react';
import ReactFlow, {
    Background,
    ConnectionMode,
    Handle,
    MarkerType,
    Position,
    useNodesState,
    useEdgesState,
    useNodesInitialized,
    useReactFlow,
    getBezierPath,
    BaseEdge,
    type Node,
    type Edge,
    type EdgeProps,
    type Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { toast } from 'sonner';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { api } from '@/services/api';
import type { ValueClaimItem, ValueTensionResponse } from '@/services/api';
import { useAxiaSchema } from './hooks/useAxiaSchema';
import { getGeometricHandles } from '../causa/layout/edgeUtils';

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------

const HEX_W = 220;
const HEX_H = 120;
const NODE_WIDTH = 220;
const COL_GAP = 80;
const NODE_HEIGHT = 120;
const NODE_GAP = 16;
const GROUP_HEADER_H = 32;
const START_X = 60;
const START_Y = 60;
const HEX_CLIP = 'polygon(8% 0%, 92% 0%, 100% 50%, 92% 100%, 8% 100%, 0% 50%)';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function polarityColors(uri?: string | null): { bg: string; text: string; label: string } {
    if (!uri) return { bg: '#e2e8f0', text: '#475569', label: '#94a3b8' };
    if (uri.includes('Supporting')) return { bg: '#dcfce7', text: '#15803d', label: '#16a34a' };
    if (uri.includes('Undermining') || uri.includes('Opposing') || uri.includes('Conflicting'))
        return { bg: '#fee2e2', text: '#b91c1c', label: '#dc2626' };
    if (uri.includes('Ambiguous') || uri.includes('Neutral'))
        return { bg: '#fef9c3', text: '#854d0e', label: '#ca8a04' };
    return { bg: '#e2e8f0', text: '#475569', label: '#94a3b8' };
}

// ---------------------------------------------------------------------------
// Custom node — hexagonale vorm met CAUSA-stijl handles
// ---------------------------------------------------------------------------

interface ValueClaimNodeData {
    claim: ValueClaimItem;
}

function ValueClaimNode({ data }: { data: ValueClaimNodeData }) {
    const { claim } = data;
    const colors = polarityColors(claim.polarity_uri);
    const [hovered, setHovered] = useState(false);

    const handleStyle = (visible: boolean): React.CSSProperties => ({
        width: 10,
        height: 10,
        background: '#475569',
        border: '2px solid #94a3b8',
        borderRadius: '50%',
        opacity: visible ? 1 : 0,
        transition: 'opacity 0.15s',
        zIndex: 10,
    });

    return (
        <div
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            style={{ width: HEX_W, height: HEX_H, position: 'relative' }}
        >
            {/* CAUSA-stijl handles: source-* en target-* per positie */}
            <Handle id="source-left"   type="source" position={Position.Left}   style={handleStyle(hovered)} />
            <Handle id="source-right"  type="source" position={Position.Right}  style={handleStyle(hovered)} />
            <Handle id="source-top"    type="source" position={Position.Top}    style={handleStyle(hovered)} />
            <Handle id="source-bottom" type="source" position={Position.Bottom} style={handleStyle(hovered)} />
            <Handle id="target-left"   type="target" position={Position.Left}   style={handleStyle(hovered)} />
            <Handle id="target-right"  type="target" position={Position.Right}  style={handleStyle(hovered)} />
            <Handle id="target-top"    type="target" position={Position.Top}    style={handleStyle(hovered)} />
            <Handle id="target-bottom" type="target" position={Position.Bottom} style={handleStyle(hovered)} />

            {/* Hexagon */}
            <div
                style={{
                    width: HEX_W,
                    height: HEX_H,
                    clipPath: HEX_CLIP,
                    backgroundColor: colors.bg,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '12px 32px',
                    boxSizing: 'border-box',
                    cursor: 'pointer',
                }}
            >
                <p style={{
                    fontSize: 11, lineHeight: 1.4, color: colors.text, textAlign: 'center',
                    margin: 0, overflow: 'hidden', display: '-webkit-box',
                    WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', fontWeight: 500,
                }}>
                    {claim.claim_content}
                </p>
                {claim.value_type_label && (
                    <span style={{
                        marginTop: 4, fontSize: 9, color: colors.label, fontWeight: 600,
                        textTransform: 'uppercase', letterSpacing: '0.05em',
                        maxWidth: '80%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                        {claim.value_type_label}
                    </span>
                )}
            </div>
        </div>
    );
}

const NODE_TYPES = { valueClaim: ValueClaimNode };

// ---------------------------------------------------------------------------
// Tension edge — CAUSA-stijl: BaseEdge + EdgeLabelRenderer + design tokens
// ---------------------------------------------------------------------------

interface ValueTensionEdgeData {
    description?: string;
    tessera_uri?: string;
}

function ValueTensionEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, markerEnd, markerStart }: EdgeProps<ValueTensionEdgeData>) {
    const [edgePath] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });

    return (
        <>
            <BaseEdge
                id={id}
                path={edgePath}
                markerEnd={markerEnd}
                markerStart={markerStart}
                style={{
                    stroke: '#dc2626',
                    strokeWidth: 2,
                    strokeDasharray: '6 3',
                    opacity: 0.7,
                }}
            />
        </>
    );
}

const EDGE_TYPES = { valueTension: ValueTensionEdge };

// ---------------------------------------------------------------------------
// AutoFitView
// ---------------------------------------------------------------------------

function AutoFitView({ shouldFitRef }: { shouldFitRef: MutableRefObject<boolean> }) {
    const { fitView } = useReactFlow();
    const nodesInitialized = useNodesInitialized();
    useEffect(() => {
        if (!nodesInitialized || !shouldFitRef.current) return;
        shouldFitRef.current = false;
        fitView({ padding: 0.2, duration: 400 });
    }, [nodesInitialized, fitView, shouldFitRef]);
    return null;
}

// ---------------------------------------------------------------------------
// CreateTensionDialog — opent na handle-drag
// ---------------------------------------------------------------------------

interface PendingConnection {
    sourceNodeId: string;
    targetNodeId: string;
    sourceLabel: string;
    targetLabel: string;
    sourceVtUri: string;
    targetVtUri: string;
}

interface CreateTensionDialogProps {
    pending: PendingConnection | null;
    designSpaceId: string;
    onConfirm: (description: string, context: string) => Promise<void>;
    onClose: () => void;
}

function CreateTensionDialog({ pending, designSpaceId: _dsId, onConfirm, onClose }: CreateTensionDialogProps) {
    const [description, setDescription] = useState('');
    const [context, setContext] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (!pending) { setDescription(''); setContext(''); }
    }, [pending]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!description.trim()) return;
        setIsSaving(true);
        try {
            await onConfirm(description.trim(), context.trim());
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <Dialog open={!!pending} onOpenChange={(open) => { if (!open) onClose(); }}>
            <DialogContent className="sm:max-w-[420px]">
                <DialogHeader>
                    <DialogTitle>Waardespanning</DialogTitle>
                    <DialogDescription>
                        {pending
                            ? `Spanning tussen "${pending.sourceLabel}" en "${pending.targetLabel}"`
                            : ''}
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="grid gap-4 py-2">
                    <div className="grid gap-2">
                        <Label htmlFor="tension-desc">Omschrijving</Label>
                        <Textarea
                            id="tension-desc"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                            placeholder="Omschrijf de spanning tussen de twee waardetypen..."
                            autoFocus
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="tension-ctx">
                            Context <span className="text-muted-foreground text-xs">(optioneel)</span>
                        </Label>
                        <Textarea
                            id="tension-ctx"
                            value={context}
                            onChange={(e) => setContext(e.target.value)}
                            rows={2}
                            placeholder="In welke situatie speelt deze spanning?"
                        />
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={onClose} disabled={isSaving}>
                            Annuleren
                        </Button>
                        <Button type="submit" disabled={!description.trim() || isSaving}>
                            {isSaving ? 'Opslaan...' : 'Spanning aanmaken'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// ---------------------------------------------------------------------------
// EditTensionDialog — opent bij dubbelklik op edge
// ---------------------------------------------------------------------------

interface EditTensionDialogProps {
    tension: ValueTensionResponse | null;
    onClose: () => void;
    onSaved: () => void;
    designSpaceId: string;
}

function EditTensionDialog({ tension, onClose, onSaved, designSpaceId }: EditTensionDialogProps) {
    const [description, setDescription] = useState('');
    const [context, setContext] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [confirmDelete, setConfirmDelete] = useState(false);

    useEffect(() => {
        if (tension) {
            setDescription(tension.description ?? '');
            setContext(tension.tension_context ?? '');
            setConfirmDelete(false);
        }
    }, [tension]);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!tension || !description.trim()) return;
        setIsSaving(true);
        try {
            await api.updateValueTension(designSpaceId, tension.tessera_uri, {
                description: description.trim(),
                tension_context: context.trim() || undefined,
            });
            toast.success('Spanning bijgewerkt.');
            onSaved();
            onClose();
        } catch {
            toast.error('Opslaan mislukt.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!tension) return;
        setIsDeleting(true);
        try {
            await api.deleteValueTension(designSpaceId, tension.tessera_uri);
            toast.success('Spanning verwijderd.');
            onSaved();
            onClose();
        } catch {
            toast.error('Verwijderen mislukt.');
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <Dialog open={!!tension} onOpenChange={(open) => { if (!open) onClose(); }}>
            <DialogContent className="sm:max-w-[420px]">
                <DialogHeader>
                    <DialogTitle>Waardespanning bewerken</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSave} className="grid gap-4 py-2">
                    <div className="grid gap-2">
                        <Label htmlFor="edit-tension-desc">Omschrijving</Label>
                        <Textarea
                            id="edit-tension-desc"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                            autoFocus
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="edit-tension-ctx">
                            Context <span className="text-muted-foreground text-xs">(optioneel)</span>
                        </Label>
                        <Textarea
                            id="edit-tension-ctx"
                            value={context}
                            onChange={(e) => setContext(e.target.value)}
                            rows={2}
                        />
                    </div>
                    <DialogFooter className="flex-col gap-2 sm:flex-row sm:justify-between">
                        <div>
                            {!confirmDelete ? (
                                <Button
                                    type="button"
                                    variant="destructive"
                                    size="sm"
                                    onClick={() => setConfirmDelete(true)}
                                    disabled={isDeleting || isSaving}
                                >
                                    Verwijderen
                                </Button>
                            ) : (
                                <div className="flex gap-2">
                                    <Button
                                        type="button"
                                        variant="destructive"
                                        size="sm"
                                        onClick={handleDelete}
                                        disabled={isDeleting}
                                    >
                                        {isDeleting ? 'Verwijderen...' : 'Bevestigen'}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setConfirmDelete(false)}
                                        disabled={isDeleting}
                                    >
                                        Annuleren
                                    </Button>
                                </div>
                            )}
                        </div>
                        <div className="flex gap-2">
                            <Button type="button" variant="outline" onClick={onClose} disabled={isSaving || isDeleting}>
                                Sluiten
                            </Button>
                            <Button type="submit" disabled={!description.trim() || isSaving || isDeleting}>
                                {isSaving ? 'Opslaan...' : 'Opslaan'}
                            </Button>
                        </div>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// ---------------------------------------------------------------------------
// buildNodes — auto-layout
// ---------------------------------------------------------------------------

function buildNodes(claims: ValueClaimItem[]): Node[] {
    const named: Record<string, ValueClaimItem[]> = {};
    const ungrouped: ValueClaimItem[] = [];
    for (const claim of claims) {
        if (claim.value_type_uri) {
            (named[claim.value_type_uri] ??= []).push(claim);
        } else {
            ungrouped.push(claim);
        }
    }
    const groups = Object.values(named).sort((a, b) =>
        (a[0]?.value_type_label ?? '').localeCompare(b[0]?.value_type_label ?? '', 'nl')
    );
    if (ungrouped.length > 0) groups.push(ungrouped);

    const nodes: Node[] = [];
    const colStep = NODE_WIDTH + COL_GAP;
    groups.forEach((group, colIndex) => {
        const x = START_X + colIndex * colStep;
        group.forEach((claim, rowIndex) => {
            nodes.push({
                id: claim.tessera_id,
                type: 'valueClaim',
                position: { x, y: START_Y + GROUP_HEADER_H + rowIndex * (NODE_HEIGHT + NODE_GAP) },
                data: { claim },
                style: { width: HEX_W, height: HEX_H },
            });
        });
    });
    return nodes;
}

// ---------------------------------------------------------------------------
// ValueCanvas
// ---------------------------------------------------------------------------

interface ValueCanvasProps {
    designSpaceId: string;
    refreshTrigger?: number;
    onEdit?: (claim: ValueClaimItem) => void;
}

export function ValueCanvas({ designSpaceId, refreshTrigger = 0, onEdit }: ValueCanvasProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState<ValueClaimNodeData>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const shouldFitRef = useRef(false);
    const [pendingConnection, setPendingConnection] = useState<PendingConnection | null>(null);
    const [editingTension, setEditingTension] = useState<ValueTensionResponse | null>(null);
    useAxiaSchema(); // schema preloaden voor ValueTensionView

    // Houd een map bij van tessera_id → claim voor snelle lookup bij onConnect
    const claimsMapRef = useRef<Map<string, ValueClaimItem>>(new Map());
    // Houd een map bij van edge-id → ValueTensionResponse voor dubbelklik
    const tensionsMapRef = useRef<Map<string, ValueTensionResponse>>(new Map());
    // Houd node positions bij voor getGeometricHandles
    const nodePositionsRef = useRef<Map<string, { x: number; y: number }>>(new Map());

    const load = useCallback(async () => {
        try {
            const [claimsResult, tensionsResult] = await Promise.all([
                api.getValueClaims(designSpaceId),
                api.getValueTensions(designSpaceId),
            ]);

            const flat: ValueClaimItem[] = Object.values(claimsResult.groups).flat();
            claimsMapRef.current = new Map(flat.map((c) => [c.tessera_id, c]));

            const builtNodes = buildNodes(flat);
            nodePositionsRef.current = new Map(builtNodes.map((n) => [n.id, n.position]));
            shouldFitRef.current = true;
            setNodes(builtNodes);

            // Bouw edges: per spanning → zoek één representatieve node per ValueType
            const vtToNodeId = new Map<string, string>();
            for (const claim of flat) {
                if (claim.value_type_uri && !vtToNodeId.has(claim.value_type_uri)) {
                    vtToNodeId.set(claim.value_type_uri, claim.tessera_id);
                }
            }

            tensionsMapRef.current = new Map(tensionsResult.tensions.map((t) => [t.tessera_id, t]));

            const newEdges: Edge[] = tensionsResult.tensions.flatMap((t) => {
                const sourceId = vtToNodeId.get(t.value_type_a_uri);
                const targetId = vtToNodeId.get(t.value_type_b_uri);
                if (!sourceId || !targetId) return [];

                // Gebruik getGeometricHandles voor slimme routing (CAUSA-patroon)
                const sourcePos = nodePositionsRef.current.get(sourceId) ?? { x: 0, y: 0 };
                const targetPos = nodePositionsRef.current.get(targetId) ?? { x: 0, y: 0 };
                const { sourceHandle, targetHandle } = getGeometricHandles(sourcePos, targetPos);

                return [{
                    id: t.tessera_id,
                    source: sourceId,
                    target: targetId,
                    sourceHandle,
                    targetHandle,
                    type: 'valueTension',
                    markerEnd: { type: MarkerType.ArrowClosed, color: '#dc2626', width: 16, height: 16 },
                    markerStart: { type: MarkerType.ArrowClosed, color: '#dc2626', width: 16, height: 16 },
                    data: {
                        description: t.description,
                        tessera_uri: t.tessera_uri,
                    },
                }];
            });
            setEdges(newEdges);
        } catch {
            // keep canvas empty on error
        }
    }, [designSpaceId, setNodes, setEdges]);

    useEffect(() => {
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [load, refreshTrigger]);

    const handleNodeDoubleClick = useCallback(
        (_: React.MouseEvent, node: { data: ValueClaimNodeData }) => {
            onEdit?.(node.data.claim);
        },
        [onEdit],
    );

    const handleEdgeDoubleClick = useCallback(
        (_: React.MouseEvent, edge: Edge) => {
            const tension = tensionsMapRef.current.get(edge.id);
            if (tension) setEditingTension(tension);
        },
        [],
    );

    const handleConnect = useCallback(
        (connection: Connection) => {
            if (!connection.source || !connection.target) return;
            if (connection.source === connection.target) return;

            const sourceNode = claimsMapRef.current.get(connection.source);
            const targetNode = claimsMapRef.current.get(connection.target);
            if (!sourceNode || !targetNode) return;
            if (!sourceNode.value_type_uri || !targetNode.value_type_uri) return;
            if (sourceNode.value_type_uri === targetNode.value_type_uri) {
                toast.error('Kies twee claims van verschillende waardetypen.');
                return;
            }

            setPendingConnection({
                sourceNodeId: connection.source,
                targetNodeId: connection.target,
                sourceLabel: sourceNode.claim_content,
                targetLabel: targetNode.claim_content,
                sourceVtUri: sourceNode.value_type_uri,
                targetVtUri: targetNode.value_type_uri,
            });
        },
        [],
    );

    const handleTensionConfirm = useCallback(
        async (description: string, context: string) => {
            if (!pendingConnection) return;
            try {
                await api.createValueTension(designSpaceId, {
                    value_type_a_uri: pendingConnection.sourceVtUri,
                    value_type_b_uri: pendingConnection.targetVtUri,
                    description,
                    tension_context: context || undefined,
                });
                toast.success('Waardespanning aangemaakt.');
                setPendingConnection(null);

                // Transitieve check
                const isTransitive = await api.checkTransitiveTension(
                    designSpaceId,
                    pendingConnection.sourceVtUri,
                    pendingConnection.targetVtUri,
                );
                if (isTransitive) {
                    toast.info(`Transitieve spanning: er bestaat al een indirecte verbinding tussen "${pendingConnection.sourceLabel}" en "${pendingConnection.targetLabel}".`);
                }

                await load();
            } catch {
                toast.error('Fout bij het aanmaken van de spanning.');
            }
        },
        [pendingConnection, designSpaceId, load],
    );

    return (
        <div className="h-full w-full">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={handleConnect}
                onNodeDoubleClick={handleNodeDoubleClick}
                onEdgeDoubleClick={handleEdgeDoubleClick}
                nodeTypes={NODE_TYPES}
                edgeTypes={EDGE_TYPES}
                connectionMode={ConnectionMode.Loose}
                proOptions={{ hideAttribution: true }}
            >
                <Background />
                <AutoFitView shouldFitRef={shouldFitRef} />
            </ReactFlow>

            <CreateTensionDialog
                pending={pendingConnection}
                designSpaceId={designSpaceId}
                onConfirm={handleTensionConfirm}
                onClose={() => setPendingConnection(null)}
            />

            <EditTensionDialog
                tension={editingTension}
                designSpaceId={designSpaceId}
                onClose={() => setEditingTension(null)}
                onSaved={load}
            />
        </div>
    );
}
