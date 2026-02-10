/**
 * Agent Chat API Module
 * ======================
 * API functions and SSE streaming helper for agent conversations.
 */

import { api } from '../../../services/apiClient';

const BASE = '/agent-chat';

// ============================================================================
// TYPES
// ============================================================================

export interface ChatFile {
    id: number;
    message_id: number | null;
    conversation_id: number;
    file_name: string;
    original_file_name: string;
    file_path: string;
    file_type: string;
    file_size: number;
    thumbnail_path: string | null;
    is_rag_ingested: boolean;
    created_at: string;
}

export interface ChatMessage {
    id: number;
    conversation_id: number;
    sender_type: 'user' | 'agent' | 'system';
    content: string;
    message_type: 'text' | 'image' | 'file' | 'pdf';
    tokens_input: number;
    tokens_output: number;
    tokens_total: number;
    duration_ms: number;
    tool_calls: Array<{ name: string; result?: string }> | null;
    files: ChatFile[];
    created_at: string;
}

export interface MessageListResponse {
    messages: ChatMessage[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface Conversation {
    id: number;
    agent_id: number;
    user_id: number;
    title: string | null;
    thread_id: string;
    is_archived: boolean;
    last_message_at: string | null;
    message_count: number;
    total_tokens_used: number;
    created_at: string;
    updated_at: string;
    last_message_preview: string | null;
    // Detail fields
    agent_name?: string;
    agent_avatar_url?: string;
    agent_color?: string;
}

export interface ConversationListResponse {
    conversations: Conversation[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface FileUploadResult {
    id: number;
    file_name: string;
    original_file_name: string;
    file_type: string;
    file_size: number;
    file_url: string;
}

// SSE event types
export interface SSEEvent {
    type: 'token' | 'step' | 'tool_start' | 'tool_end' | 'message' | 'agent_message' | 'done' | 'error';
    content?: string;
    step?: string;
    tool?: string;
    result?: string;
    message_id?: number;
    thread_id?: string;
    error?: string;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

export const agentChatApi = {
    // Conversations
    createConversation: (agentId: number, title?: string) =>
        api.post<Conversation>(`${BASE}/agents/${agentId}/conversations`, { title }),

    getConversations: (agentId: number, page = 1, pageSize = 20) =>
        api.get<ConversationListResponse>(
            `${BASE}/agents/${agentId}/conversations?page=${page}&page_size=${pageSize}`
        ),

    getConversation: (conversationId: number) =>
        api.get<Conversation>(`${BASE}/conversations/${conversationId}`),

    deleteConversation: (conversationId: number) =>
        api.delete<void>(`${BASE}/conversations/${conversationId}`),

    // Messages
    getMessages: (conversationId: number, page = 1, pageSize = 50) =>
        api.get<MessageListResponse>(
            `${BASE}/conversations/${conversationId}/messages?page=${page}&page_size=${pageSize}`
        ),

    // File upload
    uploadFile: (conversationId: number, file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post<FileUploadResult>(
            `${BASE}/conversations/${conversationId}/upload`,
            formData,
            { headers: { 'Content-Type': 'multipart/form-data' } }
        );
    },

    // File URL builder
    getFileUrl: (fileId: number) =>
        `${import.meta.env.VITE_API_URL || '/api/v1'}${BASE}/files/${fileId}`,
};

// ============================================================================
// SSE STREAMING HELPER
// ============================================================================

/**
 * Send a message and stream the agent's response via Server-Sent Events.
 */
export async function sendMessageStream(
    conversationId: number,
    content: string,
    messageType: string = 'text',
    fileIds: number[] | null = null,
    callbacks: {
        onToken?: (token: string) => void;
        onStep?: (step: string) => void;
        onToolStart?: (tool: string) => void;
        onToolEnd?: (tool: string, result: string) => void;
        onMessage?: (messageId: number) => void;
        onAgentMessage?: (messageId: number) => void;
        onDone?: (threadId: string) => void;
        onError?: (error: string) => void;
    }
): Promise<void> {
    const token = localStorage.getItem('worksynapse-access-token');
    const apiUrl = import.meta.env.VITE_API_URL || '/api/v1';

    const response = await fetch(
        `${apiUrl}${BASE}/conversations/${conversationId}/messages`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
                content,
                message_type: messageType,
                file_ids: fileIds,
            }),
        }
    );

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Parse SSE lines
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;

                try {
                    const event: SSEEvent = JSON.parse(line.slice(6));

                    switch (event.type) {
                        case 'token':
                            callbacks.onToken?.(event.content || '');
                            break;
                        case 'step':
                            callbacks.onStep?.(event.step || '');
                            break;
                        case 'tool_start':
                            callbacks.onToolStart?.(event.tool || '');
                            break;
                        case 'tool_end':
                            callbacks.onToolEnd?.(event.tool || '', event.result || '');
                            break;
                        case 'message':
                            callbacks.onMessage?.(event.message_id || 0);
                            break;
                        case 'agent_message':
                            callbacks.onAgentMessage?.(event.message_id || 0);
                            break;
                        case 'done':
                            callbacks.onDone?.(event.thread_id || '');
                            break;
                        case 'error':
                            callbacks.onError?.(event.error || 'Unknown error');
                            break;
                    }
                } catch {
                    // Skip malformed JSON
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

export default agentChatApi;
