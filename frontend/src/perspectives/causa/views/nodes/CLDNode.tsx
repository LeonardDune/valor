import type { FunctionComponent } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';

// Strict "Academic" styling: Simple white circle with black border and centered label.
const nodeStyle = {
    background: '#fff',
    border: '2px solid #333',
    borderRadius: '50%',
    width: 50,
    height: 50,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    fontSize: '10px',
    fontWeight: 'bold',
    color: '#333',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
};

const CLDNode: FunctionComponent<NodeProps> = ({ data }) => {
    return (
        <div style={nodeStyle}>
            {/* Handles are hidden visually but required for connections */}
            <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
            <div>{data.label}</div>
            <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
        </div>
    );
};

export default CLDNode;
