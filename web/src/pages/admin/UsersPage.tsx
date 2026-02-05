/**
 * WorkSynapse Admin Users Page
 */
import React, { useState, useEffect } from 'react';
import { Users, Plus, Search, Eye, Edit, Trash2 } from 'lucide-react';
import { FilterBar } from '../../components/ui/FilterBar';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmModal } from '../../components/ui/ConfirmModal';
import { UserCreateModal } from '../../features/users/components/UserCreateModal';
import { userService } from '../../features/users/services/userService';
import { User } from '../../features/users/types';
import './Admin.css';

export function UsersPage() {
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(1);

    // Modals
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [userToDelete, setUserToDelete] = useState<User | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);

    useEffect(() => {
        loadUsers();
    }, [page, searchQuery]);

    const loadUsers = async () => {
        setIsLoading(true);
        try {
            // Assuming getAll supports pagination params like roles
            // Currently userService.getAll mock implementation might need update to support params in backend or frontend service
            // Backend endpoint supports skip/limit.
            // But let's just fetch all for now or paginated if needed.
            // For now, fetching list.
            const data = await userService.getAll({
                skip: (page - 1) * 10,
                limit: 10,
                search: searchQuery
            });
            setUsers(data);
        } catch (error) {
            console.error('Failed to load users', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!userToDelete) return;
        setIsDeleting(true);
        try {
            await userService.delete(userToDelete.id);
            setUserToDelete(null);
            loadUsers();
        } catch (error) {
            console.error("Failed to delete user", error);
            alert("Failed to delete user.");
        } finally {
            setIsDeleting(false);
        }
    };

    const getStatusBadge = (user: User) => {
        const isActive = user.is_active;
        return (
            <span className={`status-badge ${isActive ? 'success' : 'muted'}`}>
                {isActive ? 'active' : 'inactive'}
            </span>
        );
    };

    return (
        <div className="admin-page fade-in">
            <header className="page-header">
                <div className="header-content">
                    <h1><Users size={28} />User Management</h1>
                    <p>Manage users and their access</p>
                </div>
                <div className="header-actions">
                    <button
                        className="btn btn-primary"
                        onClick={() => setIsCreateModalOpen(true)}
                    >
                        <Plus size={18} />
                        Add User
                    </button>
                </div>
            </header>

            <FilterBar
                onSearch={setSearchQuery}
                searchPlaceholder="Search users by name or email..."
            />

            <div className="data-table" style={{ marginTop: '24px' }}>
                {isLoading ? (
                    <div className="flex center-center h-48">
                        <div className="loading-spinner"></div>
                    </div>
                ) : (
                    <table>
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Roles</th>
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
                                            <div className="user-avatar-sm">
                                                {user.full_name ? user.full_name[0].toUpperCase() : '?'}
                                            </div>
                                            <div>
                                                <span className="user-name">{user.full_name}</span>
                                                <span className="user-email">{user.email}</span>
                                                {user.is_superuser && <span className="system-badge ml-2" style={{ fontSize: '0.65rem' }}>Super Admin</span>}
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <div className="flex gap-1 flex-wrap">
                                            {user.roles?.map(role => (
                                                <span key={role} className="role-tag">{role}</span>
                                            ))}
                                            {user.roles?.length === 0 && <span className="text-muted text-sm">-</span>}
                                        </div>
                                    </td>
                                    <td>{getStatusBadge(user)}</td>
                                    <td>{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                                    <td>
                                        <div className="action-buttons">
                                            <button className="btn-icon" title="Edit"><Edit size={16} /></button>
                                            <button
                                                className="btn-icon danger"
                                                title="Delete"
                                                onClick={() => setUserToDelete(user)}
                                                disabled={user.is_superuser} // Prevent deleting superusers easily
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {users.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="text-center py-8 text-muted">No users found.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Pagination could be added here if backend supports total count return in list response */}

            <UserCreateModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSuccess={() => {
                    loadUsers();
                }}
            />

            <ConfirmModal
                isOpen={!!userToDelete}
                onClose={() => setUserToDelete(null)}
                onConfirm={handleDelete}
                title="Delete User"
                message={`Are you sure you want to delete user "${userToDelete?.full_name}"? This action cannot be undone.`}
                confirmText="Delete User"
                isDestructive={true}
                isLoading={isDeleting}
            />
        </div>
    );
}

export default UsersPage;
