/**
 * Agent Chat Page
 * ================
 * ChatGPT-style conversation interface for AI agents.
 * Supports streaming responses, file uploads, and conversation management.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
    agentChatApi,
    sendMessageStream,
    Conversation,
    ChatMessage,
    FileUploadResult,
} from '../api/agentChatApi';
import { agentBuilderApi, CustomAgent } from '../api/agentBuilderApi';
import './AgentChatPage.css';

// ============================================================================
// HELPERS
// ============================================================================

function formatTime(iso: string) {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatFileSize(bytes: number) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(type: string) {
    if (type.startsWith('image/')) return '🖼️';
    if (type === 'application/pdf') return '📄';
    if (type.includes('spreadsheet') || type.includes('excel') || type.includes('csv')) return '📊';
    if (type.includes('word') || type.includes('document')) return '📝';
    return '📎';
}

// ============================================================================
// COMPONENT
// ============================================================================

const AgentChatPage: React.FC = () => {
    const { agentId } = useParams<{ agentId: string }>();
    const parsedAgentId = parseInt(agentId || '0', 10);

    // State
    const [agent, setAgent] = useState<CustomAgent | null>(null);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeConvId, setActiveConvId] = useState<number | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputText, setInputText] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const [currentStep, setCurrentStep] = useState('');
    const [activeTool, setActiveTool] = useState('');
    const [uploadedFiles, setUploadedFiles] = useState<FileUploadResult[]>([]);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [loadingMessages, setLoadingMessages] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Refs
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // ========================================================================
    // DATA FETCHING
    // ========================================================================

    // Load agent info
    useEffect(() => {
        if (!parsedAgentId) return;
        agentBuilderApi.getAgent(parsedAgentId)
            .then(setAgent)
            .catch(err => {
                console.error('Failed to load agent:', err);
                setError('Failed to load agent');
            });
    }, [parsedAgentId]);

    // Load conversations
    const loadConversations = useCallback(async () => {
        if (!parsedAgentId) return;
        try {
            const res = await agentChatApi.getConversations(parsedAgentId);
            setConversations(res.conversations);
        } catch (err) {
            console.error('Failed to load conversations:', err);
        }
    }, [parsedAgentId]);

    useEffect(() => {
        loadConversations();
    }, [loadConversations]);

    // Load messages when conversation changes
    useEffect(() => {
        if (!activeConvId) {
            setMessages([]);
            return;
        }
        setLoadingMessages(true);
        agentChatApi.getMessages(activeConvId)
            .then(res => {
                setMessages(res.messages);
                setLoadingMessages(false);
            })
            .catch(err => {
                console.error('Failed to load messages:', err);
                setLoadingMessages(false);
            });
    }, [activeConvId]);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamingContent]);

    // Auto-resize textarea
    const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputText(e.target.value);
        const ta = e.target;
        ta.style.height = 'auto';
        ta.style.height = Math.min(ta.scrollHeight, 150) + 'px';
    };

    // ========================================================================
    // ACTIONS
    // ========================================================================

    const createNewConversation = async () => {
        if (!parsedAgentId) return;
        try {
            const conv = await agentChatApi.createConversation(parsedAgentId);
            setConversations(prev => [conv, ...prev]);
            setActiveConvId(conv.id);
            setMessages([]);
        } catch (err) {
            console.error('Failed to create conversation:', err);
            setError('Failed to create conversation');
        }
    };

    const deleteConversation = async (convId: number) => {
        try {
            await agentChatApi.deleteConversation(convId);
            setConversations(prev => prev.filter(c => c.id !== convId));
            if (activeConvId === convId) {
                setActiveConvId(null);
                setMessages([]);
            }
        } catch (err) {
            console.error('Failed to delete conversation:', err);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || !activeConvId) return;

        for (const file of Array.from(files)) {
            try {
                const result = await agentChatApi.uploadFile(activeConvId, file);
                setUploadedFiles(prev => [...prev, result]);
            } catch (err: any) {
                setError(err?.response?.data?.detail || 'Failed to upload file');
            }
        }
        // Reset input
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const removeUploadedFile = (fileId: number) => {
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    const sendMessage = async () => {
        if (!inputText.trim() || isStreaming) return;

        // Auto-create conversation if none
        let convId = activeConvId;
        if (!convId) {
            try {
                const conv = await agentChatApi.createConversation(parsedAgentId);
                setConversations(prev => [conv, ...prev]);
                setActiveConvId(conv.id);
                convId = conv.id;
            } catch {
                setError('Failed to create conversation');
                return;
            }
        }

        const content = inputText.trim();
        const fileIds = uploadedFiles.map(f => f.id);

        // Optimistic add user message
        const tempUserMsg: ChatMessage = {
            id: Date.now(),
            conversation_id: convId,
            sender_type: 'user',
            content,
            message_type: 'text',
            tokens_input: 0,
            tokens_output: 0,
            tokens_total: 0,
            duration_ms: 0,
            tool_calls: null,
            files: uploadedFiles.map(f => ({
                id: f.id,
                message_id: null,
                conversation_id: convId!,
                file_name: f.file_name,
                original_file_name: f.original_file_name,
                file_path: '',
                file_type: f.file_type,
                file_size: f.file_size,
                thumbnail_path: null,
                is_rag_ingested: false,
                created_at: new Date().toISOString(),
            })),
            created_at: new Date().toISOString(),
        };

        setMessages(prev => [...prev, tempUserMsg]);
        setInputText('');
        setUploadedFiles([]);
        setIsStreaming(true);
        setStreamingContent('');
        setCurrentStep('');
        setActiveTool('');
        setError(null);

        // Reset textarea height
        if (textareaRef.current) textareaRef.current.style.height = 'auto';

        try {
            await sendMessageStream(
                convId, content, 'text',
                fileIds.length > 0 ? fileIds : null,
                {
                    onStep: (step) => setCurrentStep(step),
                    onToken: (token) => setStreamingContent(prev => prev + token),
                    onToolStart: (tool) => setActiveTool(tool),
                    onToolEnd: () => setActiveTool(''),
                    onDone: () => {
                        setIsStreaming(false);
                        // Reload messages to get the saved versions
                        if (convId) {
                            agentChatApi.getMessages(convId).then(res => {
                                setMessages(res.messages);
                            });
                        }
                        loadConversations();
                    },
                    onError: (err) => {
                        setError(err);
                        setIsStreaming(false);
                    },
                }
            );
        } catch (err: any) {
            setError(err.message || 'Failed to send message');
            setIsStreaming(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // Clear error after 5s
    useEffect(() => {
        if (error) {
            const t = setTimeout(() => setError(null), 5000);
            return () => clearTimeout(t);
        }
    }, [error]);

    // ========================================================================
    // RENDER HELPERS
    // ========================================================================

    const agentColor = agent?.color || '#6366f1';
    const agentInitial = agent?.name?.charAt(0)?.toUpperCase() || 'A';

    const renderMessage = (msg: ChatMessage) => {
        const isUser = msg.sender_type === 'user';
        const isSystem = msg.sender_type === 'system';

        return (
            <div key={msg.id} className={`message-row ${msg.sender_type}`}>
                <div className={`message-avatar-wrap ${msg.sender_type}-msg`}>
                    {isUser ? '👤' : isSystem ? '⚙️' : agentInitial}
                </div>
                <div className="message-content-wrap">
                    <div className="message-bubble">
                        {msg.content}
                    </div>
                    {/* File attachments */}
                    {msg.files && msg.files.length > 0 && (
                        <div className="message-files">
                            {msg.files.map(f => (
                                f.file_type.startsWith('image/') ? (
                                    <img
                                        key={f.id}
                                        src={agentChatApi.getFileUrl(f.id)}
                                        alt={f.original_file_name}
                                        className="message-image-preview"
                                    />
                                ) : (
                                    <a
                                        key={f.id}
                                        href={agentChatApi.getFileUrl(f.id)}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="message-file-card"
                                    >
                                        <span className="file-icon">{getFileIcon(f.file_type)}</span>
                                        <div className="file-info">
                                            <div className="file-info-name">{f.original_file_name}</div>
                                            <div className="file-info-size">{formatFileSize(f.file_size)}</div>
                                        </div>
                                    </a>
                                )
                            ))}
                        </div>
                    )}
                    <div className="message-time">{formatTime(msg.created_at)}</div>
                </div>
            </div>
        );
    };

    // ========================================================================
    // RENDER
    // ========================================================================

    return (
        <div className="agent-chat-page">
            {/* SIDEBAR */}
            <div className={`chat-sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
                <div className="sidebar-header">
                    <h3 className="sidebar-title">Conversations</h3>
                    <button className="new-chat-btn" onClick={createNewConversation}>
                        ＋ New
                    </button>
                </div>
                <div className="conversation-list">
                    {conversations.length === 0 ? (
                        <div className="empty-conversations">
                            <span className="empty-icon">💬</span>
                            <p>No conversations yet.<br />Start a new chat!</p>
                        </div>
                    ) : (
                        conversations.map(conv => (
                            <div
                                key={conv.id}
                                className={`conversation-item ${conv.id === activeConvId ? 'active' : ''}`}
                                onClick={() => setActiveConvId(conv.id)}
                            >
                                <div className="conv-icon">💬</div>
                                <div className="conv-details">
                                    <div className="conv-title">
                                        {conv.title || 'New Chat'}
                                    </div>
                                    <div className="conv-preview">
                                        {conv.last_message_preview || `${conv.message_count} messages`}
                                    </div>
                                </div>
                                <button
                                    className="conv-delete-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        deleteConversation(conv.id);
                                    }}
                                    title="Delete"
                                >
                                    🗑️
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* MAIN CHAT */}
            <div className="chat-main">
                {/* Header */}
                <div className="chat-header">
                    <button
                        className="sidebar-toggle-btn"
                        onClick={() => setSidebarOpen(prev => !prev)}
                        title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
                    >
                        {sidebarOpen ? '◀' : '▶'}
                    </button>
                    <div
                        className="agent-avatar"
                        style={{ background: `linear-gradient(135deg, ${agentColor}, ${agentColor}88)` }}
                    >
                        {agent?.avatar_url ? (
                            <img src={agent.avatar_url} alt={agent.name} style={{ width: 36, height: 36, borderRadius: 10 }} />
                        ) : agentInitial}
                    </div>
                    <div className="agent-header-info">
                        <h3 className="agent-header-name">{agent?.name || 'Agent'}</h3>
                        <p className="agent-header-model">
                            {agent?.model_provider && agent?.model_name
                                ? `${agent.model_provider} · ${agent.model_name}`
                                : 'AI Agent'}
                        </p>
                    </div>
                </div>

                {/* Messages */}
                <div className="messages-area">
                    {loadingMessages ? (
                        <div className="loading-messages">Loading messages...</div>
                    ) : messages.length === 0 && !isStreaming ? (
                        <div className="welcome-screen">
                            <div
                                className="welcome-avatar"
                                style={{ background: `linear-gradient(135deg, ${agentColor}, ${agentColor}88)` }}
                            >
                                {agentInitial}
                            </div>
                            <h2>Chat with {agent?.name || 'Agent'}</h2>
                            <p>{agent?.description || 'Start a conversation with this AI agent. Ask anything!'}</p>
                        </div>
                    ) : (
                        <div className="messages-container">
                            {messages.map(renderMessage)}

                            {/* Streaming indicators */}
                            {isStreaming && (
                                <>
                                    {currentStep && (
                                        <div className="step-indicator">
                                            <span className="step-dot" />
                                            {currentStep}
                                        </div>
                                    )}

                                    {activeTool && (
                                        <div className="tool-call-indicator">
                                            <span className="tool-spinner" />
                                            Using tool: {activeTool}
                                        </div>
                                    )}

                                    {streamingContent ? (
                                        <div className="message-row agent">
                                            <div className="message-avatar-wrap agent-msg">
                                                {agentInitial}
                                            </div>
                                            <div className="message-content-wrap">
                                                <div className="message-bubble">
                                                    {streamingContent}
                                                    <span className="cursor-blink">▌</span>
                                                </div>
                                            </div>
                                        </div>
                                    ) : !currentStep && !activeTool && (
                                        <div className="typing-indicator">
                                            <div className="message-avatar-wrap agent-msg">
                                                {agentInitial}
                                            </div>
                                            <div className="typing-dots">
                                                <span className="typing-dot" />
                                                <span className="typing-dot" />
                                                <span className="typing-dot" />
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Input */}
                <div className="chat-input-area">
                    <div className="chat-input-container">
                        {/* Upload preview */}
                        {uploadedFiles.length > 0 && (
                            <div className="upload-preview-bar">
                                {uploadedFiles.map(f => (
                                    <div key={f.id} className="upload-preview-item">
                                        <span>{getFileIcon(f.file_type)}</span>
                                        <span>{f.original_file_name}</span>
                                        <button
                                            className="remove-upload"
                                            onClick={() => removeUploadedFile(f.id)}
                                        >
                                            ×
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="input-row">
                            <button
                                className="attach-btn"
                                onClick={() => fileInputRef.current?.click()}
                                title="Attach file"
                                disabled={!activeConvId && !parsedAgentId}
                            >
                                📎
                            </button>
                            <input
                                ref={fileInputRef}
                                type="file"
                                className="hidden-file-input"
                                multiple
                                accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.md,.json"
                                onChange={handleFileUpload}
                            />
                            <textarea
                                ref={textareaRef}
                                className="chat-textarea"
                                placeholder={`Message ${agent?.name || 'Agent'}...`}
                                value={inputText}
                                onChange={handleTextareaInput}
                                onKeyDown={handleKeyDown}
                                rows={1}
                                disabled={isStreaming}
                            />
                            <button
                                className={`send-btn ${isStreaming ? 'streaming' : ''}`}
                                onClick={sendMessage}
                                disabled={(!inputText.trim() && uploadedFiles.length === 0) || isStreaming}
                                title={isStreaming ? 'Generating...' : 'Send message'}
                            >
                                {isStreaming ? '⏹' : '➤'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Error toast */}
            {error && <div className="chat-error-toast">{error}</div>}
        </div>
    );
};

export default AgentChatPage;
