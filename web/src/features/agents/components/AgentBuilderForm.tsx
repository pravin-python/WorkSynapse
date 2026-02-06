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

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { agentBuilderApi, AgentModel, AgentApiKey, AvailableTool, CreateAgentDTO, UpdateAgentDTO, CustomAgentDetail } from '../api/agentBuilderApi';
import './AgentBuilderForm.css';

// ============================================================================
// TYPES
// ============================================================================

interface FormData {
    // Basic Info
    name: string;
    description: string;

    // Model
    model_id: number | null;
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

type FormSection = 'basic' | 'model' | 'prompts' | 'tools' | 'connections' | 'mcp' | 'review';

// ============================================================================
// COMPONENT
// ============================================================================

export const AgentBuilderForm: React.FC = () => {
    const navigate = useNavigate();
    const { agentId } = useParams<{ agentId: string }>();
    const isEditing = !!agentId;

    // State
    const [currentSection, setCurrentSection] = useState<FormSection>('basic');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [errors, setErrors] = useState<FormErrors>({});

    // Data
    const [models, setModels] = useState<AgentModel[]>([]);
    const [apiKeys, setApiKeys] = useState<AgentApiKey[]>([]);
    const [availableTools, setAvailableTools] = useState<AvailableTool[]>([]);
    const [existingAgent, setExistingAgent] = useState<CustomAgentDetail | null>(null);

    // Modals
    const [showApiKeyModal, setShowApiKeyModal] = useState(false);
    const [showToolConfigModal, setShowToolConfigModal] = useState<SelectedTool | null>(null);

    // Form Data
    const [formData, setFormData] = useState<FormData>({
        name: '',
        description: '',
        model_id: null,
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
        is_public: false,
        color: '#6366f1',
        icon: 'robot',
    });

    // Sections configuration
    const sections: { id: FormSection; label: string; icon: string }[] = [
        { id: 'basic', label: 'Basic Info', icon: '📝' },
        { id: 'model', label: 'Model Selection', icon: '🤖' },
        { id: 'prompts', label: 'Prompts', icon: '💬' },
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
            const [modelsRes, toolsRes] = await Promise.all([
                agentBuilderApi.getModels(),
                agentBuilderApi.getAvailableTools(),
            ]);
            setModels(modelsRes);
            setAvailableTools(toolsRes);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadExistingAgent = async (id: number) => {
        try {
            const agent = await agentBuilderApi.getAgent(id);
            setExistingAgent(agent);

            // Populate form with existing data
            setFormData({
                name: agent.name,
                description: agent.description || '',
                model_id: agent.model_id,
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
                is_public: agent.is_public,
                color: agent.color || '#6366f1',
                icon: agent.icon || 'robot',
            });

            // Load API keys for the model's provider
            if (agent.model_provider) {
                const keysRes = await agentBuilderApi.getApiKeys(agent.model_provider);
                setApiKeys(keysRes);
            }
        } catch (error) {
            console.error('Failed to load agent:', error);
        }
    };

    // ========================================================================
    // MODEL SELECTION
    // ========================================================================

    const handleModelSelect = async (modelId: number) => {
        const model = models.find(m => m.id === modelId);
        if (!model) return;

        setFormData(prev => ({ ...prev, model_id: modelId, api_key_id: null }));
        setErrors(prev => ({ ...prev, model_id: '', api_key_id: '' }));

        // Load API keys for this provider
        try {
            const keysRes = await agentBuilderApi.getApiKeys(model.provider);
            setApiKeys(keysRes);

            // If model requires API key and none exists, show modal
            if (model.requires_api_key && keysRes.length === 0) {
                setShowApiKeyModal(true);
            }
        } catch (error) {
            console.error('Failed to load API keys:', error);
        }
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
                if (!formData.model_id) {
                    newErrors.model_id = 'Please select a model';
                }
                const selectedModel = models.find(m => m.id === formData.model_id);
                if (selectedModel?.requires_api_key && !formData.api_key_id) {
                    newErrors.api_key_id = 'API key is required for this model';
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
                model_id: formData.model_id!,
                api_key_id: formData.api_key_id || undefined,
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
            };

            if (isEditing && agentId) {
                await agentBuilderApi.updateAgent(parseInt(agentId), agentData as UpdateAgentDTO);
            } else {
                await agentBuilderApi.createAgent(agentData);
            }

            navigate('/ai/agents');
        } catch (error: unknown) {
            console.error('Failed to save agent:', error);
            setErrors({ submit: (error as Error).message || 'Failed to save agent' });
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

    const renderModelSelection = () => {
        const selectedModel = models.find(m => m.id === formData.model_id);

        return (
            <div className="agent-builder-section">
                <h2 className="section-title">
                    <span className="section-icon">🤖</span>
                    Model Selection
                </h2>
                <p className="section-description">
                    Choose the AI model that will power your agent.
                </p>

                {errors.model_id && <div className="error-banner">{errors.model_id}</div>}

                <div className="models-grid">
                    {models.map(model => (
                        <div
                            key={model.id}
                            className={`model-card ${formData.model_id === model.id ? 'selected' : ''} ${!model.is_active ? 'disabled' : ''}`}
                            onClick={() => model.is_active && handleModelSelect(model.id)}
                        >
                            <div className="model-header">
                                <span className="model-provider">{model.provider}</span>
                                {model.has_api_key && <span className="key-badge">✓ Key</span>}
                            </div>
                            <h3 className="model-name">{model.display_name}</h3>
                            <p className="model-description">{model.description}</p>
                            <div className="model-specs">
                                <span title="Context Window">📝 {(model.context_window / 1000).toFixed(0)}k</span>
                                {model.supports_vision && <span title="Vision">👁️</span>}
                                {model.supports_tools && <span title="Tool Use">🔧</span>}
                            </div>
                            {model.input_price_per_million > 0 && (
                                <div className="model-pricing">
                                    ${model.input_price_per_million.toFixed(2)} / ${model.output_price_per_million.toFixed(2)} per 1M tokens
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {selectedModel?.requires_api_key && (
                    <div className="api-key-section">
                        <h3>API Key</h3>
                        {apiKeys.length > 0 ? (
                            <div className="api-key-selector">
                                <select
                                    value={formData.api_key_id || ''}
                                    onChange={e => setFormData(prev => ({ ...prev, api_key_id: parseInt(e.target.value) || null }))}
                                    className={errors.api_key_id ? 'error' : ''}
                                >
                                    <option value="">Select an API key...</option>
                                    {apiKeys.map(key => (
                                        <option key={key.id} value={key.id}>
                                            {key.label} ({key.key_preview}) {!key.is_valid && '⚠️'}
                                        </option>
                                    ))}
                                </select>
                                <button
                                    type="button"
                                    className="btn-secondary"
                                    onClick={() => setShowApiKeyModal(true)}
                                >
                                    + Add New Key
                                </button>
                            </div>
                        ) : (
                            <div className="no-api-key">
                                <p>No API key found for {selectedModel.provider}.</p>
                                <button
                                    type="button"
                                    className="btn-primary"
                                    onClick={() => setShowApiKeyModal(true)}
                                >
                                    Add API Key
                                </button>
                            </div>
                        )}
                        {errors.api_key_id && <span className="error-message">{errors.api_key_id}</span>}
                    </div>
                )}

                {selectedModel && (
                    <div className="model-params">
                        <h3>Model Parameters</h3>
                        <div className="params-grid">
                            <div className="param-group">
                                <label>Temperature: {formData.temperature}</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    value={formData.temperature}
                                    onChange={e => setFormData(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                                />
                                <span className="param-hint">Lower = more focused, Higher = more creative</span>
                            </div>
                            <div className="param-group">
                                <label>Max Tokens: {formData.max_tokens}</label>
                                <input
                                    type="range"
                                    min="100"
                                    max={selectedModel.max_output_tokens}
                                    step="100"
                                    value={formData.max_tokens}
                                    onChange={e => setFormData(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

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

    const renderConnections = () => (
        <div className="agent-builder-section">
            <h2 className="section-title">
                <span className="section-icon">🔗</span>
                Connections
            </h2>
            <p className="section-description">
                Connect your agent to external services like GitHub, Slack, etc.
            </p>

            <div className="connections-grid">
                {[
                    { type: 'github', name: 'GitHub', icon: '🐙', description: 'Connect to GitHub for repo access' },
                    { type: 'slack', name: 'Slack', icon: '💬', description: 'Send messages to Slack channels' },
                    { type: 'notion', name: 'Notion', icon: '📔', description: 'Access Notion workspaces' },
                    { type: 'jira', name: 'Jira', icon: '📋', description: 'Manage Jira issues and projects' },
                    { type: 'discord', name: 'Discord', icon: '🎮', description: 'Connect to Discord servers' },
                ].map(conn => (
                    <div key={conn.type} className="connection-card">
                        <span className="connection-icon">{conn.icon}</span>
                        <h4>{conn.name}</h4>
                        <p>{conn.description}</p>
                        <button type="button" className="btn-secondary" disabled>
                            Connect (Coming Soon)
                        </button>
                    </div>
                ))}
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
        const selectedModel = models.find(m => m.id === formData.model_id);

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
                            <dd>{selectedModel?.display_name || 'Not selected'}</dd>
                            <dt>Provider</dt>
                            <dd>{selectedModel?.provider || '-'}</dd>
                            <dt>Temperature</dt>
                            <dd>{formData.temperature}</dd>
                            <dt>Max Tokens</dt>
                            <dd>{formData.max_tokens}</dd>
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
                </main>
            </div>

            {/* API Key Modal */}
            {showApiKeyModal && (
                <ApiKeyModal
                    provider={models.find(m => m.id === formData.model_id)?.provider || ''}
                    onClose={() => setShowApiKeyModal(false)}
                    onSave={async (key) => {
                        try {
                            const newKey = await agentBuilderApi.createApiKey({
                                provider: models.find(m => m.id === formData.model_id)?.provider || '',
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
            <div className="modal-content api-key-modal" onClick={e => e.stopPropagation()}>
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

export default AgentBuilderForm;
