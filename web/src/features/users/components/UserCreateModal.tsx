import React, { useEffect, useState } from 'react';
import { X, Save, AlertTriangle, Shield } from 'lucide-react';
import { roleService } from '../../roles/services/roleService';
import { userService } from '../services/userService';
import { Role } from '../../roles/types';
import { UserCreateData } from '../types';

interface UserCreateModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export function UserCreateModal({ isOpen, onClose, onSuccess }: UserCreateModalProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [roles, setRoles] = useState<Role[]>([]);
    const [formData, setFormData] = useState<UserCreateData>({
        full_name: '',
        email: '',
        password: '',
        username: '',
        role_id: undefined
    });
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            loadRoles();
            // Reset form
            setFormData({
                full_name: '',
                email: '',
                password: '',
                username: '',
                role_id: undefined
            });
            setError(null);
        }
    }, [isOpen]);

    const loadRoles = async () => {
        try {
            // Fetch all roles to populate dropdown
            const data = await roleService.getAll({ limit: 100 });
            setRoles(data.items.filter(r => !r.is_system)); // Optionally filter if system roles shouldn't be assigned manually or generally available
        } catch (err) {
            console.error("Failed to load roles", err);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await userService.create(formData);
            onSuccess();
            onClose();
        } catch (err: any) {
            console.error("Failed to create user", err);
            setError(err.response?.data?.detail || "Failed to create user. Please check your input.");
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay open" onClick={onClose}>
            <div className="modal-container" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
                <div className="modal-header">
                    <div className="modal-icon">
                        <Shield size={24} />
                    </div>
                    <button className="modal-close" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                <div className="modal-content">
                    <h3>Create New User</h3>
                    <p style={{ marginBottom: '20px' }}>Add a new staff member and assign them a role.</p>

                    {error && (
                        <div className="form-error" style={{ marginBottom: '16px' }}>
                            <AlertTriangle size={16} />
                            <span>{error}</span>
                        </div>
                    )}

                    <form id="create-user-form" onSubmit={handleSubmit} className="form-grid" style={{ gridTemplateColumns: '1fr', gap: '16px' }}>
                        <div className="form-group">
                            <label>Full Name</label>
                            <input
                                type="text"
                                required
                                value={formData.full_name}
                                onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                                placeholder="John Doe"
                                className="form-input"
                            />
                        </div>

                        <div className="form-group">
                            <label>Email Address</label>
                            <input
                                type="email"
                                required
                                value={formData.email}
                                onChange={e => setFormData({ ...formData, email: e.target.value })}
                                placeholder="john@example.com"
                                className="form-input"
                            />
                        </div>

                        <div className="form-group">
                            <label>Username (Optional)</label>
                            <input
                                type="text"
                                value={formData.username}
                                onChange={e => setFormData({ ...formData, username: e.target.value })}
                                placeholder="johndoe"
                                className="form-input"
                            />
                        </div>

                        <div className="form-group">
                            <label>Password</label>
                            <input
                                type="password"
                                required
                                minLength={8}
                                value={formData.password}
                                onChange={e => setFormData({ ...formData, password: e.target.value })}
                                placeholder="Type a strong password..."
                                className="form-input"
                            />
                        </div>

                        <div className="form-group">
                            <label>System Role</label>
                            <select
                                required
                                value={formData.role_id || ''}
                                onChange={e => setFormData({ ...formData, role_id: Number(e.target.value) })}
                                className="form-select"
                                style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid hsl(var(--color-border))', background: 'hsl(var(--input-bg))', color: 'hsl(var(--color-text))' }}
                            >
                                <option value="">Select a role...</option>
                                {roles.map(role => (
                                    <option key={role.id} value={role.id}>
                                        {role.name}
                                    </option>
                                ))}
                            </select>
                            <p className="help-text" style={{ fontSize: '0.8rem', color: 'hsl(var(--color-text-muted))', marginTop: '4px' }}>
                                This determines what permissions the user will have.
                            </p>
                        </div>
                    </form>
                </div>

                <div className="modal-actions">
                    <button type="button" className="btn btn-ghost" onClick={onClose} disabled={isLoading}>
                        Cancel
                    </button>
                    <button
                        type="submit"
                        form="create-user-form"
                        className="btn btn-primary"
                        disabled={isLoading}
                    >
                        {isLoading ? <div className="loading-spinner-small"></div> : (
                            <>
                                <Save size={16} style={{ marginRight: '8px' }} />
                                Create User
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
