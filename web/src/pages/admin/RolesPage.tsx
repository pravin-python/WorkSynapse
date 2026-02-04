/**
 * WorkSynapse Admin Roles Page
 */
import React, { useState } from 'react';
import { Shield, Plus, Edit, Trash2 } from 'lucide-react';
import './Admin.css';

interface Role {
    id: number;
    name: string;
    description: string;
    permissions: string[];
    user_count: number;
}

export function RolesPage() {
    const [roles] = useState<Role[]>([
        { id: 1, name: 'SUPER_ADMIN', description: 'Full system access', permissions: ['*'], user_count: 1 },
        { id: 2, name: 'ADMIN', description: 'Administrative access', permissions: ['users:*', 'projects:*', 'settings:*'], user_count: 2 },
        { id: 3, name: 'MANAGER', description: 'Project management access', permissions: ['projects:*', 'tasks:*', 'users:read'], user_count: 3 },
        { id: 4, name: 'DEVELOPER', description: 'Standard developer access', permissions: ['projects:read', 'tasks:*', 'notes:*'], user_count: 15 },
        { id: 5, name: 'VIEWER', description: 'Read-only access', permissions: ['projects:read', 'tasks:read'], user_count: 5 },
    ]);

    return (
        <div className="admin-page">
            <header className="page-header">
                <div className="header-content">
                    <h1><Shield size={28} />Roles & Permissions</h1>
                    <p>Manage roles and their permissions</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary">
                        <Plus size={18} />
                        Add Role
                    </button>
                </div>
            </header>

            <div className="roles-grid">
                {roles.map((role) => (
                    <div key={role.id} className="role-card">
                        <div className="role-header">
                            <Shield size={24} className="role-icon" />
                            <div className="role-actions">
                                <button className="btn-icon" title="Edit"><Edit size={16} /></button>
                                <button className="btn-icon danger" title="Delete"><Trash2 size={16} /></button>
                            </div>
                        </div>
                        <h3>{role.name}</h3>
                        <p>{role.description}</p>
                        <div className="role-stats">
                            <span>{role.user_count} users</span>
                            <span>{role.permissions.length} permissions</span>
                        </div>
                        <div className="role-permissions">
                            {role.permissions.slice(0, 3).map((perm) => (
                                <span key={perm} className="permission-tag">{perm}</span>
                            ))}
                            {role.permissions.length > 3 && (
                                <span className="permission-more">+{role.permissions.length - 3} more</span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default RolesPage;
