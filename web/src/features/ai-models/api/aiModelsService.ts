/**
 * AI Models Service
 * =================
 * 
 * API service for managing AI model providers and API keys.
 * All API keys are encrypted at rest using Fernet encryption.
 */
import { api } from '../../../services/apiClient';

// ===========================================
// TYPES
// ===========================================

export interface LLMProvider {
    id: number;
    name: string;
    type: string;
    display_name: string;
    description: string | null;
    base_url: string | null;
    requires_api_key: boolean;
    icon: string | null;
    is_active: boolean;
    config_schema: any;
    created_at: string;
    has_api_key: boolean;
    key_count: number;
}

export interface LLMApiKey {
    id: number;
    provider_id: number;
    provider_name: string | null;
    label: string;
    key_preview: string;
    extra_params: any;
    is_active: boolean;
    is_valid: boolean;
    last_used_at: string | null;
    usage_count: number;
    created_at: string;
}

export interface LLMApiKeyCreate {
    provider_id: number;
    api_key: string;
    label?: string;
    extra_params?: any;
}

export interface LLMApiKeyUpdate {
    label?: string;
    api_key?: string;
    is_active?: boolean;
    extra_params?: any;
}

export interface AIAgent {
    id: number;
    name: string;
    description: string | null;
    provider_id: number;
    provider_name: string | null;
    api_key_id: number;
    key_preview: string | null;
    model_name: string;
    type: string;
    temperature: number;
    max_tokens: number;
    system_prompt: string | null;
    status: string;
    is_public: boolean;
    total_requests: number;
    total_tokens_used: number;
    last_used_at: string | null;
    created_at: string;
}

export interface AIAgentCreate {
    name: string;
    description?: string;
    provider_id: number;
    api_key_id: number;
    model_name: string;
    type?: string;
    temperature?: number;
    max_tokens?: number;
    system_prompt?: string;
    is_public?: boolean;
}

export interface AIAgentUpdate {
    name?: string;
    description?: string;
    api_key_id?: number;
    model_name?: string;
    type?: string;
    temperature?: number;
    max_tokens?: number;
    system_prompt?: string;
    status?: string;
    is_public?: boolean;
}

export interface AgentCreateCheck {
    provider_id: number;
}

export interface AgentCreateCheckResponse {
    can_create: boolean;
    has_api_key: boolean;
    provider_name: string;
    available_keys: LLMApiKey[];
    message: string;
}

export interface LLMProviderCreate {
    name: string;
    type: string;
    display_name: string;
    description?: string;
    base_url?: string;
    requires_api_key?: boolean;
    icon?: string;
    available_models?: string[];
}

// ===========================================
// PROVIDER ENDPOINTS
// ===========================================

/**
 * Get all LLM providers with user's key status
 */
export async function getProviders(): Promise<LLMProvider[]> {
    return api.get<LLMProvider[]>('/llm/providers');
}

/**
 * Get a specific provider by ID
 */
export async function getProvider(providerId: number): Promise<LLMProvider> {
    return api.get<LLMProvider>(`/llm/providers/${providerId}`);
}

/**
 * Seed default LLM providers (Admin only)
 */
export async function seedProviders(): Promise<{ message: string; count: number }> {
    return api.post('/llm/providers/seed');
}

// ===========================================
// API KEY ENDPOINTS
// ===========================================

/**
 * Get all API keys for the current user
 */
export async function getApiKeys(providerId?: number): Promise<LLMApiKey[]> {
    const params = providerId ? `?provider_id=${providerId}` : '';
    return api.get<LLMApiKey[]>(`/llm/keys${params}`);
}

/**
 * Get a specific API key
 */
export async function getApiKey(keyId: number): Promise<LLMApiKey> {
    return api.get<LLMApiKey>(`/llm/keys/${keyId}`);
}

/**
 * Create a new encrypted API key
 */
export async function createApiKey(data: LLMApiKeyCreate): Promise<LLMApiKey> {
    return api.post<LLMApiKey>('/llm/keys', data);
}

/**
 * Update an API key
 */
export async function updateApiKey(keyId: number, data: LLMApiKeyUpdate): Promise<LLMApiKey> {
    return api.patch<LLMApiKey>(`/llm/keys/${keyId}`, data);
}

/**
 * Delete an API key
 */
export async function deleteApiKey(keyId: number): Promise<{ message: string }> {
    return api.delete<{ message: string }>(`/llm/keys/${keyId}`);
}

// ===========================================
// AGENT ENDPOINTS
// ===========================================

/**
 * Get all agents for the current user
 */
export async function getAgents(): Promise<AIAgent[]> {
    return api.get<AIAgent[]>('/llm/agents');
}

/**
 * Get a specific agent
 */
export async function getAgent(agentId: number): Promise<AIAgent> {
    return api.get<AIAgent>(`/llm/agents/${agentId}`);
}

/**
 * Check if an agent can be created for a provider
 */
export async function checkAgentCreation(data: AgentCreateCheck): Promise<AgentCreateCheckResponse> {
    return api.post<AgentCreateCheckResponse>('/llm/agents/check', data);
}

/**
 * Create a new agent
 */
export async function createAgent(data: AIAgentCreate): Promise<AIAgent> {
    return api.post<AIAgent>('/llm/agents', data);
}

/**
 * Update an agent
 */
export async function updateAgent(agentId: number, data: AIAgentUpdate): Promise<AIAgent> {
    return api.patch<AIAgent>(`/llm/agents/${agentId}`, data);
}

/**
 * Delete an agent
 */
export async function deleteAgent(agentId: number): Promise<{ message: string }> {
    return api.delete<{ message: string }>(`/llm/agents/${agentId}`);
}

// ===========================================
// AGENT MODEL REGISTRY (NEW)
// ===========================================

// ===========================================
// AGENT MODEL REGISTRY (NEW)
// ===========================================

export interface AgentModel {
    id: number;
    name: string;
    display_name: string;
    provider_id: number;
    provider?: LLMProvider;
    description: string | null;
    requires_api_key: boolean;
    api_key_prefix: string | null;
    base_url: string | null;
    context_window: number;
    max_output_tokens: number;
    supports_vision: boolean;
    supports_tools: boolean;
    supports_streaming: boolean;
    input_price_per_million: number;
    output_price_per_million: number;
    is_active: boolean;
    is_deprecated: boolean;
    created_at: string;
}

export interface AgentModelCreate {
    name: string;
    display_name: string;
    provider_id: number;
    description?: string;
    requires_api_key?: boolean;
    api_key_prefix?: string;
    base_url?: string;
    context_window: number;
    max_output_tokens: number;
    supports_vision?: boolean;
    supports_tools?: boolean;
    supports_streaming?: boolean;
    input_price_per_million?: number;
    output_price_per_million?: number;
}

export interface AgentModelUpdate {
    display_name?: string;
    description?: string;
    is_active?: boolean;
    is_deprecated?: boolean;
    input_price_per_million?: number;
    output_price_per_million?: number;
    // name and provider are usually locked after creation
}

/**
 * Get all agent models (registry)
 */
export async function getAgentModels(params?: { provider_id?: number; is_active?: boolean; search?: string }): Promise<AgentModel[]> {
    const query = new URLSearchParams();
    if (params?.provider_id) query.append('provider_id', String(params.provider_id));
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    if (params?.search) query.append('search', params.search);

    return api.get<AgentModel[]>(`/agent-models?${query.toString()}`);
}

/**
 * Get models for a specific provider
 */
export async function getProviderModels(providerId: number): Promise<AgentModel[]> {
    return api.get<AgentModel[]>(`/llm/providers/${providerId}/models`);
}

/**
 * Create a new agent model
 */
export async function createAgentModel(data: AgentModelCreate): Promise<AgentModel> {
    return api.post<AgentModel>('/agent-models', data);
}

/**
 * Update an agent model
 */
export async function updateAgentModel(modelId: number, data: AgentModelUpdate): Promise<AgentModel> {
    return api.put<AgentModel>(`/agent-models/${modelId}`, data);
}

/**
 * Soft delete an agent model
 */
export async function deleteAgentModel(modelId: number): Promise<{ message: string }> {
    return api.delete<{ message: string }>(`/agent-models/${modelId}`);
}

// ===========================================
// UTILITY FUNCTIONS
// ===========================================

/**
 * Validate API key format for a provider
 */
export function validateApiKeyFormat(
    apiKey: string,
    providerType: string
): { valid: boolean; error: string } {
    if (!apiKey || apiKey.length < 10) {
        return { valid: false, error: 'API key is too short' };
    }

    const validations: Record<string, { prefix: string; minLength: number; error: string }> = {
        openai: {
            prefix: 'sk-',
            minLength: 40,
            error: "OpenAI keys should start with 'sk-'"
        },
        anthropic: {
            prefix: 'sk-ant-',
            minLength: 40,
            error: "Anthropic keys should start with 'sk-ant-'"
        },
        huggingface: {
            prefix: 'hf_',
            minLength: 20,
            error: "HuggingFace keys should start with 'hf_'"
        },
        google: {
            prefix: '',
            minLength: 30,
            error: ''
        },
        // ... (existing code)
        gemini: {
            prefix: '',
            minLength: 30,
            error: ''
        },
        groq: {
            prefix: 'gsk_',
            minLength: 20,
            error: "Groq keys should start with 'gsk_'"
        },
    };

    const rule = validations[providerType.toLowerCase()];
    if (rule) {
        if (rule.prefix && !apiKey.startsWith(rule.prefix)) {
            return { valid: false, error: rule.error };
        }
        if (apiKey.length < rule.minLength) {
            return { valid: false, error: `Key should be at least ${rule.minLength} characters` };
        }
    }

    return { valid: true, error: '' };
}

/**
 * Get provider icon emoji
 */
export function getProviderIcon(providerType: string): string {
    const icons: Record<string, string> = {
        openai: '🤖',
        anthropic: '🔮',
        google: '🌐',
        gemini: '💎',
        huggingface: '🤗',
        ollama: '🖥️',
        azure_openai: '☁️',
        cohere: '⚡',
        groq: '🚀',
        custom: '🔧',
    };
    return icons[providerType.toLowerCase()] || '🔑';
}

/**
 * Get status badge color class
 */
export function getStatusBadgeClass(status: string): string {
    switch (status) {
        case 'active':
            return 'success';
        case 'inactive':
        case 'paused':
            return 'warning';
        case 'error':
            return 'error';
        default:
            return 'info';
    }
}

// Export all service functions as a single object
const aiModelsService = {
    // Providers
    getProviders,
    getProvider,
    seedProviders,
    // API Keys
    getApiKeys,
    getApiKey,
    createApiKey,
    updateApiKey,
    deleteApiKey,
    // Agents
    getAgents,
    getAgent,
    checkAgentCreation,
    createAgent,
    updateAgent,
    deleteAgent,
    // Utilities
    validateApiKeyFormat,
    getProviderIcon,
    getStatusBadgeClass,
    // Agent Registry
    getAgentModels,
    getProviderModels,
    createAgentModel,
    updateAgentModel,
    deleteAgentModel,
};

export default aiModelsService;
