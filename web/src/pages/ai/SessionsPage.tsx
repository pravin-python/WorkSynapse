/**
 * WorkSynapse AI Sessions Page
 */
import React from 'react';
import { Bot, MessageSquare } from 'lucide-react';
import './AI.css';

export function SessionsPage() {
    return (
        <div className="ai-page">
            <header className="page-header">
                <div className="header-content">
                    <h1><MessageSquare size={28} />AI Sessions</h1>
                    <p>View AI agent conversation history</p>
                </div>
            </header>

            <div className="empty-state">
                <Bot size={48} />
                <h3>No sessions yet</h3>
                <p>AI agent sessions will appear here once agents are running</p>
            </div>
        </div>
    );
}

export default SessionsPage;
