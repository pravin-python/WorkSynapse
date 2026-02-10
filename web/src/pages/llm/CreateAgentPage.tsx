/**
 * Create AI Agent Page
 * =====================
 * 
 * Create a new AI agent with provider selection, model choice, and API key validation.
 * Shows warning modal if no API key exists for selected provider.
 */
import React, { useState, useEffect } from 'react';
import {
    Bot, Sparkles, AlertTriangle, Key,
    ChevronRight, Check, Settings, Loader2
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/apiClient';
import './CreateAgent.css';
import { toast } from 'react-hot-toast';

// Types
interface LLMProvider {
    id: number;
    name: string;
    display_name: string;
    type: string;
    has_api_key: boolean;
    key_count: number;
}

interface LLMApiKey {
    id: number;
    provider_id: number;
    label: string;
    key_preview: string;
}

interface AgentModel {
    id: number;
    name: string;
    display_name: string;
}

interface AgentForm {
    name: string;
    description: string;
    provider_id: number;
    model_name: string;
    api_key_id: number;
    type: string;
    temperature: number;
    max_tokens: number;
    system_prompt: string;
    is_public: boolean;
}

const agentTypes = [
    { value: 'assistant', label: 'General Assistant', icon: '💬' },
    { value: 'planning', label: 'Project Planner', icon: '📋' },
    { value: 'code_review', label: 'Code Reviewer', icon: '🔍' },
    { value: 'documentation', label: 'Documentation Writer', icon: '📝' },
    { value: 'analytics', label: 'Data Analyst', icon: '📊' },
    { value: 'custom', label: 'Custom Agent', icon: '⚙️' },
];

export function CreateAgentPage() {
    const navigate = useNavigate();
    useAuth(); // Auth context for user verification

    const [step, setStep] = useState(1);
    const [providers, setProviders] = useState<LLMProvider[]>([]);
    const [allKeys, setAllKeys] = useState<LLMApiKey[]>([]);
    const [providersLoading, setProvidersLoading] = useState(true);

    // Derived state for the current step
    const [providerModels, setProviderModels] = useState<AgentModel[]>([]);
    const [modelsLoading, setModelsLoading] = useState(false);

    const [availableKeys, setAvailableKeys] = useState<LLMApiKey[]>([]);
    const [showKeyWarning, setShowKeyWarning] = useState(false);
    const [selectedProvider, setSelectedProvider] = useState<LLMProvider | null>(null);

    const [form, setForm] = useState<AgentForm>({
        name: '',
        description: '',
        provider_id: 0,
        model_name: '',
        api_key_id: 0,
        type: 'assistant',
        temperature: 0.7,
        max_tokens: 4096,
        system_prompt: '',
        is_public: false
    });

    const [errors, setErrors] = useState<Record<string, string>>({});

    // Fetch Providers and Keys on mount
    useEffect(() => {
        const fetchData = async () => {
            try {
                setProvidersLoading(true);
                const [providersRes, keysRes] = await Promise.all([
                    api.get<LLMProvider[]>('/llm/providers'),
                    api.get<LLMApiKey[]>('/llm/keys')
                ]);
                setProviders(providersRes);
                setAllKeys(keysRes);
            } catch (error) {
                console.error('Failed to fetch data:', error);
                toast.error('Failed to load providers. Please try again.');
            } finally {
                setProvidersLoading(false);
            }
        };

        fetchData();
    }, []);

    const fetchModels = async (providerId: number) => {
        try {
            setModelsLoading(true);
            const models = await api.get<AgentModel[]>(`/llm/providers/${providerId}/models`);
            setProviderModels(models);

            // Auto-select first model if available
            if (models.length > 0) {
                setForm(f => ({ ...f, model_name: models[0].name }));
            } else {
                setForm(f => ({ ...f, model_name: '' }));
            }
        } catch (error) {
            console.error('Failed to fetch models:', error);
            toast.error('Failed to load models for this provider.');
        } finally {
            setModelsLoading(false);
        }
    };

    const handleProviderSelect = async (provider: LLMProvider) => {
        setSelectedProvider(provider);
        setForm({ ...form, provider_id: provider.id, api_key_id: 0 }); // Reset key when provider changes

        // Fetch models for this provider
        await fetchModels(provider.id);

        // Filter keys for this provider
        const keys = allKeys.filter(k => k.provider_id === provider.id);
        setAvailableKeys(keys);

        // Check key requirement
        // Note: Ollama (local) usually doesn't need a key, but the provider object tells us has_api_key
        // Update: check provider.name for ollama specific logic if needed, but backend handles has_api_key
        if (!provider.has_api_key && provider.name !== 'ollama') {
            setShowKeyWarning(true);
        } else {
            setShowKeyWarning(false);
            // Auto-select key if only one exists
            if (keys.length === 1) {
                setForm(f => ({ ...f, api_key_id: keys[0].id }));
            }
            setStep(2);
        }
    };

    const handleModelSelect = (modelName: string) => {
        setForm({ ...form, model_name: modelName });
    };

    const handleKeySelect = (keyId: number) => {
        setForm({ ...form, api_key_id: keyId });
    };

    const validateForm = (): boolean => {
        const newErrors: Record<string, string> = {};

        if (!form.name.trim()) {
            newErrors.name = 'Agent name is required';
        } else if (form.name.length < 3) {
            newErrors.name = 'Name must be at least 3 characters';
        }

        if (!form.provider_id) {
            newErrors.provider = 'Please select a provider';
        }

        if (!form.model_name) {
            newErrors.model = 'Please select a model';
        }

        if (selectedProvider?.name !== 'ollama' && availableKeys.length > 0 && !form.api_key_id) {
            // Enforce key selection if keys are available and not ollama
            // Note: If no keys avail, we already showed warning or let them proceed if not required?
            // Backend requires key for most providers.
            newErrors.api_key = 'Please select an API key';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) return;

        try {
            await api.post('/llm/agents', form);
            toast.success('Agent created successfully!');
            navigate('/ai/agents');
        } catch (error: any) {
            console.error('Failed to create agent:', error);
            toast.error(error.response?.data?.detail || 'Failed to create agent');
        }
    };

    const getProviderIcon = (name: string) => {
        const icons: Record<string, string> = {
            openai: '🤖',
            anthropic: '🔮',
            google: '🌐',
            ollama: '🖥️',
            gemini: '✨',
            groq: '⚡',
        };
        return icons[name.toLowerCase()] || '🔑';
    };

    if (providersLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="animate-spin text-primary" size={32} />
            </div>
        );
    }

    return (
        <div className="create-agent-page">
            <header className="page-header">
                <div className="header-content">
                    <h1><Bot size={28} />Create AI Agent</h1>
                    <p>Configure a new AI agent for your workspace</p>
                </div>
            </header>

            {/* Progress Steps */}
            <div className="progress-steps">
                <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
                    <span className="step-number">1</span>
                    <span className="step-label">Select Provider</span>
                </div>
                <ChevronRight size={20} className="step-arrow" />
                <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
                    <span className="step-number">2</span>
                    <span className="step-label">Configure Agent</span>
                </div>
                <ChevronRight size={20} className="step-arrow" />
                <div className={`step ${step >= 3 ? 'active' : ''}`}>
                    <span className="step-number">3</span>
                    <span className="step-label">Review & Create</span>
                </div>
            </div>

            <form onSubmit={handleSubmit}>
                {/* Step 1: Provider Selection */}
                {step === 1 && (
                    <section className="form-section">
                        <h2>Select LLM Provider</h2>
                        <p className="section-desc">Choose the AI provider for your agent</p>

                        <div className="provider-selection">
                            {providers.map(provider => (
                                <div
                                    key={provider.id}
                                    className={`provider-option ${form.provider_id === provider.id ? 'selected' : ''} ${!provider.has_api_key && provider.name !== 'ollama' ? 'no-key' : ''}`}
                                    onClick={() => handleProviderSelect(provider)}
                                >
                                    <span className="provider-icon-lg">{getProviderIcon(provider.name)}</span>
                                    <div className="provider-info">
                                        <h4>{provider.display_name}</h4>
                                        <span className="model-count">{provider.type}</span>
                                    </div>
                                    {provider.has_api_key || provider.name === 'ollama' ? (
                                        <span className="key-status has-key"><Check size={14} /></span>
                                    ) : (
                                        <span className="key-status no-key"><AlertTriangle size={14} /></span>
                                    )}
                                </div>
                            ))}
                        </div>
                    </section>
                )}

                {/* Step 2: Agent Configuration */}
                {step === 2 && selectedProvider && (
                    <section className="form-section">
                        <h2>Configure Your Agent</h2>
                        <p className="section-desc">Set up the details for your AI agent</p>

                        <div className="form-grid">
                            {/* Basic Info */}
                            <div className="form-card">
                                <h3><Sparkles size={18} />Basic Information</h3>

                                <div className="form-group">
                                    <label>Agent Name *</label>
                                    <input
                                        type="text"
                                        value={form.name}
                                        onChange={e => setForm({ ...form, name: e.target.value })}
                                        placeholder="e.g., Code Review Assistant"
                                        className={`form-input ${errors.name ? 'error' : ''}`}
                                    />
                                    {errors.name && <span className="form-error">{errors.name}</span>}
                                </div>

                                <div className="form-group">
                                    <label>Description</label>
                                    <textarea
                                        value={form.description}
                                        onChange={e => setForm({ ...form, description: e.target.value })}
                                        placeholder="What does this agent do?"
                                        className="form-input"
                                        rows={3}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Agent Type</label>
                                    <div className="type-grid">
                                        {agentTypes.map(type => (
                                            <div
                                                key={type.value}
                                                className={`type-option ${form.type === type.value ? 'selected' : ''}`}
                                                onClick={() => setForm({ ...form, type: type.value })}
                                            >
                                                <span className="type-icon">{type.icon}</span>
                                                <span className="type-label">{type.label}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Model Selection */}
                            <div className="form-card">
                                <h3><Settings size={18} />Model Configuration</h3>

                                <div className="form-group">
                                    <label>Provider</label>
                                    <div className="selected-provider">
                                        <span>{getProviderIcon(selectedProvider.name)}</span>
                                        <span>{selectedProvider.display_name}</span>
                                        <button type="button" className="btn-link" onClick={() => setStep(1)}>Change</button>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Model *</label>
                                    {modelsLoading ? (
                                        <div className="loading-input">Loading models...</div>
                                    ) : (
                                        <select
                                            value={form.model_name}
                                            onChange={e => handleModelSelect(e.target.value)}
                                            className="form-input"
                                        >
                                            <option value="" disabled>Select a model</option>
                                            {providerModels.map(model => (
                                                <option key={model.id} value={model.name}>{model.display_name}</option>
                                            ))}
                                        </select>
                                    )}
                                    {errors.model && <span className="form-error">{errors.model}</span>}
                                </div>

                                {/* API Key Selection - Always show if keys exist (or even warn if empty) */}
                                {selectedProvider.name !== 'ollama' && (
                                    <div className="form-group">
                                        <label>API Key *</label>
                                        <select
                                            value={form.api_key_id}
                                            onChange={e => handleKeySelect(Number(e.target.value))}
                                            className={`form-input ${errors.api_key ? 'error' : ''}`}
                                            disabled={availableKeys.length === 0}
                                        >
                                            <option value="">
                                                {availableKeys.length === 0 ? "No keys available" : "Select a key..."}
                                            </option>
                                            {availableKeys.map(key => (
                                                <option key={key.id} value={key.id}>
                                                    {key.label} ({key.key_preview})
                                                </option>
                                            ))}
                                        </select>
                                        {errors.api_key && <span className="form-error">{errors.api_key}</span>}
                                        {availableKeys.length === 0 && (
                                            <button
                                                type="button"
                                                className="text-sm text-primary mt-2 underline"
                                                onClick={() => navigate('/llm/keys')}
                                            >
                                                Add API Key
                                            </button>
                                        )}
                                    </div>
                                )}

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Temperature</label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="2"
                                            step="0.1"
                                            value={form.temperature}
                                            onChange={e => setForm({ ...form, temperature: parseFloat(e.target.value) })}
                                            className="form-range"
                                        />
                                        <span className="range-value">{form.temperature}</span>
                                    </div>

                                    <div className="form-group">
                                        <label>Max Tokens</label>
                                        <input
                                            type="number"
                                            value={form.max_tokens}
                                            onChange={e => setForm({ ...form, max_tokens: parseInt(e.target.value) })}
                                            min={100}
                                            max={128000}
                                            className="form-input"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* System Prompt */}
                            <div className="form-card full-width">
                                <h3>System Prompt (Optional)</h3>
                                <textarea
                                    value={form.system_prompt}
                                    onChange={e => setForm({ ...form, system_prompt: e.target.value })}
                                    placeholder="You are a helpful assistant that..."
                                    className="form-input"
                                    rows={4}
                                />
                            </div>
                        </div>

                        <div className="form-actions">
                            <button type="button" className="btn btn-secondary" onClick={() => setStep(1)}>
                                Back
                            </button>
                            <button type="button" className="btn btn-primary" onClick={() => setStep(3)}>
                                Continue
                                <ChevronRight size={18} />
                            </button>
                        </div>
                    </section>
                )}

                {/* Step 3: Review */}
                {step === 3 && selectedProvider && (
                    <section className="form-section">
                        <h2>Review & Create</h2>
                        <p className="section-desc">Review your agent configuration before creating</p>

                        <div className="review-card">
                            <div className="review-header">
                                <div className="review-icon">
                                    <Bot size={32} />
                                </div>
                                <div>
                                    <h3>{form.name || 'Unnamed Agent'}</h3>
                                    <p>{form.description || 'No description'}</p>
                                </div>
                            </div>

                            <div className="review-details">
                                <div className="review-item">
                                    <span className="label">Provider</span>
                                    <span className="value">{selectedProvider.display_name}</span>
                                </div>
                                <div className="review-item">
                                    <span className="label">Model</span>
                                    <span className="value">{form.model_name}</span>
                                </div>
                                <div className="review-item">
                                    <span className="label">Type</span>
                                    <span className="value">{agentTypes.find(t => t.value === form.type)?.label}</span>
                                </div>
                                <div className="review-item">
                                    <span className="label">Temperature</span>
                                    <span className="value">{form.temperature}</span>
                                </div>
                                <div className="review-item">
                                    <span className="label">Max Tokens</span>
                                    <span className="value">{form.max_tokens.toLocaleString()}</span>
                                </div>
                            </div>
                        </div>

                        <div className="form-actions">
                            <button type="button" className="btn btn-secondary" onClick={() => setStep(2)}>
                                Back
                            </button>
                            <button type="submit" className="btn btn-primary">
                                <Bot size={18} />
                                Create Agent
                            </button>
                        </div>
                    </section>
                )}
            </form>

            {/* No API Key Warning Modal */}
            {showKeyWarning && selectedProvider && (
                <div className="modal-backdrop" onClick={() => setShowKeyWarning(false)}>
                    <div className="modal-content warning-modal" onClick={e => e.stopPropagation()}>
                        <div className="warning-icon">
                            <AlertTriangle size={48} />
                        </div>
                        <h3>API Key Required</h3>
                        <p>
                            You don't have an API key for <strong>{selectedProvider.display_name}</strong>.
                            Please add an API key before creating an agent with this provider.
                        </p>
                        <div className="modal-actions">
                            <button className="btn btn-secondary" onClick={() => setShowKeyWarning(false)}>
                                Choose Another Provider
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => navigate('/llm/keys')}
                            >
                                <Key size={16} />
                                Add API Key
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default CreateAgentPage;
