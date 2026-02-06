/**
 * Add API Key Modal Component
 * ===========================
 * 
 * Modal for adding new keys with support for dynamic provider configurations.
 */
import React, { useState } from 'react';
import { Key, Eye, EyeOff, Shield, X, AlertTriangle, ExternalLink } from 'lucide-react';
import { LLMProvider, validateApiKeyFormat } from '../api/aiModelsService';
import './AddApiKeyModal.css';

interface AddApiKeyModalProps {
    provider: LLMProvider;
    onClose: () => void;
    onSubmit: (data: { provider_id: number; api_key: string; label: string; extra_params?: any }) => Promise<void>;
    loading?: boolean;
}

export function AddApiKeyModal({ provider, onClose, onSubmit, loading }: AddApiKeyModalProps) {
    const [label, setLabel] = useState('default');
    const [apiKey, setApiKey] = useState('');
    const [extraParams, setExtraParams] = useState<Record<string, string>>({});
    const [showKey, setShowKey] = useState(false);
    const [error, setError] = useState('');

    const configSchema = provider.config_schema;
    const fields = configSchema?.fields || [];
    const helpLink = configSchema?.help_link;
    const useApiKeyField = configSchema?.use_api_key_field !== false;

    // Initialize defaults if needed
    React.useEffect(() => {
        if (fields.length > 0) {
            const defaults: Record<string, string> = {};
            fields.forEach((f: any) => {
                if (f.default) defaults[f.name] = f.default;
            });
            setExtraParams(prev => ({ ...defaults, ...prev }));
        }
    }, [fields]);

    const getKeyHint = () => {
        if (!useApiKeyField) return '';
        const hints: Record<string, string> = {
            openai: "Keys start with 'sk-'",
            anthropic: "Keys start with 'sk-ant-'",
            huggingface: "Keys start with 'hf_'",
            google: "Get your key from Google AI Studio",
            gemini: "Get your key from Google AI Studio",
            deepseek: "Start with 'sk-' from DeepSeek Platform",
            groq: "Start with 'gsk_'",
            azure_openai: "Your Azure OpenAI API Key 1 or 2",
        };
        return hints[provider.type.toLowerCase()] || '';
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validate key format only if standard field usage
        if (useApiKeyField) {
            const validation = validateApiKeyFormat(apiKey, provider.type);
            if (!validation.valid) {
                setError(validation.error);
                return;
            }
        }

        // Validate extra params
        for (const field of fields) {
            if (field.required && !extraParams[field.name]) {
                setError(`${field.label} is required`);
                return;
            }
        }

        try {
            await onSubmit({
                provider_id: provider.id,
                api_key: apiKey || 'dummy_for_schema_validation', // Backend might ignore if use_api_key_field is false, but valid requires length
                label: label || 'default',
                extra_params: Object.keys(extraParams).length > 0 ? extraParams : undefined
            });
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Failed to save API key');
        }
    };

    const handleParamChange = (name: string, value: string) => {
        setExtraParams(prev => ({ ...prev, [name]: value }));
        setError('');
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="add-key-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>
                        <Key size={20} />
                        Add {provider.display_name} Credentials
                    </h3>
                    <button className="btn-close" onClick={onClose} disabled={loading}>
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="key-label">Label</label>
                        <input
                            id="key-label"
                            type="text"
                            value={label}
                            onChange={e => setLabel(e.target.value)}
                            placeholder="e.g., Production, Development"
                            className="form-input"
                            disabled={loading}
                        />
                        <span className="form-hint">
                            A name to identify this key (optional)
                        </span>
                    </div>

                    {useApiKeyField && (
                        <div className="form-group">
                            <label htmlFor="api-key">API Key</label>
                            <div className="input-with-toggle">
                                <input
                                    id="api-key"
                                    type={showKey ? 'text' : 'password'}
                                    value={apiKey}
                                    onChange={e => {
                                        setApiKey(e.target.value);
                                        setError('');
                                    }}
                                    placeholder={`Enter your ${provider.display_name} API key`}
                                    className="form-input"
                                    required
                                    disabled={loading}
                                    autoComplete="off"
                                />
                                <button
                                    type="button"
                                    className="toggle-visibility"
                                    onClick={() => setShowKey(!showKey)}
                                    disabled={loading}
                                >
                                    {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                            {getKeyHint() && (
                                <span className="form-hint">{getKeyHint()}</span>
                            )}
                        </div>
                    )}

                    {/* Dynamic Extra Fields */}
                    {fields.map((field: any) => (
                        <div className="form-group" key={field.name}>
                            <label htmlFor={field.name}>{field.label}</label>
                            {field.type === 'textarea' ? (
                                <textarea
                                    id={field.name}
                                    value={extraParams[field.name] || ''}
                                    onChange={e => handleParamChange(field.name, e.target.value)}
                                    placeholder={field.placeholder}
                                    className="form-input"
                                    required={field.required}
                                    disabled={loading}
                                />
                            ) : (
                                <input
                                    id={field.name}
                                    type={field.type || 'text'}
                                    value={extraParams[field.name] || ''}
                                    onChange={e => handleParamChange(field.name, e.target.value)}
                                    placeholder={field.placeholder}
                                    className="form-input"
                                    required={field.required}
                                    disabled={loading}
                                />
                            )}
                        </div>
                    ))}

                    {/* Help Link */}
                    {helpLink && (
                        <div className="help-link-section">
                            <span>Need credentials? </span>
                            <a href={helpLink} target="_blank" rel="noopener noreferrer" className="provider-help-link">
                                Get API key / Purchase access <ExternalLink size={12} style={{ marginLeft: 4 }} />
                            </a>
                        </div>
                    )}

                    {error && (
                        <div className="alert alert-error">
                            <AlertTriangle size={16} />
                            {error}
                        </div>
                    )}

                    <div className="security-notice">
                        <Shield size={16} />
                        <span>
                            Your credentials will be encrypted using <strong>Fernet (AES-128)</strong> symmetric encryption before storage.
                        </span>
                    </div>

                    <div className="modal-actions">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={onClose}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner" />
                                    Encrypting...
                                </>
                            ) : (
                                <>
                                    <Key size={16} />
                                    Save Encrypted Credentials
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default AddApiKeyModal;
