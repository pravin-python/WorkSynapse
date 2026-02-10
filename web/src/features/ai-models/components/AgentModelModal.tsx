import { useState, useEffect } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { AgentModel, AgentModelCreate, AgentModelUpdate, getProviders, LLMProvider } from '../api/aiModelsService';

interface ModelModalProps {
    model?: AgentModel; // If exists, it's edit mode
    onClose: () => void;
    onSubmit: (data: AgentModelCreate | AgentModelUpdate) => Promise<void>;
}

export function AgentModelModal({ model, onClose, onSubmit }: ModelModalProps) {
    const isEdit = !!model;
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [providers, setProviders] = useState<LLMProvider[]>([]);

    // Load available providers
    useEffect(() => {
        getProviders().then(setProviders).catch(console.error);
    }, []);

    // Form State
    const [formData, setFormData] = useState<Partial<AgentModelCreate>>({
        name: model?.name || '',
        display_name: model?.display_name || '',
        provider_id: model?.provider_id || 0,
        description: model?.description || '',
        base_url: model?.base_url || '',
        requires_api_key: model?.requires_api_key ?? true,
        api_key_prefix: model?.api_key_prefix || '',
        context_window: model?.context_window || 4096,
        max_output_tokens: model?.max_output_tokens || 4096,
        supports_vision: model?.supports_vision || false,
        supports_tools: model?.supports_tools || true,
        supports_streaming: model?.supports_streaming || true,
        input_price_per_million: model?.input_price_per_million || 0,
        output_price_per_million: model?.output_price_per_million || 0,
    });

    // Set default provider if not set (for create mode)
    useEffect(() => {
        if (!isEdit && !formData.provider_id && providers.length > 0) {
            setFormData(prev => ({ ...prev, provider_id: providers[0].id }));
        }
    }, [isEdit, formData.provider_id, providers]);

    // Status flags for editing
    const [statusFlags, setStatusFlags] = useState({
        is_active: model?.is_active ?? true,
        is_deprecated: model?.is_deprecated ?? false
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            if (isEdit) {
                // Update mode
                const updateData: AgentModelUpdate = {
                    display_name: formData.display_name,
                    description: formData.description,
                    input_price_per_million: Number(formData.input_price_per_million),
                    output_price_per_million: Number(formData.output_price_per_million),
                    is_active: statusFlags.is_active,
                    is_deprecated: statusFlags.is_deprecated,
                };
                // Hack: extend the object
                await onSubmit({ ...updateData, ...formData } as any);
            } else {
                // Create mode
                if (!formData.provider_id) {
                    throw new Error("Provider is required");
                }
                await onSubmit(formData as AgentModelCreate);
            }
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Failed to save model');
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (field: string, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="modal-backdrop">
            <div className="modal-content model-modal">
                <div className="modal-header">
                    <h2>{isEdit ? 'Edit AI Model' : 'Add New AI Model'}</h2>
                    <button className="close-btn" onClick={onClose}><X size={20} /></button>
                </div>

                {error && (
                    <div className="alert alert-error">
                        <AlertTriangle size={16} />
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="form-grid">
                        {/* Basic Info */}
                        <div className="form-group">
                            <label>Model Internal Name {isEdit && <span className="locked-badge">Locked</span>}</label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={e => handleChange('name', e.target.value)}
                                disabled={isEdit}
                                placeholder="e.g. gpt-4-turbo"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Display Name</label>
                            <input
                                type="text"
                                value={formData.display_name}
                                onChange={e => handleChange('display_name', e.target.value)}
                                placeholder="e.g. GPT-4 Turbo"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Provider {isEdit && <span className="locked-badge">Locked</span>}</label>
                            <select
                                value={formData.provider_id}
                                onChange={e => handleChange('provider_id', Number(e.target.value))}
                                disabled={isEdit}
                                required
                            >
                                <option value={0} disabled>Select Provider</option>
                                {providers.map(p => (
                                    <option key={p.id} value={p.id}>{p.display_name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group full-width">
                            <label>Description</label>
                            <textarea
                                value={formData.description}
                                onChange={e => handleChange('description', e.target.value)}
                                rows={2}
                            />
                        </div>

                        {/* Config */}
                        <div className="form-group">
                            <label>Context Window</label>
                            <input
                                type="number"
                                value={formData.context_window}
                                onChange={e => handleChange('context_window', parseInt(e.target.value))}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Max Output Tokens</label>
                            <input
                                type="number"
                                value={formData.max_output_tokens}
                                onChange={e => handleChange('max_output_tokens', parseInt(e.target.value))}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Input Price ($ / 1M)</label>
                            <input
                                type="number"
                                step="0.000001"
                                value={formData.input_price_per_million}
                                onChange={e => handleChange('input_price_per_million', parseFloat(e.target.value))}
                            />
                        </div>

                        <div className="form-group">
                            <label>Output Price ($ / 1M)</label>
                            <input
                                type="number"
                                step="0.000001"
                                value={formData.output_price_per_million}
                                onChange={e => handleChange('output_price_per_million', parseFloat(e.target.value))}
                            />
                        </div>

                        {/* API Config */}
                        <div className="form-group full-width">
                            <label>Base URL (Optional)</label>
                            <input
                                type="text"
                                value={formData.base_url}
                                onChange={e => handleChange('base_url', e.target.value)}
                                placeholder="https://api.example.com/v1"
                            />
                        </div>

                        {/* Toggles Group 1 */}
                        <div className="toggles-row full-width">
                            <label className="toggle-label">
                                <input
                                    type="checkbox"
                                    checked={formData.requires_api_key}
                                    onChange={e => handleChange('requires_api_key', e.target.checked)}
                                />
                                Requires API Key
                            </label>

                            {formData.requires_api_key && (
                                <div className="prefix-input-group">
                                    <input
                                        type="text"
                                        className="inline-input"
                                        placeholder="Prefix (e.g. sk-)"
                                        value={formData.api_key_prefix}
                                        onChange={e => handleChange('api_key_prefix', e.target.value)}
                                        title="Enter the key prefix (not the full key)"
                                    />
                                    {formData.api_key_prefix && formData.api_key_prefix.length > 20 && (
                                        <div className="input-warning" style={{ fontSize: '0.7rem', color: 'orange', marginTop: '4px' }}>
                                            Warning: This looks like a full key. This field is for the prefix only.
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Toggles Group 2 */}
                        <div className="toggles-row full-width">
                            <label className="toggle-label">
                                <input
                                    type="checkbox"
                                    checked={formData.supports_vision}
                                    onChange={e => handleChange('supports_vision', e.target.checked)}
                                />
                                Vision
                            </label>
                            <label className="toggle-label">
                                <input
                                    type="checkbox"
                                    checked={formData.supports_tools}
                                    onChange={e => handleChange('supports_tools', e.target.checked)}
                                />
                                Tools
                            </label>
                            <label className="toggle-label">
                                <input
                                    type="checkbox"
                                    checked={formData.supports_streaming}
                                    onChange={e => handleChange('supports_streaming', e.target.checked)}
                                />
                                Streaming
                            </label>
                        </div>

                        {/* Status Flags (Edit Only) */}
                        {isEdit && (
                            <div className="toggles-row full-width status-flags">
                                <label className="toggle-label status-active">
                                    <input
                                        type="checkbox"
                                        checked={statusFlags.is_active}
                                        onChange={e => setStatusFlags(p => ({ ...p, is_active: e.target.checked }))}
                                    />
                                    Active
                                </label>
                                <label className="toggle-label status-deprecated">
                                    <input
                                        type="checkbox"
                                        checked={statusFlags.is_deprecated}
                                        onChange={e => setStatusFlags(p => ({ ...p, is_deprecated: e.target.checked }))}
                                    />
                                    Deprecated
                                </label>
                            </div>
                        )}
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn-text" onClick={onClose} disabled={loading}>
                            Cancel
                        </button>
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? 'Saving...' : (isEdit ? 'Update Model' : 'Create Model')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
