import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, FileText, Save, AlertCircle, CheckSquare, Square } from 'lucide-react';
import { Role, Permission } from '../types';
import { roleService } from '../services/roleService';
import '../styles.css';

interface RoleFormProps {
    initialData?: Role;
    mode: 'create' | 'edit';
    onSuccess?: () => void;
}

export function RoleForm({ initialData, mode, onSuccess }: RoleFormProps) {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [permissions, setPermissions] = useState<Permission[]>([]);

    const [formData, setFormData] = useState({
        name: initialData?.name || '',
        description: initialData?.description || '',
        permission_ids: initialData?.permissions.map(p => p.id) || [] as number[],
    });

    useEffect(() => {
        loadPermissions();
    }, []);

    const loadPermissions = async () => {
        try {
            const data = await roleService.getPermissions();
            setPermissions(data);
        } catch (err) {
            console.error('Failed to load permissions', err);
            setError('Failed to load permissions list');
        }
    };

    // Group permissions by resource
    const groupedPermissions = permissions.reduce((acc, perm) => {
        const resource = perm.resource;
        if (!acc[resource]) {
            acc[resource] = [];
        }
        acc[resource].push(perm);
        return acc;
    }, {} as Record<string, Permission[]>);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handlePermissionToggle = (permId: number) => {
        setFormData(prev => {
            const current = prev.permission_ids;
            if (current.includes(permId)) {
                return { ...prev, permission_ids: current.filter(id => id !== permId) };
            } else {
                return { ...prev, permission_ids: [...current, permId] };
            }
        });
    };

    const handleGroupToggle = (resourcePermissions: Permission[]) => {
        const resourcePermIds = resourcePermissions.map(p => p.id);
        const allSelected = resourcePermIds.every(id => formData.permission_ids.includes(id));

        setFormData(prev => {
            if (allSelected) {
                // Deselect all
                return {
                    ...prev,
                    permission_ids: prev.permission_ids.filter(id => !resourcePermIds.includes(id))
                };
            } else {
                // Select all
                const newIds = [...prev.permission_ids];
                resourcePermIds.forEach(id => {
                    if (!newIds.includes(id)) newIds.push(id);
                });
                return { ...prev, permission_ids: newIds };
            }
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            if (mode === 'create') {
                await roleService.create(formData);
            } else {
                if (!initialData) return;
                await roleService.update(initialData.id, formData);
            }

            if (onSuccess) {
                onSuccess();
            } else {
                navigate('/admin/roles');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'An error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="role-form">
            {error && (
                <div className="form-error">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                </div>
            )}

            <div className="form-section">
                <h3>Role Details</h3>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Role Name</label>
                        <div className="input-icon-wrapper">
                            <Shield size={18} />
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                required
                                placeholder="e.g. Content Manager"
                            />
                        </div>
                    </div>

                    <div className="form-group full-width">
                        <label>Description</label>
                        <div className="input-icon-wrapper">
                            <FileText size={18} />
                            <textarea
                                name="description"
                                value={formData.description}
                                onChange={handleChange}
                                placeholder="Describe the responsibilities of this role..."
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div className="form-section">
                <h3>Permissions</h3>
                <div className="permissions-grid">
                    {Object.entries(groupedPermissions).map(([resource, groupPerms]) => {
                        const allSelected = groupPerms.every(p => formData.permission_ids.includes(p.id));

                        return (
                            <div key={resource} className="permission-group">
                                <h4>
                                    <button
                                        type="button"
                                        className="btn-icon-text"
                                        onClick={() => handleGroupToggle(groupPerms)}
                                        style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 'inherit', fontSize: 'inherit' }}
                                    >
                                        {allSelected ? <CheckSquare size={16} /> : <Square size={16} />}
                                        {resource}
                                    </button>
                                </h4>
                                <div className="permission-list">
                                    {groupPerms.map(perm => (
                                        <label key={perm.id} className="permission-item">
                                            <input
                                                type="checkbox"
                                                checked={formData.permission_ids.includes(perm.id)}
                                                onChange={() => handlePermissionToggle(perm.id)}
                                            />
                                            <div className="permission-info">
                                                <span className="permission-name">{perm.action}</span>
                                                {perm.description && (
                                                    <span className="permission-desc">{perm.description}</span>
                                                )}
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="form-actions">
                <button type="button" onClick={() => navigate(-1)} className="btn btn-ghost">
                    Cancel
                </button>
                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <div className="loading-spinner-small"></div>
                    ) : (
                        <>
                            <Save size={18} />
                            {mode === 'create' ? 'Create Role' : 'Save Changes'}
                        </>
                    )}
                </button>
            </div>
        </form>
    );
}
