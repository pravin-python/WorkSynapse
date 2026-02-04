/**
 * LLM Keys Management Page
 * ========================
 * 
 * Manage LLM API keys with encryption, validation, and provider selection.
 */
import React, { useState } from 'react';
import {
    Key, Plus, Shield, Eye, EyeOff, Trash2,
    Check, X, AlertTriangle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './LLMKeys.css';

// Types
interface LLMProvider {
    id: number;
    name: string;
    display_name: string;
    description: string;
    icon: string;
    requires_api_key: boolean;
    available_models: string[];
    has_api_key: boolean;
    key_count: number;
}

interface LLMApiKey {
    id: number;
    provider_id: number;
    provider_name: string;
    label: string;
    key_preview: string;
    is_active: boolean;
    is_valid: boolean;
    usage_count: number;
    created_at: string;
}

// Mock data for demo
const mockProviders: LLMProvider[] = [
    { id: 1, name: 'openai', display_name: 'OpenAI', description: 'GPT-4, GPT-3.5 and other OpenAI models', icon: 'openai', requires_api_key: true, available_models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'], has_api_key: true, key_count: 1 },
    { id: 2, name: 'anthropic', display_name: 'Anthropic', description: 'Claude 3 family of models', icon: 'anthropic', requires_api_key: true, available_models: ['claude-3-5-sonnet-latest', 'claude-3-opus-latest'], has_api_key: false, key_count: 0 },
    { id: 3, name: 'google', display_name: 'Google AI', description: 'Gemini Pro and other Google models', icon: 'google', requires_api_key: true, available_models: ['gemini-1.5-pro', 'gemini-1.5-flash'], has_api_key: false, key_count: 0 },
    { id: 4, name: 'huggingface', display_name: 'HuggingFace', description: 'Open source models via HuggingFace API', icon: 'huggingface', requires_api_key: true, available_models: ['meta-llama/Llama-3.1-8B-Instruct'], has_api_key: false, key_count: 0 },
    { id: 5, name: 'ollama', display_name: 'Ollama (Local)', description: 'Run models locally with Ollama', icon: 'server', requires_api_key: false, available_models: ['llama3.1', 'mistral', 'codellama'], has_api_key: true, key_count: 0 },
];

const mockKeys: LLMApiKey[] = [
    { id: 1, provider_id: 1, provider_name: 'OpenAI', label: 'Production Key', key_preview: 'sk-ab...xyz', is_active: true, is_valid: true, usage_count: 156, created_at: '2024-01-15' },
];

export function LLMKeysPage() {
    const { } = useAuth();
    const [providers, setProviders] = useState<LLMProvider[]>(mockProviders);
    const [keys, setKeys] = useState<LLMApiKey[]>(mockKeys);
    const [selectedProvider, setSelectedProvider] = useState<LLMProvider | null>(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showKeyValue, setShowKeyValue] = useState(false);
    const [newKey, setNewKey] = useState({ label: '', api_key: '', provider_id: 0 });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleAddKey = (provider: LLMProvider) => {
        setSelectedProvider(provider);
        setNewKey({ label: 'default', api_key: '', provider_id: provider.id });
        setShowAddModal(true);
        setError('');
    };

    const validateKeyFormat = (key: string, providerName: string): { valid: boolean; error: string } => {
        if (!key || key.length < 10) {
            return { valid: false, error: 'API key is too short' };
        }

        const validations: Record<string, { prefix: string; minLength: number }> = {
            openai: { prefix: 'sk-', minLength: 40 },
            anthropic: { prefix: 'sk-ant-', minLength: 40 },
            huggingface: { prefix: 'hf_', minLength: 20 },
        };

        const rule = validations[providerName.toLowerCase()];
        if (rule) {
            if (!key.startsWith(rule.prefix)) {
                return { valid: false, error: `${providerName} keys should start with '${rule.prefix}'` };
            }
            if (key.length < rule.minLength) {
                return { valid: false, error: `Key should be at least ${rule.minLength} characters` };
            }
        }

        return { valid: true, error: '' };
    };

    const handleSubmitKey = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!selectedProvider) return;

        // Validate key format
        const validation = validateKeyFormat(newKey.api_key, selectedProvider.name);
        if (!validation.valid) {
            setError(validation.error);
            return;
        }

        // Simulate API call
        const maskedKey = `${newKey.api_key.slice(0, 5)}...${newKey.api_key.slice(-4)}`;
        const newKeyEntry: LLMApiKey = {
            id: Date.now(),
            provider_id: selectedProvider.id,
            provider_name: selectedProvider.display_name,
            label: newKey.label || 'default',
            key_preview: maskedKey,
            is_active: true,
            is_valid: true,
            usage_count: 0,
            created_at: new Date().toISOString().split('T')[0],
        };

        setKeys([...keys, newKeyEntry]);
        setProviders(providers.map(p =>
            p.id === selectedProvider.id
                ? { ...p, has_api_key: true, key_count: p.key_count + 1 }
                : p
        ));

        setShowAddModal(false);
        setNewKey({ label: '', api_key: '', provider_id: 0 });
        setSuccess(`API key for ${selectedProvider.display_name} added successfully!`);
        setTimeout(() => setSuccess(''), 3000);
    };

    const handleDeleteKey = (keyId: number) => {
        const keyToDelete = keys.find(k => k.id === keyId);
        if (!keyToDelete) return;

        setKeys(keys.filter(k => k.id !== keyId));
        setProviders(providers.map(p =>
            p.id === keyToDelete.provider_id
                ? { ...p, has_api_key: p.key_count - 1 > 0, key_count: p.key_count - 1 }
                : p
        ));
    };

    const getProviderIcon = (iconName: string) => {
        // Simple icon mapping - you can replace with actual provider logos
        const iconMap: Record<string, string> = {
            openai: '🤖',
            anthropic: '🔮',
            google: '🌐',
            huggingface: '🤗',
            server: '🖥️',
            cohere: '⚡',
        };
        return iconMap[iconName] || '🔑';
    };

    return (
        <div className="llm-keys-page">
            <header className="page-header">
                <div className="header-content">
                    <h1><Key size={28} />LLM API Keys</h1>
                    <p>Manage your encrypted API keys for AI providers</p>
                </div>
            </header>

            {success && (
                <div className="alert alert-success">
                    <Check size={18} />
                    {success}
                </div>
            )}

            {/* Providers Grid */}
            <section className="providers-section">
                <h2>Available Providers</h2>
                <div className="providers-grid">
                    {providers.map(provider => (
                        <div
                            key={provider.id}
                            className={`provider-card ${provider.has_api_key ? 'has-key' : ''}`}
                        >
                            <div className="provider-header">
                                <span className="provider-icon">{getProviderIcon(provider.icon)}</span>
                                <div className="provider-status">
                                    {provider.has_api_key ? (
                                        <span className="status-badge success">
                                            <Check size={12} /> {provider.key_count} key(s)
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

                            <h3>{provider.display_name}</h3>
                            <p>{provider.description}</p>

                            <div className="models-preview">
                                {provider.available_models.slice(0, 3).map(model => (
                                    <span key={model} className="model-tag">{model}</span>
                                ))}
                                {provider.available_models.length > 3 && (
                                    <span className="model-more">+{provider.available_models.length - 3}</span>
                                )}
                            </div>

                            {provider.requires_api_key && (
                                <button
                                    className="btn btn-secondary btn-sm"
                                    onClick={() => handleAddKey(provider)}
                                >
                                    <Plus size={14} />
                                    {provider.has_api_key ? 'Add Another Key' : 'Add API Key'}
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            </section>

            {/* Existing Keys */}
            <section className="keys-section">
                <h2><Shield size={20} />Your Encrypted Keys</h2>

                {keys.length === 0 ? (
                    <div className="empty-state">
                        <Key size={48} />
                        <h3>No API keys yet</h3>
                        <p>Add API keys for your preferred LLM providers above</p>
                    </div>
                ) : (
                    <div className="keys-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Provider</th>
                                    <th>Label</th>
                                    <th>Key Preview</th>
                                    <th>Status</th>
                                    <th>Usage</th>
                                    <th>Added</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {keys.map(key => (
                                    <tr key={key.id}>
                                        <td><strong>{key.provider_name}</strong></td>
                                        <td>{key.label}</td>
                                        <td><code>{key.key_preview}</code></td>
                                        <td>
                                            {key.is_valid && key.is_active ? (
                                                <span className="status-badge success"><Check size={12} /> Valid</span>
                                            ) : (
                                                <span className="status-badge error"><X size={12} /> Invalid</span>
                                            )}
                                        </td>
                                        <td>{key.usage_count} calls</td>
                                        <td>{key.created_at}</td>
                                        <td>
                                            <button
                                                className="btn-icon danger"
                                                onClick={() => handleDeleteKey(key.id)}
                                                title="Delete key"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {/* Add Key Modal */}
            {showAddModal && selectedProvider && (
                <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>
                                <Key size={20} />
                                Add API Key for {selectedProvider.display_name}
                            </h3>
                            <button className="btn-close" onClick={() => setShowAddModal(false)}>
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmitKey}>
                            <div className="form-group">
                                <label>Label</label>
                                <input
                                    type="text"
                                    value={newKey.label}
                                    onChange={e => setNewKey({ ...newKey, label: e.target.value })}
                                    placeholder="e.g., Production, Development"
                                    className="form-input"
                                />
                            </div>

                            <div className="form-group">
                                <label>API Key</label>
                                <div className="input-with-toggle">
                                    <input
                                        type={showKeyValue ? 'text' : 'password'}
                                        value={newKey.api_key}
                                        onChange={e => {
                                            setNewKey({ ...newKey, api_key: e.target.value });
                                            setError('');
                                        }}
                                        placeholder={`Enter your ${selectedProvider.display_name} API key`}
                                        className="form-input"
                                        required
                                    />
                                    <button
                                        type="button"
                                        className="toggle-visibility"
                                        onClick={() => setShowKeyValue(!showKeyValue)}
                                    >
                                        {showKeyValue ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                                <span className="form-hint">
                                    {selectedProvider.name === 'openai' && 'Keys start with sk-'}
                                    {selectedProvider.name === 'anthropic' && 'Keys start with sk-ant-'}
                                    {selectedProvider.name === 'huggingface' && 'Keys start with hf_'}
                                </span>
                            </div>

                            {error && (
                                <div className="alert alert-error">
                                    <AlertTriangle size={16} />
                                    {error}
                                </div>
                            )}

                            <div className="security-notice">
                                <Shield size={16} />
                                <span>Your key will be encrypted using Fernet encryption before storage.</span>
                            </div>

                            <div className="modal-actions">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary">
                                    <Key size={16} />
                                    Save Encrypted Key
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default LLMKeysPage;
