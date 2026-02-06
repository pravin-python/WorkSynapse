/**
 * API Key Table Component
 * =======================
 * 
 * Displays a table of encrypted API keys with actions.
 */
import { Key, Trash2, Check, X, Edit2, Power, PowerOff } from 'lucide-react';
import { LLMApiKey } from '../api/aiModelsService';
import './ApiKeyTable.css';

interface ApiKeyTableProps {
    keys: LLMApiKey[];
    onDelete: (keyId: number) => void;
    onEdit?: (key: LLMApiKey) => void;
    onToggleActive?: (key: LLMApiKey) => void;
    loading?: boolean;
}

export function ApiKeyTable({
    keys,
    onDelete,
    onEdit,
    onToggleActive,
    loading
}: ApiKeyTableProps) {
    if (keys.length === 0) {
        return (
            <div className="api-keys-empty">
                <Key size={48} className="empty-icon" />
                <h3>No API keys yet</h3>
                <p>Add API keys for your preferred LLM providers above</p>
            </div>
        );
    }

    const formatDate = (dateString: string | null) => {
        if (!dateString) return 'Never';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    return (
        <div className={`api-keys-table-container ${loading ? 'loading' : ''}`}>
            <table className="api-keys-table">
                <thead>
                    <tr>
                        <th>Provider</th>
                        <th>Label</th>
                        <th>Key Preview</th>
                        <th>Status</th>
                        <th>Usage</th>
                        <th>Last Used</th>
                        <th>Added</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {keys.map(key => (
                        <tr key={key.id} className={!key.is_active ? 'inactive' : ''}>
                            <td>
                                <strong>{key.provider_name}</strong>
                            </td>
                            <td>{key.label}</td>
                            <td>
                                <code className="key-preview">{key.key_preview}</code>
                            </td>
                            <td>
                                {key.is_valid && key.is_active ? (
                                    <span className="status-badge success">
                                        <Check size={12} /> Valid
                                    </span>
                                ) : !key.is_active ? (
                                    <span className="status-badge warning">
                                        <PowerOff size={12} /> Inactive
                                    </span>
                                ) : (
                                    <span className="status-badge error">
                                        <X size={12} /> Invalid
                                    </span>
                                )}
                            </td>
                            <td>
                                <span className="usage-count">{key.usage_count.toLocaleString()} calls</span>
                            </td>
                            <td>
                                <span className="date-cell">{formatDate(key.last_used_at)}</span>
                            </td>
                            <td>
                                <span className="date-cell">{formatDate(key.created_at)}</span>
                            </td>
                            <td>
                                <div className="key-actions">
                                    {onEdit && (
                                        <button
                                            className="btn-icon"
                                            onClick={() => onEdit(key)}
                                            title="Edit key"
                                        >
                                            <Edit2 size={16} />
                                        </button>
                                    )}
                                    {onToggleActive && (
                                        <button
                                            className={`btn-icon ${key.is_active ? '' : 'success'}`}
                                            onClick={() => onToggleActive(key)}
                                            title={key.is_active ? 'Deactivate key' : 'Activate key'}
                                        >
                                            {key.is_active ? <PowerOff size={16} /> : <Power size={16} />}
                                        </button>
                                    )}
                                    <button
                                        className="btn-icon danger"
                                        onClick={() => onDelete(key.id)}
                                        title="Delete key"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default ApiKeyTable;
