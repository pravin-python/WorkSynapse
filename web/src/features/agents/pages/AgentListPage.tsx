/**
 * Agent Builder Page
 * ==================
 * 
 * Main page for listing and managing custom AI agents.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { agentBuilderApi, CustomAgent, AgentListResponse } from '../api/agentBuilderApi';
import './AgentListPage.css';

export const AgentListPage: React.FC = () => {
    const navigate = useNavigate();

    // State
    const [agents, setAgents] = useState<CustomAgent[]>([]);
    const [loading, setLoading] = useState(true);
    const [totalAgents, setTotalAgents] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize] = useState(12);
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [showMyAgentsOnly, setShowMyAgentsOnly] = useState(false);
    const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

    // Load agents
    useEffect(() => {
        loadAgents();
    }, [currentPage, statusFilter, showMyAgentsOnly]);

    const loadAgents = async () => {
        setLoading(true);
        try {
            const response: AgentListResponse = await agentBuilderApi.getAgents(
                currentPage,
                pageSize,
                statusFilter || undefined,
                !showMyAgentsOnly
            );
            setAgents(response.agents);
            setTotalAgents(response.total);
        } catch (error) {
            console.error('Failed to load agents:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (agentId: number) => {
        try {
            await agentBuilderApi.deleteAgent(agentId);
            setAgents(prev => prev.filter(a => a.id !== agentId));
            setConfirmDelete(null);
        } catch (error) {
            console.error('Failed to delete agent:', error);
        }
    };

    const handleActivate = async (agentId: number) => {
        try {
            const updated = await agentBuilderApi.activateAgent(agentId);
            setAgents(prev => prev.map(a => a.id === agentId ? updated : a));
        } catch (error) {
            console.error('Failed to activate agent:', error);
        }
    };

    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'active': return 'status-active';
            case 'draft': return 'status-draft';
            case 'paused': return 'status-paused';
            case 'archived': return 'status-archived';
            case 'error': return 'status-error';
            default: return '';
        }
    };

    const getStatusIcon = (status: string): string => {
        switch (status) {
            case 'active': return '🟢';
            case 'draft': return '📝';
            case 'paused': return '⏸️';
            case 'archived': return '📦';
            case 'error': return '🔴';
            default: return '⚪';
        }
    };

    const totalPages = Math.ceil(totalAgents / pageSize);

    return (
        <div className="agent-list-page">
            <header className="page-header">
                <div className="header-content">
                    <h1>
                        <span className="header-icon">🤖</span>
                        AI Agents
                    </h1>
                    <p className="header-description">
                        Create and manage your AI agents with custom models, tools, and integrations.
                    </p>
                </div>
                <button
                    className="btn-create-agent"
                    onClick={() => navigate('/ai/agents/create')}
                >
                    <span className="btn-icon">+</span>
                    Create Agent
                </button>
            </header>

            <div className="filters-bar">
                <div className="filter-group">
                    <label>Status:</label>
                    <select
                        value={statusFilter}
                        onChange={e => {
                            setStatusFilter(e.target.value);
                            setCurrentPage(1);
                        }}
                    >
                        <option value="">All Statuses</option>
                        <option value="active">Active</option>
                        <option value="draft">Draft</option>
                        <option value="paused">Paused</option>
                        <option value="archived">Archived</option>
                    </select>
                </div>

                <div className="filter-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={showMyAgentsOnly}
                            onChange={e => {
                                setShowMyAgentsOnly(e.target.checked);
                                setCurrentPage(1);
                            }}
                        />
                        My agents only
                    </label>
                </div>

                <div className="agents-count">
                    Showing <strong>{agents.length}</strong> of <strong>{totalAgents}</strong> agents
                </div>
            </div>

            {loading ? (
                <div className="loading-state">
                    <div className="loading-spinner"></div>
                    <p>Loading agents...</p>
                </div>
            ) : agents.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">🤖</div>
                    <h2>No agents yet</h2>
                    <p>Create your first AI agent to get started.</p>
                    <button
                        className="btn-primary"
                        onClick={() => navigate('/ai/agents/create')}
                    >
                        Create Your First Agent
                    </button>
                </div>
            ) : (
                <div className="agents-grid">
                    {agents.map(agent => (
                        <div
                            key={agent.id}
                            className="agent-card"
                            style={{ '--agent-color': agent.color || '#6366f1' } as React.CSSProperties}
                        >
                            <div className="agent-card-header">
                                <div
                                    className="agent-avatar"
                                    style={{ backgroundColor: agent.color || '#6366f1' }}
                                >
                                    {agent.name.charAt(0).toUpperCase()}
                                </div>
                                <div className="agent-info">
                                    <h3 className="agent-name">{agent.name}</h3>
                                    <span className={`agent-status ${getStatusColor(agent.status)}`}>
                                        {getStatusIcon(agent.status)} {agent.status}
                                    </span>
                                </div>
                                {agent.is_public && (
                                    <span className="public-badge" title="Public Agent">🌐</span>
                                )}
                            </div>

                            <p className="agent-description">
                                {agent.description || 'No description'}
                            </p>

                            <div className="agent-model">
                                <span className="model-provider">{agent.model_provider}</span>
                                <span className="model-name">{agent.model_name}</span>
                            </div>

                            <div className="agent-stats">
                                <div className="stat">
                                    <span className="stat-icon">💬</span>
                                    <span className="stat-value">{agent.total_messages}</span>
                                    <span className="stat-label">Messages</span>
                                </div>
                                <div className="stat">
                                    <span className="stat-icon">🎯</span>
                                    <span className="stat-value">{agent.total_sessions}</span>
                                    <span className="stat-label">Sessions</span>
                                </div>
                                <div className="stat">
                                    <span className="stat-icon">💰</span>
                                    <span className="stat-value">${agent.total_cost_usd.toFixed(2)}</span>
                                    <span className="stat-label">Cost</span>
                                </div>
                            </div>

                            {agent.last_used_at && (
                                <div className="last-used">
                                    Last used: {new Date(agent.last_used_at).toLocaleDateString()}
                                </div>
                            )}

                            <div className="agent-actions">
                                {agent.status === 'draft' && (
                                    <button
                                        className="btn-action activate"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleActivate(agent.id);
                                        }}
                                        title="Activate Agent"
                                    >
                                        ▶️ Activate
                                    </button>
                                )}
                                <button
                                    className="btn-action edit"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        navigate(`/ai/agents/${agent.id}/edit`);
                                    }}
                                    title="Edit Agent"
                                >
                                    ✏️ Edit
                                </button>
                                <button
                                    className="btn-action chat"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        navigate(`/ai/agents/${agent.id}/chat`);
                                    }}
                                    title="Chat with Agent"
                                    disabled={agent.status !== 'active'}
                                >
                                    💬 Chat
                                </button>
                                <button
                                    className="btn-action delete"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setConfirmDelete(agent.id);
                                    }}
                                    title="Delete Agent"
                                >
                                    🗑️
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {totalPages > 1 && (
                <div className="pagination">
                    <button
                        className="btn-page"
                        disabled={currentPage === 1}
                        onClick={() => setCurrentPage(prev => prev - 1)}
                    >
                        ← Previous
                    </button>
                    <span className="page-info">
                        Page {currentPage} of {totalPages}
                    </span>
                    <button
                        className="btn-page"
                        disabled={currentPage === totalPages}
                        onClick={() => setCurrentPage(prev => prev + 1)}
                    >
                        Next →
                    </button>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {confirmDelete !== null && (
                <div className="modal-backdrop" onClick={() => setConfirmDelete(null)}>
                    <div className="modal-content confirm-modal" onClick={e => e.stopPropagation()}>
                        <h2>🗑️ Delete Agent?</h2>
                        <p>Are you sure you want to delete this agent? This action cannot be undone.</p>
                        <div className="modal-actions">
                            <button
                                className="btn-secondary"
                                onClick={() => setConfirmDelete(null)}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn-danger"
                                onClick={() => handleDelete(confirmDelete)}
                            >
                                Delete Agent
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AgentListPage;
