/**
 * Agent Builder API Module
 * ========================
 * 
 * API functions for the Custom Agent Builder feature.
 */

import { api } from '../../../services/apiClient';

// ============================================================================
// ============================================================================
// TYPES
// ============================================================================

export enum AgentAutonomyLevel {
    LOW = 'low',
    MEDIUM = 'medium',
    HIGH = 'high'
}

export interface AgentModel {
    id: number;
    name: string;
    display_name: string;
    provider_id: number;
    provider?: { id: number; display_name: string } | string | null;
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

/**
 * Represents an API key for an LLM provider.
 */
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

export interface KnowledgeSource {
    id: number;
    name: string;
    type: string;
    metadata: Record<string, unknown> | null;
}

export interface RagDocument {
    id: number;
    filename: string;
    file_type: string;
    created_at: string;
    status?: string;
}

export interface PromptTemplate {
    id: string;
    name: string;
    description: string;
    system_prompt: string;
}

export interface CustomAgent {
    id: number;
    name: string;
    description: string | null;
    slug: string;
    model_id: number | null;
    local_model_id: number | null;
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

    // Memory & RAG
    memory_enabled: boolean;
    memory_config: Record<string, unknown> | null;
    rag_enabled: boolean;
    rag_config: Record<string, unknown> | null;
    rag_documents?: RagDocument[];
    knowledge_sources?: KnowledgeSource[];

    // Action Mode
    action_mode_enabled: boolean;
    autonomy_level: AgentAutonomyLevel;
    max_steps: number;
    mcp_enabled: boolean;

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
    knowledge_sources: KnowledgeSource[];
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
    model_id?: number;
    local_model_id?: number;
    api_key_id?: number;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    system_prompt: string;
    goal_prompt?: string;
    service_prompt?: string;

    // Memory & RAG
    memory_enabled?: boolean;
    memory_config?: Record<string, unknown>;
    rag_enabled?: boolean;
    rag_config?: Record<string, unknown>;
    knowledge_source_ids?: number[];

    // Action Mode
    action_mode_enabled?: boolean;
    autonomy_level?: AgentAutonomyLevel;
    max_steps?: number;
    mcp_enabled?: boolean;

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
    local_model_id?: number;
    api_key_id?: number;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    system_prompt?: string;
    goal_prompt?: string;
    service_prompt?: string;

    // Memory & RAG
    memory_enabled?: boolean;
    memory_config?: Record<string, unknown>;
    rag_enabled?: boolean;
    rag_config?: Record<string, unknown>;
    knowledge_source_ids?: number[];

    // Action Mode
    action_mode_enabled?: boolean;
    autonomy_level?: AgentAutonomyLevel;
    max_steps?: number;
    mcp_enabled?: boolean;

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

export interface AgentExecutionRequest {
    message: string;
    conversation_id?: number;
    thread_id?: string;
    stream?: boolean;
    metadata?: Record<string, unknown>;
}

export interface AgentExecutionResponse {
    response: string;
    thread_id?: string;
    tool_calls: Array<{ name: string; arguments: Record<string, unknown> }>;
    tokens_input: number;
    tokens_output: number;
    tokens_total: number;
    duration_ms: number;
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

const BASE_URL = '/agent-builder';

export const agentBuilderApi = {
    // Models
    getModels: (providerId?: number) =>
        api.get<AgentModel[]>(`${BASE_URL}/models${providerId !== undefined ? `?provider_id=${providerId}` : ''}`),

    getModel: (modelId: number) =>
        api.get<AgentModel>(`${BASE_URL}/models/${modelId}`),

    seedModels: () =>
        api.post<{ message: string; count: number }>(`${BASE_URL}/models/seed`),

    // API Keys
    getApiKeys: (providerId?: number) =>
        api.get<AgentApiKey[]>(`${BASE_URL}/api-keys${providerId !== undefined ? `?provider_id=${providerId}` : ''}`),

    getApiKey: (keyId: number) =>
        api.get<AgentApiKey>(`${BASE_URL}/api-keys/${keyId}`),

    createApiKey: (data: CreateApiKeyDTO) =>
        api.post<AgentApiKey>(`${BASE_URL}/api-keys`, data),

    updateApiKey: (keyId: number, data: UpdateApiKeyDTO) =>
        api.patch<AgentApiKey>(`${BASE_URL}/api-keys/${keyId}`, data),

    deleteApiKey: (keyId: number) =>
        api.delete<{ message: string }>(`${BASE_URL}/api-keys/${keyId}`),

    checkApiKeyExists: (providerId: number) =>
        api.post<{ has_api_key: boolean; key_count: number; keys: AgentApiKey[] }>(
            `${BASE_URL}/api-keys/check?provider_id=${providerId}`
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

    executeAgent: (agentId: number, data: AgentExecutionRequest) =>
        api.post<AgentExecutionResponse>(`${BASE_URL}/agents/${agentId}/execute`, data),

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

    getPromptTemplates: () =>
        api.get<PromptTemplate[]>(`${BASE_URL}/prompt-templates`),

    // RAG
    uploadRagFile: (agentId: number, file: File) => {
        const formData = new FormData();
        formData.append('agent_id', agentId.toString());
        formData.append('file', file);
        return api.post<RagDocument>('/rag/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    getAgentDocuments: (agentId: number) =>
        api.get<RagDocument[]>(`/rag/agents/${agentId}/documents`),

    deleteRagDocument: (documentId: number) =>
        api.delete<{ message: string }>(`/rag/documents/${documentId}`),

    // Integrations Testing
    testConnection: (service: string, config: Record<string, unknown>) => {
        // Map service to endpoint
        const endpointMap: Record<string, string> = {
            slack: '/integrations/test/slack',
            teams: '/integrations/test/teams',
            telegram: '/integrations/test/telegram',
            whatsapp: '/integrations/test/whatsapp',
            gmail: '/integrations/test/gmail',
            google_drive: '/integrations/test/google_drive',
            google_chat: '/integrations/test/google_chat',
            n8n: '/integrations/test/n8n_webhook',
            mcp: '/integrations/test/mcp',
        };

        const endpoint = endpointMap[service] || '/integrations/test';

        // If falling back to generic endpoint, structure data accordingly
        if (endpoint === '/integrations/test') {
            return api.post<{ ok: boolean; message: string; details?: Record<string, unknown> }>(endpoint, {
                type: 'tool',
                service,
                config
            });
        }

        return api.post<{ ok: boolean; message: string; details?: Record<string, unknown> }>(endpoint, config);
    },
};

export default agentBuilderApi;
