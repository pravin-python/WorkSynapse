/**
 * WorkSynapse AI Agents Page
 */
import React, { useState } from 'react';
import { Bot, Plus, Play, Pause, Settings, Trash2, RefreshCw } from 'lucide-react';
import './AI.css';

interface Agent {
    id: number;
    name: string;
    type: string;
    status: 'RUNNING' | 'STOPPED' | 'ERROR';
    description: string;
    tasks_completed: number;
    last_run?: string;
}

export function AgentsPage() {
    const [agents] = useState<Agent[]>([
        { id: 1, name: 'Project Planner', type: 'PLANNING', status: 'RUNNING', description: 'Automatically generates project plans and task breakdowns', tasks_completed: 156, last_run: '5 min ago' },
        { id: 2, name: 'Code Reviewer', type: 'REVIEW', status: 'RUNNING', description: 'Reviews code changes and provides feedback', tasks_completed: 89, last_run: '2 min ago' },
        { id: 3, name: 'Sprint Analyzer', type: 'ANALYTICS', status: 'STOPPED', description: 'Analyzes sprint velocity and predicts completion', tasks_completed: 45, last_run: '1 hour ago' },
        { id: 4, name: 'Meeting Summarizer', type: 'NLP', status: 'ERROR', description: 'Transcribes and summarizes meetings', tasks_completed: 23 },
    ]);

    const getStatusBadge = (status: string) => {
        const config: Record<string, { color: string; icon: React.ReactNode }> = {
            RUNNING: { color: 'success', icon: <Play size={12} /> },
            STOPPED: { color: 'muted', icon: <Pause size={12} /> },
            ERROR: { color: 'error', icon: <RefreshCw size={12} /> },
        };
        const { color, icon } = config[status] || config.STOPPED;
        return <span className={`agent-status ${color}`}>{icon} {status.toLowerCase()}</span>;
    };

    return (
        <div className="ai-page">
            <header className="page-header">
                <div className="header-content">
                    <h1><Bot size={28} />AI Agents</h1>
                    <p>Manage and monitor your AI agents</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary">
                        <Plus size={18} />
                        New Agent
                    </button>
                </div>
            </header>

            <div className="agents-grid">
                {agents.map((agent) => (
                    <div key={agent.id} className="agent-card">
                        <div className="agent-header">
                            <div className="agent-icon">
                                <Bot size={24} />
                            </div>
                            {getStatusBadge(agent.status)}
                        </div>
                        <h3>{agent.name}</h3>
                        <span className="agent-type">{agent.type}</span>
                        <p>{agent.description}</p>
                        <div className="agent-stats">
                            <div className="stat">
                                <span className="stat-value">{agent.tasks_completed}</span>
                                <span className="stat-label">Tasks</span>
                            </div>
                            <div className="stat">
                                <span className="stat-value">{agent.last_run || 'Never'}</span>
                                <span className="stat-label">Last Run</span>
                            </div>
                        </div>
                        <div className="agent-actions">
                            {agent.status === 'RUNNING' ? (
                                <button className="btn btn-secondary"><Pause size={16} /> Stop</button>
                            ) : (
                                <button className="btn btn-primary"><Play size={16} /> Start</button>
                            )}
                            <button className="btn-icon"><Settings size={16} /></button>
                            <button className="btn-icon danger"><Trash2 size={16} /></button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default AgentsPage;
