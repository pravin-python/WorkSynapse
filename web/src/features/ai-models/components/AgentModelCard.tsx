import { useState, useEffect } from 'react';
import {
    Eye, Wrench, Zap, Key, MoreVertical, Database
} from 'lucide-react';
import aiModelsService, { AgentModel } from '../api/aiModelsService';
// import './AgentModelCard.css'; // Will use AIModelsPage.css for now or add new styles

interface AgentModelCardProps {
    model: AgentModel;
    onEdit: (model: AgentModel) => void;
    onDelete: (model: AgentModel) => void;
}

export function AgentModelCard({ model, onEdit, onDelete }: AgentModelCardProps) {
    const [showMenu, setShowMenu] = useState(false);

    // Close menu when clicking outside (simple implementation)
    useEffect(() => {
        const handleClickOutside = () => setShowMenu(false);
        if (showMenu) {
            document.addEventListener('click', handleClickOutside);
        }
        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    }, [showMenu]);

    const getStatusClass = (model: AgentModel) => {
        if (model.is_deprecated) return 'status-deprecated';
        if (!model.is_active) return 'status-inactive';
        return 'status-active';
    };

    const getStatusText = (model: AgentModel) => {
        if (model.is_deprecated) return 'Deprecated';
        if (!model.is_active) return 'Inactive';
        return 'Active';
    };

    return (
        <div className={`provider-card agent-model-card ${getStatusClass(model)}`}>
            {/* Header */}
            <div className="card-header">
                <div className="provider-icon">
                    {/* Use provider icon if available, or generic CPU */}
                    {aiModelsService.getProviderIcon(model.provider?.type || '')}
                </div>
                <div className="provider-info">
                    <h3>{model.display_name}</h3>
                    <div className="model-badges">
                        <span className="badge provider-badge">{model.provider?.display_name || 'Unknown'}</span>
                        <span className={`badge status-badge ${getStatusClass(model)}`}>
                            {getStatusText(model)}
                        </span>
                    </div>
                </div>
                <div className="card-actions-menu-container" onClick={e => e.stopPropagation()}>
                    <button
                        className="btn-icon"
                        onClick={() => setShowMenu(!showMenu)}
                        title="Actions"
                    >
                        <MoreVertical size={16} />
                    </button>
                    {showMenu && (
                        <div className="dropdown-menu">
                            <button onClick={() => onEdit(model)}>Edit Model</button>
                            <button
                                className="warning"
                                onClick={() => onEdit(model)}
                                title="Configure model status and settings"
                            >
                                Configure
                            </button>
                            <button className="danger" onClick={() => onDelete(model)}>
                                Soft Delete
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Description */}
            <p className="provider-description">
                {model.description || 'No description available for this AI model.'}
            </p>

            {/* Specs Grid */}
            <div className="model-specs-grid">
                <div className="spec-item" title="Context Window">
                    <Database size={14} />
                    <span>{Math.round(model.context_window / 1024)}k</span>
                </div>
                <div className="spec-item" title="Vision Support">
                    <Eye size={14} className={model.supports_vision ? "supported" : "unsupported"} />
                </div>
                <div className="spec-item" title="Tool Use">
                    <Wrench size={14} className={model.supports_tools ? "supported" : "unsupported"} />
                </div>
                <div className="spec-item" title="Streaming">
                    <Zap size={14} className={model.supports_streaming ? "supported" : "unsupported"} />
                </div>
                {model.requires_api_key && (
                    <div className="spec-item" title="Requires API Key">
                        <Key size={14} />
                    </div>
                )}
            </div>

            {/* Pricing */}
            <div className="model-pricing">
                <div className="price-item">
                    <span className="price-label">In:</span>
                    <span className="price-value">${model.input_price_per_million}</span>
                </div>
                <div className="price-item">
                    <span className="price-label">Out:</span>
                    <span className="price-value">${model.output_price_per_million}</span>
                </div>
                <div className="price-per">/ 1M tokens</div>
            </div>
        </div>
    );
}
