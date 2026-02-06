/**
 * Agent Builder API Module
 * ========================
 * 
 * API functions for the Custom Agent Builder feature.
 */

import { api } from '../../../services/apiClient';

// ============================================================================
// TYPES
// ============================================================================

export interface AgentModel {
    id: number;
    name: string;
    display_name: string;
    provider: string;
    description: string | null;
    requires_api_key: boolean;
    api_key_prefix: string | null;
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
    has_api_key: boolean;
    key_count: number;
}

export interface AgentApiKey {
    id: number;
    provider: string;
    label: string;
    key_preview: string;
    is_active: boolean;
    is_valid: boolean;
    last_validated_at: string | null;
    last_used_at: string | null;
    usage_count: number;
    created_at: string;
}

export interface AgentTool {
    id: number;
    agent_id: number;
    tool_type: string;
    tool_name: string;
    display_name: string;
    description: string | null;
    config_json: Record<string, unknown> | null;
    is_enabled: boolean;
    requires_auth: boolean;
    is_configured: boolean;
    created_at: string;
    updated_at: string;
}

export interface AgentConnection {
    id: number;
    agent_id: number;
    connection_type: string;
    name: string;
    display_name: string;
    description: string | null;
    config_json: Record<string, unknown> | null;
    is_active: boolean;
    is_connected: boolean;
    last_connected_at: string | null;
    last_error: string | null;
    created_at: string;
}

export interface AgentMCPServer {
    id: number;
    agent_id: number;
    server_name: string;
    server_url: string;
    description: string | null;
    config_json: Record<string, unknown> | null;
    transport_type: string;
    requires_auth: boolean;
    is_enabled: boolean;
    is_connected: boolean;
    last_health_check: string | null;
    last_error: string | null;
    available_tools: string[] | null;
    available_resources: string[] | null;
    created_at: string;
    updated_at: string;
}

export interface CustomAgent {
    id: number;
    name: string;
    description: string | null;
    slug: string;
    model_id: number;
    model_name: string | null;
    model_provider: string | null;
    api_key_id: number | null;
    api_key_preview: string | null;
    temperature: number;
    max_tokens: number;
    top_p: number;
    frequency_penalty: number;
    presence_penalty: number;
    system_prompt: string;
    goal_prompt: string | null;
    service_prompt: string | null;
    status: string;
    is_public: boolean;
    total_sessions: number;
    total_messages: number;
    total_tokens_used: number;
    total_cost_usd: number;
    last_used_at: string | null;
    version: number;
    avatar_url: string | null;
    color: string | null;
    icon: string | null;
    created_at: string;
    updated_at: string;
}

export interface CustomAgentDetail extends CustomAgent {
    tools: AgentTool[];
    connections: AgentConnection[];
    mcp_servers: AgentMCPServer[];
}

export interface AgentListResponse {
    agents: CustomAgent[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface AvailableTool {
    type: string;
    name: string;
    display_name: string;
    description: string;
    icon: string;
    requires_auth: boolean;
    config_schema: Record<string, unknown> | null;
}

export interface AgentCreationCheck {
    can_create: boolean;
    has_api_key: boolean;
    model_name: string;
    model_provider: string;
    requires_api_key: boolean;
    available_keys: AgentApiKey[];
    message: string;
}

// Create/Update DTOs
export interface CreateAgentDTO {
    name: string;
    description?: string;
    model_id: number;
    api_key_id?: number;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    system_prompt: string;
    goal_prompt?: string;
    service_prompt?: string;
    is_public?: boolean;
    avatar_url?: string;
    color?: string;
    icon?: string;
    tools?: CreateToolDTO[];
    connections?: CreateConnectionDTO[];
    mcp_servers?: CreateMCPServerDTO[];
}

export interface UpdateAgentDTO {
    name?: string;
    description?: string;
    model_id?: number;
    api_key_id?: number;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    system_prompt?: string;
    goal_prompt?: string;
    service_prompt?: string;
    status?: string;
    is_public?: boolean;
    avatar_url?: string;
    color?: string;
    icon?: string;
}

export interface CreateApiKeyDTO {
    provider: string;
    label?: string;
    api_key: string;
}

export interface UpdateApiKeyDTO {
    label?: string;
    api_key?: string;
    is_active?: boolean;
}

export interface CreateToolDTO {
    tool_type: string;
    tool_name: string;
    display_name: string;
    description?: string;
    config_json?: Record<string, unknown>;
    is_enabled?: boolean;
}

export interface CreateConnectionDTO {
    connection_type: string;
    name: string;
    display_name: string;
    description?: string;
    config_json?: Record<string, unknown>;
}

export interface CreateMCPServerDTO {
    server_name: string;
    server_url: string;
    description?: string;
    config_json?: Record<string, unknown>;
    transport_type?: string;
    requires_auth?: boolean;
    auth_type?: string;
    auth_credentials?: string;
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

const BASE_URL = '/agent-builder';

// Models
export const agentBuilderApi = {
    // Models
    getModels: (provider?: string) =>
        api.get<AgentModel[]>(`${BASE_URL}/models${provider ? `?provider=${provider}` : ''}`),

    getModel: (modelId: number) =>
        api.get<AgentModel>(`${BASE_URL}/models/${modelId}`),

    seedModels: () =>
        api.post<{ message: string; count: number }>(`${BASE_URL}/models/seed`),

    // API Keys
    getApiKeys: (provider?: string) =>
        api.get<AgentApiKey[]>(`${BASE_URL}/api-keys${provider ? `?provider=${provider}` : ''}`),

    getApiKey: (keyId: number) =>
        api.get<AgentApiKey>(`${BASE_URL}/api-keys/${keyId}`),

    createApiKey: (data: CreateApiKeyDTO) =>
        api.post<AgentApiKey>(`${BASE_URL}/api-keys`, data),

    updateApiKey: (keyId: number, data: UpdateApiKeyDTO) =>
        api.patch<AgentApiKey>(`${BASE_URL}/api-keys/${keyId}`, data),

    deleteApiKey: (keyId: number) =>
        api.delete<{ message: string }>(`${BASE_URL}/api-keys/${keyId}`),

    checkApiKeyExists: (provider: string) =>
        api.post<{ has_api_key: boolean; key_count: number; keys: AgentApiKey[] }>(
            `${BASE_URL}/api-keys/check?provider=${provider}`
        ),

    // Agents
    getAgents: (page = 1, pageSize = 20, status?: string, includePublic = true) =>
        api.get<AgentListResponse>(
            `${BASE_URL}/agents?page=${page}&page_size=${pageSize}&include_public=${includePublic}${status ? `&status=${status}` : ''}`
        ),

    getAgent: (agentId: number) =>
        api.get<CustomAgentDetail>(`${BASE_URL}/agents/${agentId}`),

    createAgent: (data: CreateAgentDTO) =>
        api.post<CustomAgentDetail>(`${BASE_URL}/agents`, data),

    updateAgent: (agentId: number, data: UpdateAgentDTO) =>
        api.patch<CustomAgentDetail>(`${BASE_URL}/agents/${agentId}`, data),

    deleteAgent: (agentId: number) =>
        api.delete<{ message: string }>(`${BASE_URL}/agents/${agentId}`),

    activateAgent: (agentId: number) =>
        api.post<CustomAgent>(`${BASE_URL}/agents/${agentId}/activate`),

    checkAgentCreation: (modelId: number) =>
        api.post<AgentCreationCheck>(`${BASE_URL}/agents/check-creation`, { model_id: modelId }),

    // Tools
    getAvailableTools: () =>
        api.get<AvailableTool[]>(`${BASE_URL}/tools/available`),

    addTool: (agentId: number, data: CreateToolDTO) =>
        api.post<AgentTool>(`${BASE_URL}/agents/${agentId}/tools`, data),

    updateTool: (agentId: number, toolId: number, data: Partial<CreateToolDTO>) =>
        api.patch<AgentTool>(`${BASE_URL}/agents/${agentId}/tools/${toolId}`, data),

    removeTool: (agentId: number, toolId: number) =>
        api.delete<{ message: string }>(`${BASE_URL}/agents/${agentId}/tools/${toolId}`),

    // MCP Servers
    addMCPServer: (agentId: number, data: CreateMCPServerDTO) =>
        api.post<AgentMCPServer>(`${BASE_URL}/agents/${agentId}/mcp-servers`, data),

    removeMCPServer: (agentId: number, mcpId: number) =>
        api.delete<{ message: string }>(`${BASE_URL}/agents/${agentId}/mcp-servers/${mcpId}`),
};

export default agentBuilderApi;
