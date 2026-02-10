/**
 * Provider Card Component
 * =======================
 * 
 * Displays an AI model provider card with status and actions.
 */
import { Plus, Check, AlertTriangle, Settings, Trash2 } from 'lucide-react';
import { LLMProvider, getProviderIcon } from '../api/aiModelsService';
import './ProviderCard.css';

interface ProviderCardProps {
    provider: LLMProvider;
    onAddKey: (provider: LLMProvider) => void;
    onManage?: (provider: LLMProvider) => void;
    onDelete?: () => void;
}

export function ProviderCard({ provider, onAddKey, onManage, onDelete }: ProviderCardProps) {
    const icon = getProviderIcon(provider.type);

    return (
        <div className={`ai-provider-card ${provider.has_api_key ? 'has-key' : ''}`}>
            <div className="provider-card-header">
                <span className="provider-icon">{icon}</span>
                <div className="provider-status">
                    {provider.has_api_key ? (
                        <span className="status-badge success">
                            <Check size={12} /> {provider.key_count} key{provider.key_count !== 1 ? 's' : ''}
                        </span>
                    ) : provider.requires_api_key ? (
                        <span className="status-badge warning">
                            <AlertTriangle size={12} /> No key
                        </span>
                    ) : (
                        <span className="status-badge info">
                            <Check size={12} /> No key needed
                        </span>
                    )}
                </div>
            </div>

            <h3 className="provider-name">{provider.display_name}</h3>
            <p className="provider-description">{provider.description}</p>



            <div className="provider-actions">
                {provider.requires_api_key && (
                    <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onAddKey(provider)}
                    >
                        <Plus size={14} />
                        {provider.has_api_key ? 'Add Another Key' : 'Add API Key'}
                    </button>
                )}
                {onManage && provider.has_api_key && (
                    <button
                        className="btn-icon"
                        onClick={() => onManage(provider)}
                        title="Manage Provider"
                    >
                        <Settings size={16} />
                    </button>
                )}
                {onDelete && (
                    <button
                        className="btn-icon destructive"
                        onClick={onDelete}
                        title="Delete Provider"
                    >
                        <Trash2 size={16} />
                    </button>
                )}
            </div>
        </div>
    );
}

export default ProviderCard;
