/**
 * Agent Builder Form Component
 * ============================
 * 
 * A comprehensive form for creating and editing custom AI agents.
 * Includes sections for:
 * - Basic Info (name, description)
 * - Model Selection with API key validation
 * - Prompts (system, goal, service)
 * - Tools configuration
 * - Connections
 * - MCP Servers
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { agentBuilderApi, AgentModel, AgentApiKey, AvailableTool, CreateAgentDTO, UpdateAgentDTO, RagDocument, PromptTemplate, AgentAutonomyLevel } from '../api/agentBuilderApi';
import { localModelsService, LocalModel } from '../../local-models/api/localModelsService';
// import { ModelInputWithSuggestions } from './ModelInputWithSuggestions';
import './AgentBuilderForm.css';

// ============================================================================
// TYPES
// ============================================================================

interface FormData {
    // Basic Info
    name: string;
    description: string;

    // Model
    model_type: 'saas' | 'local';
    model_id: number | null;
    local_model_id: number | null;
    api_key_id: number | null;

    // Parameters
    temperature: number;
    max_tokens: number;
    top_p: number;
    frequency_penalty: number;
    presence_penalty: number;

    // Prompts
    system_prompt: string;
    goal_prompt: string;
    service_prompt: string;

    // Tools
    tools: SelectedTool[];

    // Connections
    connections: SelectedConnection[];

    // MCP Servers
    mcp_servers: MCPServer[];

    // Memory & RAG
    memory_enabled: boolean;
    memory_config: Record<string, unknown>;
    rag_enabled: boolean;
    rag_config: Record<string, unknown>;

    // Autonomy & Actions
    action_mode_enabled: boolean;
    autonomy_level: AgentAutonomyLevel;
    max_steps: number;
    mcp_enabled: boolean;

    // Settings
    is_public: boolean;
    color: string;
    icon: string;
}

interface SelectedTool {
    type: string;
    name: string;
    display_name: string;
    description: string;
    config: Record<string, unknown>;
    is_enabled: boolean;
}

interface SelectedConnection {
    type: string;
    name: string;
    display_name: string;
    config: Record<string, unknown>;
    description: string;
}

interface MCPServer {
    server_name: string;
    server_url: string;
    description: string;
    transport_type: string;
    requires_auth: boolean;
    auth_type: string;
}

interface FormErrors {
    [key: string]: string;
}

interface ConnectionSchema {
    fields: {
        [key: string]: {
            label: string;
            type: 'text' | 'password' | 'url';
            placeholder?: string;
            description?: string;
            required?: boolean;
            validation?: (value: string) => string | null;
        }
    };
    testService: string;
}

const CONNECTION_SCHEMAS: Record<string, ConnectionSchema> = {
    github: {
        fields: {
            access_token: { label: 'Personal Access Token', type: 'password', required: true, description: 'GitHub PAT with repo scopes.' }
        },
        testService: 'github'
    },
    slack: {
        fields: {
            bot_token: { label: 'Bot Token (xoxb-)', type: 'password', required: true, validation: v => v.startsWith('xoxb-') ? null : 'Must start with xoxb-' },
            channel_id: { label: 'Default Channel ID', type: 'text', placeholder: 'C12345678' }
        },
        testService: 'slack'
    },
    telegram: {
        fields: {
            bot_token: { label: 'Bot Token', type: 'password', required: true, description: 'Token from @BotFather' },
            chat_id: { label: 'Chat ID', type: 'text', description: 'Optional default chat ID' }
        },
        testService: 'telegram'
    },
    gmail: {
        fields: {
            credentials_json: { label: 'Service Account JSON', type: 'password', description: 'Paste the full JSON content' },
            email: { label: 'Impersonated User Email', type: 'text', description: 'Email to impersonate (if using service account)' }
        },
        testService: 'gmail'
    },
    google_drive: {
        fields: {
            credentials_json: { label: 'Service Account JSON', type: 'password', description: 'Paste the full JSON content' },
            folder_id: { label: 'Root Folder ID', type: 'text', description: 'Optional root folder' }
        },
        testService: 'google_drive'
    },
    notion: {
        fields: {
            api_key: { label: 'Integration Token', type: 'password', required: true }
        },
        testService: 'notion' // Backend might not have this yet, generic fallback
    },
    jira: {
        fields: {
            url: { label: 'Jira URL', type: 'url', required: true },
            email: { label: 'Email', type: 'text', required: true },
            api_token: { label: 'API Token', type: 'password', required: true }
        },
        testService: 'jira'
    },
    discord: {
        fields: {
            bot_token: { label: 'Bot Token', type: 'password', required: true }
        },
        testService: 'discord'
    }
};

type FormSection = 'basic' | 'model' | 'prompts' | 'knowledge' | 'actions' | 'tools' | 'connections' | 'mcp' | 'review';

// ============================================================================
// COMPONENT
// ============================================================================

export const AgentBuilderForm: React.FC = () => {
    const navigate = useNavigate();
    const { agentId } = useParams<{ agentId: string }>();
    const isEditing = !!agentId;

    // State
    const [currentSection, setCurrentSection] = useState<FormSection>('basic');
    const [modelTab, setModelTab] = useState<'saas' | 'local'>('saas');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [errors, setErrors] = useState<FormErrors>({});

    // Search State
    // const [modelQuery, setModelQuery] = useState('');

    // Data
    const [models, setModels] = useState<AgentModel[]>([]);
    const [localModels, setLocalModels] = useState<LocalModel[]>([]);
    const [apiKeys, setApiKeys] = useState<AgentApiKey[]>([]);
    const [availableTools, setAvailableTools] = useState<AvailableTool[]>([]);
    const [ragDocuments, setRagDocuments] = useState<RagDocument[]>([]);
    const [promptTemplates, setPromptTemplates] = useState<PromptTemplate[]>([]);


    // Modals
    const [showApiKeyModal, setShowApiKeyModal] = useState(false);
    const [showToolConfigModal, setShowToolConfigModal] = useState<SelectedTool | null>(null);
    const [showConnectionModal, setShowConnectionModal] = useState<{ type: string; name: string } | null>(null);

    // Form Data
    const [formData, setFormData] = useState<FormData>({
        name: '',
        description: '',
        model_type: 'saas',
        model_id: null,
        local_model_id: null,
        api_key_id: null,
        temperature: 0.7,
        max_tokens: 4096,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
        system_prompt: '',
        goal_prompt: '',
        service_prompt: '',
        tools: [],
        connections: [],
        mcp_servers: [],
        memory_enabled: false,
        memory_config: {},
        rag_enabled: false,
        rag_config: {},
        action_mode_enabled: false,
        autonomy_level: AgentAutonomyLevel.LOW,
        max_steps: 10,
        mcp_enabled: false,
        is_public: false,
        color: '#6366f1',
        icon: 'robot',
    });

    // Sections configuration
    const sections: { id: FormSection; label: string; icon: string }[] = [
        { id: 'basic', label: 'Basic Info', icon: '📝' },
        { id: 'model', label: 'Model Selection', icon: '🤖' },
        { id: 'prompts', label: 'Prompts', icon: '💬' },
        { id: 'knowledge', label: 'Knowledge & Memory', icon: '🧠' },
        { id: 'actions', label: 'Actions & Autonomy', icon: '⚡' },
        { id: 'tools', label: 'Tools', icon: '🔧' },
        { id: 'connections', label: 'Connections', icon: '🔗' },
        { id: 'mcp', label: 'MCP Servers', icon: '🔌' },
        { id: 'review', label: 'Review & Create', icon: '✅' },
    ];

    // ========================================================================
    // DATA LOADING
    // ========================================================================

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        if (isEditing && agentId) {
            loadExistingAgent(parseInt(agentId));
        }
    }, [agentId, isEditing]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [modelsRes, toolsRes, localRes, templatesRes] = await Promise.all([
                agentBuilderApi.getModels(),
                agentBuilderApi.getAvailableTools(),
                localModelsService.getModelsForAgent(),
                agentBuilderApi.getPromptTemplates(),
            ]);
            setModels(modelsRes);
            setAvailableTools(toolsRes);
            setLocalModels(localRes);
            setPromptTemplates(templatesRes);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadExistingAgent = async (id: number) => {
        try {
            const agent = await agentBuilderApi.getAgent(id);

            setModelTab(agent.local_model_id ? 'local' : 'saas');

            // Populate form with existing data
            setFormData({
                name: agent.name,
                description: agent.description || '',
                model_type: agent.local_model_id ? 'local' : 'saas',
                model_id: agent.model_id,
                local_model_id: agent.local_model_id,
                api_key_id: agent.api_key_id,
                temperature: agent.temperature,
                max_tokens: agent.max_tokens,
                top_p: agent.top_p,
                frequency_penalty: agent.frequency_penalty,
                presence_penalty: agent.presence_penalty,
                system_prompt: agent.system_prompt,
                goal_prompt: agent.goal_prompt || '',
                service_prompt: agent.service_prompt || '',
                tools: agent.tools.map(t => ({
                    type: t.tool_type,
                    name: t.tool_name,
                    display_name: t.display_name,
                    description: t.description || '',
                    config: t.config_json || {},
                    is_enabled: t.is_enabled,
                })),
                connections: agent.connections.map(c => ({
                    type: c.connection_type,
                    name: c.name,
                    display_name: c.display_name,
                    description: c.description || '',
                    config: c.config_json || {},
                })),
                mcp_servers: agent.mcp_servers.map(m => ({
                    server_name: m.server_name,
                    server_url: m.server_url,
                    description: m.description || '',
                    transport_type: m.transport_type,
                    requires_auth: m.requires_auth,
                    auth_type: '',
                })),
                memory_enabled: agent.memory_enabled,
                memory_config: agent.memory_config || {},
                rag_enabled: agent.rag_enabled,
                rag_config: agent.rag_config || {},
                action_mode_enabled: agent.action_mode_enabled,
                autonomy_level: agent.autonomy_level,
                max_steps: agent.max_steps,
                mcp_enabled: agent.mcp_enabled,
                is_public: agent.is_public,
                color: agent.color || '#6366f1',
                icon: agent.icon || 'robot',
            });

            if (agent.rag_documents) {
                setRagDocuments(agent.rag_documents);
            }

            // API keys will be loaded by the useEffect when selectedProvider is set
        } catch (error) {
            console.error('Failed to load agent:', error);
        }
    };

    // ========================================================================
    // MODEL SELECTION
    // ========================================================================

    const [selectedProvider, setSelectedProvider] = useState<number | null>(null);

    // Load API keys when provider changes
    useEffect(() => {
        if (selectedProvider) {
            agentBuilderApi.getApiKeys(selectedProvider)
                .then(setApiKeys)
                .catch(err => console.error('Failed to load keys:', err));
        } else {
            setApiKeys([]);
        }
    }, [selectedProvider]);

    // Initialize provider and query when editing
    useEffect(() => {
        if (formData.model_type === 'saas' && formData.model_id && models.length > 0) {
            const model = models.find(m => m.id === formData.model_id);
            if (model && model.provider_id) {
                setSelectedProvider(model.provider_id);
            }
        }
    }, [formData.model_id, models, formData.model_type]);

    // Reset query when switching tabs
    useEffect(() => {
        // setModelQuery('');
    }, [modelTab]);

    const getUniqueProviders = () => {
        if (!models || models.length === 0) return [];

        const providersMap = new Map<number, string>();

        models.forEach(m => {
            if (m.provider_id) {
                // Try to get display name from provider object if available, otherwise use a fallback or skip
                let displayName = '';
                if (typeof m.provider === 'object' && m.provider && 'display_name' in m.provider) {
                    displayName = m.provider.display_name;
                } else if (typeof m.provider === 'string') {
                    displayName = m.provider;
                }

                if (displayName) {
                    providersMap.set(m.provider_id, displayName);
                }
            }
        });

        return Array.from(providersMap.entries())
            .map(([id, name]) => ({ id, name }))
            .sort((a, b) => a.name.localeCompare(b.name));
    };

    const getModelsForProvider = (providerId: number) => {
        return models.filter(m => m.provider_id === providerId);
    };

    const handleProviderSelect = (providerId: number) => {
        setSelectedProvider(providerId);

        // Clear current model selection if switching providers
        if (formData.model_type === 'saas' && formData.model_id) {
            const currentModel = models.find(m => m.id === formData.model_id);
            if (currentModel) {
                if (currentModel.provider_id !== providerId) {
                    setFormData(prev => ({ ...prev, model_id: null, api_key_id: null }));
                }
            }
        }
    };

    const handleModelSelect = async (modelId: number, type: 'saas' | 'local' = 'saas') => {
        if (type === 'saas') {
            const model = models.find(m => m.id === modelId);
            if (!model) return;

            setFormData(prev => ({
                ...prev,
                model_type: 'saas',
                model_id: modelId,
                local_model_id: null,
                api_key_id: null
            }));
            setErrors(prev => ({ ...prev, model_id: '', api_key_id: '' }));

            // Load API keys for this provider
            try {
                if (model.provider_id) {
                    const keysRes = await agentBuilderApi.getApiKeys(model.provider_id);
                    setApiKeys(keysRes);

                    // If model requires API key and none exists, show modal
                    if (model.requires_api_key && keysRes.length === 0) {
                        setShowApiKeyModal(true);
                    }
                }
            } catch (error) {
                console.error('Failed to load API keys:', error);
            }
        } else {
            const model = localModels.find(m => m.id === modelId);
            if (!model) return;

            setFormData(prev => ({
                ...prev,
                model_type: 'local',
                model_id: null,
                local_model_id: modelId,
                api_key_id: null
            }));
            setErrors(prev => ({ ...prev, model_id: '', api_key_id: '' }));
            setApiKeys([]);
        }
    };

    const renderModelSelection = () => {
        const selectedModel = formData.model_type === 'saas'
            ? models.find(m => m.id === formData.model_id)
            : localModels.find(m => m.id === formData.local_model_id);

        return (
            <div className="agent-builder-section">
                <h2 className="section-title">
                    <span className="section-icon">🤖</span>
                    Model Selection
                </h2>
                <p className="section-description">
                    Choose the AI model that will power your agent.
                </p>

                <div className="model-tabs" style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
                    <button type="button" className={`tab-btn ${modelTab === 'saas' ? 'active' : ''}`} onClick={() => setModelTab('saas')}>Cloud Models</button>
                    <button type="button" className={`tab-btn ${modelTab === 'local' ? 'active' : ''}`} onClick={() => setModelTab('local')}>Local Models</button>
                </div>

                {errors.model_id && <div className="error-banner">{errors.model_id}</div>}

                {modelTab === 'saas' ? (
                    <div className="cloud-models-flow">
                        {models.length === 0 && !loading ? (
                            <div className="empty-state" style={{ padding: '30px', textAlign: 'center', border: '2px dashed hsl(var(--color-border))', borderRadius: '12px', background: 'hsl(var(--color-bg))' }}>
                                <div style={{ fontSize: '2rem', marginBottom: '10px' }}>☁️</div>
                                <h3 style={{ marginBottom: '10px', color: 'hsl(var(--color-text))' }}>No Cloud Models Available</h3>
                                <p style={{ color: 'hsl(var(--color-text-muted))' }}>
                                    There are no cloud models configured in the system.
                                    Please contact an administrator to seed the model database.
                                </p>
                            </div>
                        ) : (
                            <>
                                {/* Step 1: Provider Selection */}
                                <div className="form-group">
                                    <label>1. Select Provider</label>
                                    <select
                                        className="form-select"
                                        value={selectedProvider || ''}
                                        onChange={(e) => handleProviderSelect(Number(e.target.value))}
                                        style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                                    >
                                        <option value="">-- Choose a Provider --</option>
                                        {getUniqueProviders().map(p => (
                                            <option key={p.id} value={p.id}>{p.name}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Step 2: Model Selection */}
                                {selectedProvider && (
                                    <div className="form-group animation-slide-in" style={{ marginTop: '20px' }}>
                                        <label>2. Select Model</label>
                                        <select
                                            className="form-select"
                                            value={formData.model_id || ''}
                                            onChange={(e) => handleModelSelect(Number(e.target.value), 'saas')}
                                            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0', marginTop: '5px' }}
                                        >
                                            <option value="">-- Choose a Model --</option>
                                            {getModelsForProvider(selectedProvider).map(m => (
                                                <option key={m.id} value={m.id}>
                                                    {m.display_name} ({(m.context_window / 1000).toFixed(0)}k context)
                                                </option>
                                            ))}
                                        </select>

                                        {selectedModel && (
                                            <div className="selected-model-info" style={{ marginTop: '10px', fontSize: '0.9rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                <span>Running <strong>{(selectedModel as AgentModel).display_name}</strong></span>
                                                <span>•</span>
                                                <span>{((selectedModel as AgentModel).context_window / 1000).toFixed(0)}k Context</span>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {!selectedProvider && (
                                    <div className="info-message" style={{ padding: '15px', backgroundColor: '#f8fafc', borderRadius: '8px', color: '#64748b', marginTop: '20px', textAlign: 'center' }}>
                                        Select a provider above to see available models.
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                ) : (
                    <div className="local-models-flow">
                        {/* Local Models Logic */}
                        <div className="form-group">
                            <label>Select Local Model</label>
                            {localModels.length === 0 ? (
                                <div className="empty-state" style={{ padding: '30px', textAlign: 'center', border: '1px dashed #cbd5e1', borderRadius: '8px', marginTop: '10px' }}>
                                    <p style={{ marginBottom: '15px', color: '#64748b' }}>No local models available.</p>
                                    <button
                                        type="button"
                                        className="btn-secondary"
                                        onClick={() => navigate('/ai/local-models')}
                                        style={{ padding: '8px 16px', borderRadius: '6px', background: '#f1f5f9', border: 'none', cursor: 'pointer' }}
                                    >
                                        Manage Local Models
                                    </button>
                                </div>
                            ) : (
                                <select
                                    className="form-select"
                                    value={formData.local_model_id || ''}
                                    onChange={(e) => handleModelSelect(Number(e.target.value), 'local')}
                                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0', marginTop: '5px' }}
                                >
                                    <option value="">-- Choose a Local Model --</option>
                                    {localModels.filter(m => m.status === 'ready').map(m => (
                                        <option key={m.id} value={m.id}>
                                            {m.name} ({m.size_gb?.toFixed(2) || '?'} GB)
                                        </option>
                                    ))}
                                </select>
                            )}
                        </div>
                    </div>
                )}

                {/* API Key Section */}
                {modelTab === 'saas' && selectedModel && ((selectedModel as AgentModel).requires_api_key !== false) && (
                    <div className="api-key-section" style={{ marginTop: '25px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
                        <h3 style={{ fontSize: '1.1rem', marginBottom: '15px' }}>API Key</h3>
                        {apiKeys.length > 0 ? (
                            <div className="api-key-selector" style={{ display: 'flex', gap: '10px' }}>
                                <div style={{ flex: 1 }}>
                                    <select
                                        value={formData.api_key_id || ''}
                                        onChange={e => setFormData(prev => ({ ...prev, api_key_id: parseInt(e.target.value) || null }))}
                                        className={errors.api_key_id ? 'form-select error' : 'form-select'}
                                        style={{ width: '100%', padding: '10px', borderRadius: '8px', border: errors.api_key_id ? '1px solid #ef4444' : '1px solid #e2e8f0' }}
                                    >
                                        <option value="">Select an API key...</option>
                                        {apiKeys.map(key => (
                                            <option key={key.id} value={key.id}>
                                                {key.label} ({key.key_preview}) {!key.is_valid && '⚠️'}
                                            </option>
                                        ))}
                                    </select>
                                    {errors.api_key_id && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.85rem', marginTop: '5px', display: 'block' }}>{errors.api_key_id}</span>}
                                </div>
                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={() => setShowApiKeyModal(true)}
                                    style={{ padding: '0 15px', borderRadius: '8px', background: '#f1f5f9', border: 'none', cursor: 'pointer', whiteSpace: 'nowrap' }}
                                >
                                    + New Key
                                </button>
                            </div>
                        ) : (
                            <div className="no-api-key" style={{ padding: '15px', background: '#fff1f2', borderRadius: '8px', border: '1px solid #ffe4e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <p style={{ margin: 0, color: '#e11d48' }}>
                                    No API key found.
                                </p>
                                <button
                                    type="button"
                                    className="btn-primary"
                                    onClick={() => setShowApiKeyModal(true)}
                                    style={{ padding: '8px 16px', borderRadius: '6px', background: '#e11d48', color: 'white', border: 'none', cursor: 'pointer' }}
                                >
                                    Add API Key
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {selectedModel && (
                    <div className="model-params" style={{ marginTop: '25px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
                        <h3 style={{ fontSize: '1.1rem', marginBottom: '15px' }}>Model Parameters</h3>
                        <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                            <div className="param-group">
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                    <label>Temperature</label>
                                    <span style={{ fontWeight: 'bold' }}>{formData.temperature}</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    value={formData.temperature}
                                    onChange={e => setFormData(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                                    style={{ width: '100%' }}
                                />
                                <span className="param-hint" style={{ fontSize: '0.8rem', color: '#64748b' }}>Lower = more focused, Higher = more creative</span>
                            </div>
                            <div className="param-group">
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                    <label>Max Tokens</label>
                                    <span style={{ fontWeight: 'bold' }}>{formData.max_tokens}</span>
                                </div>
                                <input
                                    type="range"
                                    min="100"
                                    max={formData.model_type === 'saas' ? (selectedModel as AgentModel).max_output_tokens : 4096}
                                    step="100"
                                    value={formData.max_tokens}
                                    onChange={e => setFormData(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    // ========================================================================
    // TOOLS MANAGEMENT
    // ========================================================================

    const handleAddTool = (tool: AvailableTool) => {
        // Check if already added
        if (formData.tools.some(t => t.type === tool.type)) {
            return;
        }

        const newTool: SelectedTool = {
            type: tool.type,
            name: tool.name,
            display_name: tool.display_name,
            description: tool.description,
            config: {},
            is_enabled: true,
        };

        setFormData(prev => ({
            ...prev,
            tools: [...prev.tools, newTool],
        }));

        // If tool requires config, open config modal
        if (tool.requires_auth || tool.config_schema) {
            setShowToolConfigModal(newTool);
        }
    };

    const handleRemoveTool = (toolType: string) => {
        setFormData(prev => ({
            ...prev,
            tools: prev.tools.filter(t => t.type !== toolType),
        }));
    };

    const handleConnectionSave = (type: string, config: Record<string, unknown>) => {
        setFormData(prev => {
            const existingIndex = prev.connections.findIndex(c => c.type === type);
            if (existingIndex >= 0) {
                // Update
                const newConns = [...prev.connections];
                newConns[existingIndex] = { ...newConns[existingIndex], config };
                return { ...prev, connections: newConns };
            } else {
                // Add new (shouldn't happen with current UI flow but safe to have)
                return prev;
            }
        });
        setShowConnectionModal(null);
    };

    const toggleConnection = (type: string, name: string, description: string) => {
        setFormData(prev => {
            const exists = prev.connections.some(c => c.type === type);
            if (exists) {
                return {
                    ...prev,
                    connections: prev.connections.filter(c => c.type !== type)
                };
            } else {
                return {
                    ...prev,
                    connections: [...prev.connections, {
                        type,
                        name,
                        display_name: name,
                        description,
                        config: {}
                    }]
                };
            }
        });
    };

    const handleToolConfigSave = (tool: SelectedTool, config: Record<string, unknown>) => {
        setFormData(prev => ({
            ...prev,
            tools: prev.tools.map(t =>
                t.type === tool.type ? { ...t, config } : t
            ),
        }));
        setShowToolConfigModal(null);
    };

    // ========================================================================
    // MCP SERVERS
    // ========================================================================

    const handleAddMCPServer = () => {
        setFormData(prev => ({
            ...prev,
            mcp_servers: [
                ...prev.mcp_servers,
                {
                    server_name: '',
                    server_url: '',
                    description: '',
                    transport_type: 'stdio',
                    requires_auth: false,
                    auth_type: '',
                },
            ],
        }));
    };

    const handleRemoveMCPServer = (index: number) => {
        setFormData(prev => ({
            ...prev,
            mcp_servers: prev.mcp_servers.filter((_, i) => i !== index),
        }));
    };

    const handleMCPServerChange = (index: number, field: string, value: string | boolean) => {
        setFormData(prev => ({
            ...prev,
            mcp_servers: prev.mcp_servers.map((server, i) =>
                i === index ? { ...server, [field]: value } : server
            ),
        }));
    };

    // ========================================================================
    // RAG DOCUMENTS
    // ========================================================================

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !agentId) return;

        setSaving(true);
        try {
            const uploadedDoc = await agentBuilderApi.uploadRagFile(parseInt(agentId), file);
            setRagDocuments(prev => [...prev, uploadedDoc]);
            // Clear input
            event.target.value = '';
        } catch (error) {
            console.error('Failed to upload file:', error);
            setErrors(prev => ({ ...prev, rag: 'Failed to upload file' }));
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteDocument = async (docId: number) => {
        if (!confirm('Are you sure you want to delete this document?')) return;

        try {
            await agentBuilderApi.deleteRagDocument(docId);
            setRagDocuments(prev => prev.filter(d => d.id !== docId));
        } catch (error) {
            console.error('Failed to delete document:', error);
        }
    };

    // ========================================================================
    // KNOWLEDGE & MEMORY
    // ========================================================================

    const renderKnowledge = () => (
        <div className="agent-builder-section">
            <h2 className="section-title">
                <span className="section-icon">🧠</span>
                Knowledge & Memory
            </h2>
            <p className="section-description">
                Give your agent long-term memory and access to your knowledge base.
            </p>

            <div className="form-group" style={{ marginBottom: '25px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <label style={{ margin: 0 }}>Enable Memory</label>
                    <div className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={formData.memory_enabled}
                            onChange={(e) => setFormData(prev => ({ ...prev, memory_enabled: e.target.checked }))}
                            id="memory-toggle"
                        />
                        <label htmlFor="memory-toggle"></label>
                    </div>
                </div>
                <p className="field-hint">
                    Allows the agent to remember past conversations and user preferences across sessions.
                </p>
            </div>

            <hr style={{ margin: '20px 0', border: 'none', borderTop: '1px solid #eee' }} />

            <div className="form-group">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <label style={{ margin: 0 }}>Enable RAG (Retrieval Augmented Generation)</label>
                    <div className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={formData.rag_enabled}
                            onChange={(e) => setFormData(prev => ({ ...prev, rag_enabled: e.target.checked }))}
                            id="rag-toggle"
                        />
                        <label htmlFor="rag-toggle"></label>
                    </div>
                </div>
                <p className="field-hint">
                    Allows the agent to search and retrieve information from your knowledge base.
                </p>

                {formData.rag_enabled && (
                    <div className="rag-documents-section animation-slide-in" style={{ marginTop: '20px' }}>
                        <label>Knowledge Documents</label>

                        {!isEditing ? (
                            <div className="info-message warning">
                                Please create the agent first to upload documents.
                            </div>
                        ) : (
                            <>
                                <div className="documents-list" style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    {ragDocuments.map(doc => (
                                        <div key={doc.id} className="document-item" style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            padding: '10px', border: '1px solid #e2e8f0', borderRadius: '6px',
                                            backgroundColor: 'white'
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                <span style={{ fontSize: '1.2rem' }}>📄</span>
                                                <div>
                                                    <div style={{ fontWeight: '500' }}>{doc.filename}</div>
                                                    <div style={{ fontSize: '0.8rem', color: '#666' }}>
                                                        {doc.file_type} • {new Date(doc.created_at).toLocaleDateString()}
                                                    </div>
                                                </div>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => handleDeleteDocument(doc.id)}
                                                className="btn-icon danger"
                                                style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer' }}
                                            >
                                                🗑️
                                            </button>
                                        </div>
                                    ))}

                                    {ragDocuments.length === 0 && (
                                        <div className="empty-state-small">No documents uploaded yet.</div>
                                    )}
                                </div>

                                <div className="upload-actions" style={{ marginTop: '15px' }}>
                                    <input
                                        type="file"
                                        id="rag-file-upload"
                                        style={{ display: 'none' }}
                                        onChange={handleFileUpload}
                                        accept=".pdf,.txt,.md,.docx,.csv"
                                    />
                                    <label
                                        htmlFor="rag-file-upload"
                                        className="btn-secondary"
                                        style={{ display: 'inline-block', cursor: 'pointer' }}
                                    >
                                        + Upload Document
                                    </label>
                                    <p className="field-hint" style={{ marginTop: '5px' }}>
                                        Supported: PDF, TXT, MD, DOCX (Max 10MB)
                                    </p>
                                </div>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );

    // ========================================================================
    // VALIDATION
    // ========================================================================

    const validateSection = (section: FormSection): boolean => {
        const newErrors: FormErrors = {};

        switch (section) {
            case 'basic':
                if (!formData.name.trim()) {
                    newErrors.name = 'Agent name is required';
                } else if (formData.name.length < 2) {
                    newErrors.name = 'Name must be at least 2 characters';
                }
                break;
            case 'model':
                if (formData.model_type === 'saas') {
                    if (!formData.model_id) {
                        newErrors.model_id = 'Please select a cloud model';
                    }
                    if (formData.model_id) {
                        const selectedModel = models.find(m => m.id === formData.model_id);
                        if (selectedModel?.requires_api_key && !formData.api_key_id) {
                            newErrors.api_key_id = 'API key is required for this model';
                        }
                    }
                } else {
                    if (!formData.local_model_id) {
                        newErrors.model_id = 'Please select a local model';
                    }
                }
                break;
            case 'prompts':
                if (!formData.system_prompt.trim()) {
                    newErrors.system_prompt = 'System prompt is required';
                } else if (formData.system_prompt.length < 10) {
                    newErrors.system_prompt = 'System prompt must be at least 10 characters';
                }
                break;
            case 'tools':
                // Tools with requires_auth should have config
                formData.tools.forEach(tool => {
                    const toolInfo = availableTools.find(t => t.type === tool.type);
                    if (toolInfo?.requires_auth && Object.keys(tool.config).length === 0) {
                        newErrors[`tool_${tool.type}`] = `${tool.display_name} requires configuration`;
                    }
                });
                break;
            case 'mcp':
                formData.mcp_servers.forEach((server, i) => {
                    if (server.server_name && !server.server_url) {
                        newErrors[`mcp_${i}_url`] = 'Server URL is required';
                    }
                    if (server.server_url && !server.server_name) {
                        newErrors[`mcp_${i}_name`] = 'Server name is required';
                    }
                });
                break;
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    // ========================================================================
    // FORM SUBMISSION
    // ========================================================================

    const handleSubmit = async () => {
        // Validate all sections
        const allValid = sections
            .filter(s => s.id !== 'review')
            .every(s => validateSection(s.id));

        if (!allValid) {
            // Find first section with errors
            for (const section of sections) {
                if (!validateSection(section.id)) {
                    setCurrentSection(section.id);
                    return;
                }
            }
            return;
        }

        setSaving(true);
        try {
            const agentData: CreateAgentDTO = {
                name: formData.name,
                description: formData.description || undefined,
                model_id: formData.model_type === 'saas' ? formData.model_id! : undefined,
                local_model_id: formData.model_type === 'local' ? formData.local_model_id! : undefined,
                api_key_id: formData.model_type === 'saas' ? (formData.api_key_id || undefined) : undefined,
                temperature: formData.temperature,
                max_tokens: formData.max_tokens,
                top_p: formData.top_p,
                frequency_penalty: formData.frequency_penalty,
                presence_penalty: formData.presence_penalty,
                system_prompt: formData.system_prompt,
                goal_prompt: formData.goal_prompt || undefined,
                service_prompt: formData.service_prompt || undefined,
                is_public: formData.is_public,
                color: formData.color,
                icon: formData.icon,
                tools: formData.tools.map(t => ({
                    tool_type: t.type,
                    tool_name: t.name,
                    display_name: t.display_name,
                    description: t.description,
                    config_json: t.config,
                    is_enabled: t.is_enabled,
                })),

                connections: formData.connections.map(c => ({
                    connection_type: c.type,
                    name: c.name,
                    display_name: c.display_name || c.name,
                    description: c.description || '',
                    config_json: c.config
                })),

                // Memory & RAG
                memory_enabled: formData.memory_enabled,
                memory_config: formData.memory_config,
                rag_enabled: formData.rag_enabled,
                rag_config: formData.rag_config,

                mcp_servers: formData.mcp_servers
                    .filter(m => m.server_name && m.server_url)
                    .map(m => ({
                        server_name: m.server_name,
                        server_url: m.server_url,
                        description: m.description,
                        transport_type: m.transport_type,
                        requires_auth: m.requires_auth,
                        auth_type: m.auth_type || undefined,
                    })),

                // Autonomy
                action_mode_enabled: formData.action_mode_enabled,
                autonomy_level: formData.autonomy_level,
                max_steps: formData.max_steps,
                mcp_enabled: formData.mcp_enabled,
            };

            if (isEditing && agentId) {
                await agentBuilderApi.updateAgent(parseInt(agentId), agentData as UpdateAgentDTO);
            } else {
                await agentBuilderApi.createAgent(agentData);
            }

            navigate('/ai/agents');
        } catch (error: any) {
            console.error('Failed to save agent:', error);
            let message = error.message || 'Failed to save agent';
            if (error.response?.data?.detail) {
                message = typeof error.response.data.detail === 'string'
                    ? error.response.data.detail
                    : JSON.stringify(error.response.data.detail);
            }
            setErrors({ submit: message });
        } finally {
            setSaving(false);
        }
    };

    // ========================================================================
    // NAVIGATION
    // ========================================================================

    const goToNextSection = () => {
        const currentIndex = sections.findIndex(s => s.id === currentSection);
        if (currentIndex < sections.length - 1) {
            if (validateSection(currentSection)) {
                setCurrentSection(sections[currentIndex + 1].id);
            }
        }
    };

    const goToPrevSection = () => {
        const currentIndex = sections.findIndex(s => s.id === currentSection);
        if (currentIndex > 0) {
            setCurrentSection(sections[currentIndex - 1].id);
        }
    };

    // ========================================================================
    // RENDER SECTIONS
    // ========================================================================

    const renderBasicInfo = () => (
        <div className="agent-builder-section">
            <h2 className="section-title">
                <span className="section-icon">📝</span>
                Basic Information
            </h2>
            <p className="section-description">
                Give your agent a name and description that reflects its purpose.
            </p>

            <div className="form-group">
                <label htmlFor="agent-name">Agent Name *</label>
                <input
                    id="agent-name"
                    type="text"
                    value={formData.name}
                    onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., Code Review Assistant"
                    className={errors.name ? 'error' : ''}
                />
                {errors.name && <span className="error-message">{errors.name}</span>}
            </div>

            <div className="form-group">
                <label htmlFor="agent-description">Description</label>
                <textarea
                    id="agent-description"
                    value={formData.description}
                    onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe what this agent does..."
                    rows={3}
                />
            </div>

            <div className="form-row">
                <div className="form-group">
                    <label htmlFor="agent-color">Theme Color</label>
                    <div className="color-picker">
                        <input
                            id="agent-color"
                            type="color"
                            value={formData.color}
                            onChange={e => setFormData(prev => ({ ...prev, color: e.target.value }))}
                        />
                        <span className="color-value">{formData.color}</span>
                    </div>
                </div>

                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={formData.is_public}
                            onChange={e => setFormData(prev => ({ ...prev, is_public: e.target.checked }))}
                        />
                        Make agent public (visible to all users)
                    </label>
                </div>
            </div>
        </div>
    );



    const renderPrompts = () => (
        <div className="agent-builder-section">
            <h2 className="section-title">
                <span className="section-icon">💬</span>
                Prompts
            </h2>
            <p className="section-description">
                Configure the prompts that define your agent's behavior and personality.
            </p>

            <div className="form-group">
                <label>Prompt Template</label>
                <select
                    onChange={(e) => {
                        const template = promptTemplates.find(t => t.id === e.target.value);
                        if (template) {
                            setFormData(prev => ({
                                ...prev,
                                system_prompt: template.system_prompt
                            }));
                        }
                    }}
                    defaultValue=""
                >
                    <option value="" disabled>Select a template...</option>
                    {promptTemplates.map(t => (
                        <option key={t.id} value={t.id}>{t.name} - {t.description}</option>
                    ))}
                </select>
                <p className="field-hint">
                    Choose a template to pre-fill the system prompt.
                </p>
            </div>

            <div className="form-group">
                <label htmlFor="system-prompt">System Prompt *</label>
                <p className="field-hint">
                    The core instruction that defines how your agent behaves. This is always sent with every request.
                </p>
                <textarea
                    id="system-prompt"
                    value={formData.system_prompt}
                    onChange={e => setFormData(prev => ({ ...prev, system_prompt: e.target.value }))}
                    placeholder="You are a helpful assistant that..."
                    rows={8}
                    className={errors.system_prompt ? 'error' : ''}
                />
                {errors.system_prompt && <span className="error-message">{errors.system_prompt}</span>}
                <div className="char-count">{formData.system_prompt.length} characters</div>
            </div>

            <div className="form-group">
                <label htmlFor="goal-prompt">Goal Prompt</label>
                <p className="field-hint">
                    Specific goals or objectives for the agent to achieve.
                </p>
                <textarea
                    id="goal-prompt"
                    value={formData.goal_prompt}
                    onChange={e => setFormData(prev => ({ ...prev, goal_prompt: e.target.value }))}
                    placeholder="Your goal is to help users..."
                    rows={4}
                />
            </div>

            <div className="form-group">
                <label htmlFor="service-prompt">Service Prompt</label>
                <p className="field-hint">
                    Additional context about the service or product the agent supports.
                </p>
                <textarea
                    id="service-prompt"
                    value={formData.service_prompt}
                    onChange={e => setFormData(prev => ({ ...prev, service_prompt: e.target.value }))}
                    placeholder="This agent is part of..."
                    rows={4}
                />
            </div>
        </div>
    );

    const renderTools = () => (
        <div className="agent-builder-section">
            <h2 className="section-title">
                <span className="section-icon">🔧</span>
                Tools
            </h2>
            <p className="section-description">
                Select the tools your agent can use to perform actions.
            </p>

            <div className="tools-selected">
                <h3>Selected Tools ({formData.tools.length})</h3>
                {formData.tools.length === 0 ? (
                    <p className="no-items">No tools selected yet. Choose from available tools below.</p>
                ) : (
                    <div className="tools-list">
                        {formData.tools.map(tool => (
                            <div key={tool.type} className="tool-chip">
                                <span className="tool-name">{tool.display_name}</span>
                                <button
                                    type="button"
                                    className="btn-icon"
                                    onClick={() => setShowToolConfigModal(tool)}
                                    title="Configure"
                                >
                                    ⚙️
                                </button>
                                <button
                                    type="button"
                                    className="btn-icon remove"
                                    onClick={() => handleRemoveTool(tool.type)}
                                    title="Remove"
                                >
                                    ×
                                </button>
                                {errors[`tool_${tool.type}`] && (
                                    <span className="tool-error">⚠️ Needs config</span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="tools-available">
                <h3>Available Tools</h3>
                <div className="tools-grid">
                    {availableTools.map(tool => {
                        const isAdded = formData.tools.some(t => t.type === tool.type);
                        return (
                            <div
                                key={tool.type}
                                className={`tool-card ${isAdded ? 'added' : ''}`}
                                onClick={() => !isAdded && handleAddTool(tool)}
                            >
                                <span className="tool-icon">{getToolIcon(tool.type)}</span>
                                <h4>{tool.display_name}</h4>
                                <p>{tool.description}</p>
                                {tool.requires_auth && (
                                    <span className="requires-auth">🔐 Requires auth</span>
                                )}
                                {isAdded && <span className="added-badge">✓ Added</span>}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );

    const renderActions = () => (
        <div className="agent-builder-section">
            <h2 className="section-title">
                <span className="section-icon">⚡</span>
                Actions & Autonomy
            </h2>
            <p className="section-description">
                Configure how your agent executes tasks and interacts with tools.
            </p>

            <div className="form-group">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <label style={{ margin: 0 }}>Action Mode Enabled</label>
                    <div className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={formData.action_mode_enabled}
                            onChange={(e) => setFormData(prev => ({ ...prev, action_mode_enabled: e.target.checked }))}
                            id="action-mode-toggle"
                        />
                        <label htmlFor="action-mode-toggle"></label>
                    </div>
                </div>
                <p className="field-hint">
                    Enables the agent to execute multi-step loops to achieve goals using tools.
                    If disabled, the agent will only respond with a single message (Chat Mode).
                </p>
            </div>

            {formData.action_mode_enabled && (
                <div className="animation-slide-in">
                    <div className="form-group">
                        <label>Autonomy Level</label>
                        <select
                            value={formData.autonomy_level}
                            onChange={(e) => setFormData(prev => ({ ...prev, autonomy_level: e.target.value as AgentAutonomyLevel }))}
                        >
                            <option value={AgentAutonomyLevel.LOW}>Low - Ask for permission before critical actions</option>
                            <option value={AgentAutonomyLevel.MEDIUM}>Medium - Autonomous for safe actions</option>
                            <option value={AgentAutonomyLevel.HIGH}>High - Fully autonomous (Use with caution)</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Max Steps per Execution: {formData.max_steps}</label>
                        <input
                            type="range"
                            min="1"
                            max="50"
                            step="1"
                            value={formData.max_steps}
                            onChange={(e) => setFormData(prev => ({ ...prev, max_steps: parseInt(e.target.value) }))}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#666' }}>
                            <span>1 Step</span>
                            <span>50 Steps</span>
                        </div>
                    </div>
                </div>
            )}

            <hr style={{ margin: '20px 0', border: 'none', borderTop: '1px solid #eee' }} />

            <div className="form-group">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <label style={{ margin: 0 }}>MCP Enabled</label>
                    <div className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={formData.mcp_enabled}
                            onChange={(e) => setFormData(prev => ({ ...prev, mcp_enabled: e.target.checked }))}
                            id="mcp-mode-toggle"
                        />
                        <label htmlFor="mcp-mode-toggle"></label>
                    </div>
                </div>
                <p className="field-hint">
                    Enables the Model Context Protocol (MCP) client to connect to external MCP servers.
                </p>
            </div>
        </div>
    );

    const renderConnections = () => (
        <div className="agent-builder-section">
            <h2 className="section-title">
                <span className="section-icon">🔗</span>
                Connections
            </h2>
            <p className="section-description">
                Connect your agent to external services. Configure and test credentials before saving.
            </p>

            <div className="connections-grid">
                {[
                    { type: 'github', name: 'GitHub', icon: '🐙', description: 'Connect to GitHub for repo access' },
                    { type: 'slack', name: 'Slack', icon: '💬', description: 'Send messages to Slack channels' },
                    { type: 'telegram', name: 'Telegram', icon: '📱', description: 'Telegram bot integration' },
                    { type: 'gmail', name: 'Gmail', icon: '📧', description: 'Read and send emails' },
                    { type: 'google_drive', name: 'Google Drive', icon: '📁', description: 'Access files in Drive' },
                    { type: 'notion', name: 'Notion', icon: '📔', description: 'Access Notion workspaces' },
                    { type: 'jira', name: 'Jira', icon: '📋', description: 'Manage Jira issues' },
                    { type: 'discord', name: 'Discord', icon: '🎮', description: 'Connect to Discord servers' },
                ].map(conn => {
                    const isConnected = formData.connections.some(c => c.type === conn.type);
                    const connection = formData.connections.find(c => c.type === conn.type);
                    const hasConfig = connection && Object.keys(connection.config).length > 0;

                    return (
                        <div key={conn.type} className={`connection-card ${isConnected ? 'active' : ''}`}>
                            <div className="connection-header">
                                <span className="connection-icon">{conn.icon}</span>
                                <h4>{conn.name}</h4>
                            </div>
                            <p>{conn.description}</p>

                            <div className="connection-actions">
                                <button
                                    type="button"
                                    className={`btn-toggle ${isConnected ? 'connected' : ''}`}
                                    onClick={() => toggleConnection(conn.type, conn.name, conn.description)}
                                >
                                    {isConnected ? 'Enabled' : 'Enable'}
                                </button>

                                {isConnected && (
                                    <button
                                        type="button"
                                        className="btn-secondary btn-sm"
                                        onClick={() => setShowConnectionModal({ type: conn.type, name: conn.name })}
                                    >
                                        {hasConfig ? '⚙️ Configure' : '⚠️ Setup Required'}
                                    </button>
                                )}
                            </div>
                            {isConnected && !hasConfig && (
                                <div className="config-warning">Configuration missing</div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );

    const renderMCPServers = () => (
        <div className="agent-builder-section">
            <h2 className="section-title">
                <span className="section-icon">🔌</span>
                MCP Servers
            </h2>
            <p className="section-description">
                Connect to Model Context Protocol (MCP) servers for extended capabilities.
            </p>

            <div className="mcp-servers-list">
                {formData.mcp_servers.map((server, index) => (
                    <div key={index} className="mcp-server-item">
                        <div className="mcp-server-row">
                            <div className="form-group">
                                <label>Server Name</label>
                                <input
                                    type="text"
                                    value={server.server_name}
                                    onChange={e => handleMCPServerChange(index, 'server_name', e.target.value)}
                                    placeholder="e.g., filesystem"
                                    className={errors[`mcp_${index}_name`] ? 'error' : ''}
                                />
                            </div>
                            <div className="form-group">
                                <label>Server URL / Command</label>
                                <input
                                    type="text"
                                    value={server.server_url}
                                    onChange={e => handleMCPServerChange(index, 'server_url', e.target.value)}
                                    placeholder="e.g., npx @modelcontextprotocol/server-filesystem"
                                    className={errors[`mcp_${index}_url`] ? 'error' : ''}
                                />
                            </div>
                            <button
                                type="button"
                                className="btn-icon remove"
                                onClick={() => handleRemoveMCPServer(index)}
                                title="Remove"
                            >
                                🗑️
                            </button>
                        </div>
                        <div className="mcp-server-row">
                            <div className="form-group">
                                <label>Transport Type</label>
                                <select
                                    value={server.transport_type}
                                    onChange={e => handleMCPServerChange(index, 'transport_type', e.target.value)}
                                >
                                    <option value="stdio">stdio</option>
                                    <option value="sse">SSE (Server-Sent Events)</option>
                                    <option value="websocket">WebSocket</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <input
                                    type="text"
                                    value={server.description}
                                    onChange={e => handleMCPServerChange(index, 'description', e.target.value)}
                                    placeholder="Optional description..."
                                />
                            </div>
                        </div>
                    </div>
                ))}

                <button type="button" className="btn-secondary" onClick={handleAddMCPServer}>
                    + Add MCP Server
                </button>
            </div>
        </div>
    );

    const renderReview = () => {
        const selectedModel = formData.model_type === 'saas'
            ? models.find(m => m.id === formData.model_id)
            : localModels.find(m => m.id === formData.local_model_id);

        return (
            <div className="agent-builder-section review-section">
                <h2 className="section-title">
                    <span className="section-icon">✅</span>
                    Review & Create
                </h2>
                <p className="section-description">
                    Review your agent configuration before creating.
                </p>

                {errors.submit && <div className="error-banner">{errors.submit}</div>}

                <div className="review-grid">
                    <div className="review-card">
                        <h3>📝 Basic Info</h3>
                        <dl>
                            <dt>Name</dt>
                            <dd>{formData.name}</dd>
                            <dt>Description</dt>
                            <dd>{formData.description || 'No description'}</dd>
                            <dt>Public</dt>
                            <dd>{formData.is_public ? 'Yes' : 'No'}</dd>
                        </dl>
                    </div>

                    <div className="review-card">
                        <h3>🤖 Model</h3>
                        <dl>
                            <dt>Model</dt>
                            <dd>{(selectedModel as any)?.display_name || (selectedModel as any)?.name || 'Not selected'}</dd>
                            <dt>Provider</dt>
                            <dd>
                                {(() => {
                                    const p = (selectedModel as any)?.provider;
                                    if (!p) return (selectedModel as any)?.source || '-';
                                    return typeof p === 'string' ? p : (p.display_name || p.name);
                                })()}
                            </dd>
                            <dt>Temperature</dt>
                            <dd>{formData.temperature}</dd>
                            <dt>Max Tokens</dt>
                            <dd>{formData.max_tokens}</dd>
                        </dl>
                    </div>

                    <div className="review-card">
                        <h3>⚡ Autonomy</h3>
                        <dl>
                            <dt>Action Mode</dt>
                            <dd>{formData.action_mode_enabled ? 'Enabled' : 'Disabled'}</dd>
                            {formData.action_mode_enabled && (
                                <>
                                    <dt>Level</dt>
                                    <dd>{formData.autonomy_level}</dd>
                                    <dt>Max Steps</dt>
                                    <dd>{formData.max_steps}</dd>
                                </>
                            )}
                            <dt>MCP</dt>
                            <dd>{formData.mcp_enabled ? 'Enabled' : 'Disabled'}</dd>
                        </dl>
                    </div>

                    <div className="review-card">
                        <h3>💬 Prompts</h3>
                        <dl>
                            <dt>System Prompt</dt>
                            <dd className="prompt-preview">
                                {formData.system_prompt.substring(0, 200)}
                                {formData.system_prompt.length > 200 && '...'}
                            </dd>
                            <dt>Goal Prompt</dt>
                            <dd>{formData.goal_prompt ? 'Set' : 'Not set'}</dd>
                            <dt>Service Prompt</dt>
                            <dd>{formData.service_prompt ? 'Set' : 'Not set'}</dd>
                        </dl>
                    </div>

                    <div className="review-card">
                        <h3>🔧 Tools & Integrations</h3>
                        <dl>
                            <dt>Tools</dt>
                            <dd>
                                {formData.tools.length > 0
                                    ? formData.tools.map(t => t.display_name).join(', ')
                                    : 'None'}
                            </dd>
                            <dt>MCP Servers</dt>
                            <dd>{formData.mcp_servers.filter(m => m.server_name).length}</dd>
                        </dl>
                    </div>
                </div>
            </div>
        );
    };

    // ========================================================================
    // HELPER FUNCTIONS
    // ========================================================================

    const getToolIcon = (type: string): string => {
        const icons: Record<string, string> = {
            github: '🐙',
            slack: '💬',
            telegram: '📱',
            filesystem: '📁',
            web: '🌐',
            email: '📧',
            database: '🗄️',
            api: '🔌',
        };
        return icons[type] || '🔧';
    };

    // ========================================================================
    // RENDER
    // ========================================================================

    if (loading) {
        return (
            <div className="agent-builder-loading">
                <div className="loading-spinner"></div>
                <p>Loading...</p>
            </div>
        );
    }

    return (
        <div className="agent-builder">
            <div className="agent-builder-header">
                <button className="btn-back" onClick={() => navigate(-1)}>
                    ← Back
                </button>
                <h1>{isEditing ? 'Edit Agent' : 'Create New Agent'}</h1>
            </div>

            <div className="agent-builder-content">
                {/* Sidebar Navigation */}
                <nav className="agent-builder-nav">
                    {sections.map((section, index) => (
                        <button
                            key={section.id}
                            className={`nav-item ${currentSection === section.id ? 'active' : ''}`}
                            onClick={() => setCurrentSection(section.id)}
                        >
                            <span className="nav-icon">{section.icon}</span>
                            <span className="nav-label">{section.label}</span>
                            <span className="nav-number">{index + 1}</span>
                        </button>
                    ))}
                </nav>

                {/* Main Form */}
                <main className="agent-builder-main">
                    {currentSection === 'basic' && renderBasicInfo()}
                    {currentSection === 'model' && renderModelSelection()}
                    {currentSection === 'prompts' && renderPrompts()}
                    {currentSection === 'knowledge' && renderKnowledge()}
                    {currentSection === 'actions' && renderActions()}
                    {currentSection === 'tools' && renderTools()}
                    {currentSection === 'connections' && renderConnections()}
                    {currentSection === 'mcp' && renderMCPServers()}
                    {currentSection === 'review' && renderReview()}

                    {/* Navigation Buttons */}
                    <div className="form-actions">
                        {currentSection !== 'basic' && (
                            <button
                                type="button"
                                className="btn-secondary"
                                onClick={goToPrevSection}
                            >
                                ← Previous
                            </button>
                        )}

                        {currentSection !== 'review' ? (
                            <button
                                type="button"
                                className="btn-primary"
                                onClick={goToNextSection}
                            >
                                Next →
                            </button>
                        ) : (
                            <button
                                type="button"
                                className="btn-primary btn-create"
                                onClick={handleSubmit}
                                disabled={saving}
                            >
                                {saving ? 'Saving...' : isEditing ? 'Update Agent' : 'Create Agent'}
                            </button>
                        )}
                    </div>
                    {errors.submit && (
                        <div className="error-alert" style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#fee2e2', border: '1px solid #ef4444', borderRadius: '0.375rem', color: '#b91c1c' }}>
                            ⚠️ {errors.submit}
                        </div>
                    )}
                </main>
            </div>

            {/* API Key Modal */}
            {showApiKeyModal && (
                <ApiKeyModal
                    provider={(() => {
                        const m = models.find(m => m.id === formData.model_id);
                        if (!m?.provider) return '';
                        return typeof m.provider === 'string' ? m.provider : m.provider.display_name;
                    })()}
                    onClose={() => setShowApiKeyModal(false)}
                    onSave={async (key) => {
                        try {
                            const m = models.find(m => m.id === formData.model_id);
                            const pName = m?.provider
                                ? (typeof m.provider === 'string' ? m.provider : m.provider.display_name)
                                : '';

                            const newKey = await agentBuilderApi.createApiKey({
                                provider: pName,
                                api_key: key,
                                label: 'Default',
                            });
                            setApiKeys(prev => [...prev, newKey]);
                            setFormData(prev => ({ ...prev, api_key_id: newKey.id }));
                            setShowApiKeyModal(false);
                        } catch (error) {
                            console.error('Failed to save API key:', error);
                        }
                    }}
                />
            )}

            {/* Tool Config Modal */}
            {showToolConfigModal && (
                <ToolConfigModal
                    tool={showToolConfigModal}
                    toolInfo={availableTools.find(t => t.type === showToolConfigModal.type)}
                    onClose={() => setShowToolConfigModal(null)}
                    onSave={(config) => handleToolConfigSave(showToolConfigModal, config)}
                />
            )}

            {/* Connection Config Modal */}
            {showConnectionModal && (
                <ConnectionConfigModal
                    type={showConnectionModal.type}
                    name={showConnectionModal.name}
                    initialConfig={formData.connections.find(c => c.type === showConnectionModal.type)?.config || {}}
                    onClose={() => setShowConnectionModal(null)}
                    onSave={(config) => handleConnectionSave(showConnectionModal.type, config)}
                />
            )}
        </div>
    );
};

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

interface ApiKeyModalProps {
    provider: string;
    onClose: () => void;
    onSave: (key: string) => void;
}

const ApiKeyModal: React.FC<ApiKeyModalProps> = ({ provider, onClose, onSave }) => {
    const [apiKey, setApiKey] = useState('');
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        if (!apiKey.trim()) return;
        setSaving(true);
        await onSave(apiKey);
        setSaving(false);
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content api-key-modal" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                <h2>Add API Key for {provider}</h2>
                <p>Enter your API key to use models from {provider}.</p>

                <div className="form-group">
                    <label>API Key</label>
                    <input
                        type="password"
                        value={apiKey}
                        onChange={e => setApiKey(e.target.value)}
                        placeholder="Enter your API key..."
                        autoFocus
                    />
                </div>

                <div className="modal-actions">
                    <button className="btn-secondary" onClick={onClose}>Cancel</button>
                    <button
                        className="btn-primary"
                        onClick={handleSave}
                        disabled={!apiKey.trim() || saving}
                    >
                        {saving ? 'Saving...' : 'Save Key'}
                    </button>
                </div>
            </div>
        </div>
    );
};

interface ToolConfigModalProps {
    tool: SelectedTool;
    toolInfo?: AvailableTool;
    onClose: () => void;
    onSave: (config: Record<string, unknown>) => void;
}

const ToolConfigModal: React.FC<ToolConfigModalProps> = ({ tool, toolInfo, onClose, onSave }) => {
    const [config, setConfig] = useState<Record<string, string>>(
        Object.fromEntries(
            Object.entries(tool.config || {}).map(([k, v]) => [k, String(v)])
        )
    );

    const schema = toolInfo?.config_schema || {};

    const handleSave = () => {
        onSave(config);
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content tool-config-modal" onClick={e => e.stopPropagation()}>
                <h2>Configure {tool.display_name}</h2>
                <p>{tool.description}</p>

                {Object.entries(schema).map(([key, fieldSchema]) => {
                    const field = fieldSchema as { type: string; description?: string; secret?: boolean };
                    return (
                        <div key={key} className="form-group">
                            <label>{key}</label>
                            {field.description && <p className="field-hint">{field.description}</p>}
                            <input
                                type={field.secret ? 'password' : 'text'}
                                value={config[key] || ''}
                                onChange={e => setConfig(prev => ({ ...prev, [key]: e.target.value }))}
                            />
                        </div>
                    );
                })}

                <div className="modal-actions">
                    <button className="btn-secondary" onClick={onClose}>Cancel</button>
                    <button className="btn-primary" onClick={handleSave}>Save Configuration</button>
                </div>
            </div>
        </div>
    );
};

interface ConnectionConfigModalProps {
    type: string;
    name: string;
    initialConfig: Record<string, unknown>;
    onClose: () => void;
    onSave: (config: Record<string, unknown>) => void;
}

const ConnectionConfigModal: React.FC<ConnectionConfigModalProps> = ({ type, name, initialConfig, onClose, onSave }) => {
    const [config, setConfig] = useState<Record<string, string>>({});
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);

    // Initialize config from props
    useEffect(() => {
        const newConfig: Record<string, string> = {};
        const schema = CONNECTION_SCHEMAS[type];
        if (schema) {
            Object.keys(schema.fields).forEach(key => {
                newConfig[key] = (initialConfig[key] as string) || '';
            });
        }
        setConfig(newConfig);
    }, [type, initialConfig]);

    const handleTest = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            const schema = CONNECTION_SCHEMAS[type];
            if (!schema) {
                setTestResult({ ok: false, message: 'No test configuration available for this service.' });
                return;
            }

            const response = await agentBuilderApi.testConnection(schema.testService, config);
            setTestResult({
                ok: response.ok,
                message: response.message || (response.ok ? 'Connection successful!' : 'Connection failed')
            });
        } catch (error: any) {
            setTestResult({
                ok: false,
                message: error.response?.data?.message || error.message || 'Connection failed'
            });
        } finally {
            setTesting(false);
        }
    };

    const handleSave = () => {
        onSave(config);
    };

    const schema = CONNECTION_SCHEMAS[type];

    if (!schema) {
        return (
            <div className="modal-backdrop" onClick={onClose}>
                <div className="modal-content" onClick={e => e.stopPropagation()}>
                    <h2>Configure {name}</h2>
                    <p>Configuration not yet available for this service.</p>
                    <button className="btn-secondary" onClick={onClose}>Close</button>
                </div>
            </div>
        );
    }

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content connection-config-modal" onClick={e => e.stopPropagation()}>
                <h2>Configure {name}</h2>
                <p>Enter credentials for {name} to enable this integration.</p>

                <div className="config-form">
                    {Object.entries(schema.fields).map(([key, field]) => (
                        <div key={key} className="form-group">
                            <label>{field.label} {field.required && '*'}</label>
                            <input
                                type={field.type}
                                value={config[key] || ''}
                                onChange={e => setConfig(prev => ({ ...prev, [key]: e.target.value }))}
                                placeholder={field.placeholder}
                            />
                            {field.description && <p className="field-hint">{field.description}</p>}
                        </div>
                    ))}
                </div>

                {testResult && (
                    <div className={`test-result ${testResult.ok ? 'success' : 'error'}`} style={{
                        padding: '10px',
                        borderRadius: '6px',
                        marginBottom: '15px',
                        background: testResult.ok ? '#f0fdf4' : '#fef2f2',
                        color: testResult.ok ? '#15803d' : '#b91c1c',
                        border: `1px solid ${testResult.ok ? '#bbf7d0' : '#fecaca'}`
                    }}>
                        {testResult.ok ? '✅ ' : '❌ '} {testResult.message}
                    </div>
                )}

                <div className="modal-actions" style={{ justifyContent: 'space-between' }}>
                    <button
                        className="btn-secondary"
                        onClick={handleTest}
                        disabled={testing}
                        style={{ marginRight: 'auto' }}
                    >
                        {testing ? 'Testing...' : 'Test Connection'}
                    </button>
                    <div style={{ display: 'flex', gap: '10px' }}>
                        <button className="btn-secondary" onClick={onClose}>Cancel</button>
                        <button className="btn-primary" onClick={handleSave}>Save Config</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AgentBuilderForm;
