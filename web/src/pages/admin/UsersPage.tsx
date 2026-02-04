/**
 * WorkSynapse Admin Users Page
 */
import React, { useState } from 'react';
import { Users, Plus, Search, Shield, MoreVertical, Edit, Trash2, Eye } from 'lucide-react';
import './Admin.css';

interface User {
    id: number;
    email: string;
    full_name: string;
    role: string;
    status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
    created_at: string;
    last_login?: string;
}

export function UsersPage() {
    const [users] = useState<User[]>([
        { id: 1, email: 'alex@worksynapse.io', full_name: 'Alex Johnson', role: 'ADMIN', status: 'ACTIVE', created_at: '2024-01-01', last_login: '2024-02-10' },
        { id: 2, email: 'sarah@worksynapse.io', full_name: 'Sarah Chen', role: 'DEVELOPER', status: 'ACTIVE', created_at: '2024-01-05', last_login: '2024-02-10' },
        { id: 3, email: 'mike@worksynapse.io', full_name: 'Mike Rivera', role: 'MANAGER', status: 'ACTIVE', created_at: '2024-01-10', last_login: '2024-02-09' },
        { id: 4, email: 'jane@worksynapse.io', full_name: 'Jane Smith', role: 'DEVELOPER', status: 'INACTIVE', created_at: '2024-01-15' },
    ]);

    const getStatusBadge = (status: string) => {
        const colors: Record<string, string> = {
            ACTIVE: 'success',
            INACTIVE: 'muted',
            SUSPENDED: 'error',
        };
        return <span className={`status-badge ${colors[status]}`}>{status.toLowerCase()}</span>;
    };

    return (
        <div className="admin-page">
            <header className="page-header">
                <div className="header-content">
                    <h1><Users size={28} />User Management</h1>
                    <p>Manage users and their access</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary">
                        <Plus size={18} />
                        Add User
                    </button>
                </div>
            </header>

            <div className="admin-toolbar">
                <div className="search-wrapper">
                    <Search size={18} />
                    <input type="text" placeholder="Search users..." className="search-input" />
                </div>
            </div>

            <div className="data-table">
                <table>
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Last Login</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map((user) => (
                            <tr key={user.id}>
                                <td>
                                    <div className="user-cell">
                                        <div className="user-avatar-sm">{user.full_name[0]}</div>
                                        <div>
                                            <span className="user-name">{user.full_name}</span>
                                            <span className="user-email">{user.email}</span>
                                        </div>
                                    </div>
                                </td>
                                <td><span className="role-tag">{user.role}</span></td>
                                <td>{getStatusBadge(user.status)}</td>
                                <td>{user.last_login || 'Never'}</td>
                                <td>
                                    <div className="action-buttons">
                                        <button className="btn-icon" title="View"><Eye size={16} /></button>
                                        <button className="btn-icon" title="Edit"><Edit size={16} /></button>
                                        <button className="btn-icon danger" title="Delete"><Trash2 size={16} /></button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default UsersPage;
