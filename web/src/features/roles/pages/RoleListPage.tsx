import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit2, Trash2, Shield, Lock, Users, Filter, Grid3X3, List, MoreVertical } from 'lucide-react';
import { Pagination } from '../../../components/ui/Pagination';
import { ConfirmModal } from '../../../components/ui/ConfirmModal';
import { SearchInput } from '../../../components/ui/SearchInput';
import { Role } from '../types';
import { roleService } from '../services/roleService';
import '../styles.css';

export function RoleListPage() {
    const navigate = useNavigate();
    const [roles, setRoles] = useState<Role[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [isSystemFilter, setIsSystemFilter] = useState<'all' | 'system' | 'custom'>('all');
    const [showFilters, setShowFilters] = useState(false);
    const pageSize = 9;

    // Modal state
    const [roleToDelete, setRoleToDelete] = useState<Role | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);

    useEffect(() => {
        loadRoles();
    }, [page, searchQuery, isSystemFilter]);

    const loadRoles = async () => {
        setIsLoading(true);
        try {
            const data = await roleService.getAll({
                skip: (page - 1) * pageSize,
                limit: pageSize,
                search: searchQuery,
                is_system: isSystemFilter === 'all' ? undefined : (isSystemFilter === 'system')
            });
            setRoles(data.items);
            setTotal(data.total);
        } catch (error) {
            console.error('Failed to load roles', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteClick = (role: Role) => {
        setRoleToDelete(role);
    };

    const handleConfirmDelete = async () => {
        if (!roleToDelete) return;

        setIsDeleting(true);
        try {
            await roleService.delete(roleToDelete.id);
            setRoleToDelete(null);
            // Refresh list
            loadRoles();
        } catch (error) {
            console.error('Failed to delete role', error);
            alert('Failed to delete role. Ensure it is not assigned to any critical system users.');
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <div className="roles-page fade-in">
            {/* Header */}
            <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="header-content">
                    <h1>
                        <Shield size={28} />
                        Roles & Permissions
                    </h1>
                    <p>Manage system roles, permissions, and user assignments.</p>
                </div>
                <div className="header-actions">
                    <button
                        className="btn btn-primary"
                        onClick={() => navigate('/admin/roles/new')}
                    >
                        <Plus size={18} />
                        Create New Role
                    </button>
                </div>
            </header>

            {/* Toolbar */}
            <div className="page-toolbar">
                <div style={{ flex: 1, maxWidth: '400px' }}>
                    <SearchInput
                        placeholder="Search roles..."
                        value={searchQuery}
                        onChange={setSearchQuery}
                        className="w-full"
                    />
                </div>

                <div className="toolbar-actions">
                    <button
                        className={`btn btn-ghost ${showFilters ? 'active' : ''}`}
                        onClick={() => setShowFilters(!showFilters)}
                    >
                        <Filter size={18} />
                        <span>Filters</span>
                    </button>

                    <div className="view-toggle">
                        <button
                            className={`toggle-btn ${viewMode === 'grid' ? 'active' : ''}`}
                            onClick={() => setViewMode('grid')}
                            aria-label="Grid view"
                        >
                            <Grid3X3 size={18} />
                        </button>
                        <button
                            className={`toggle-btn ${viewMode === 'list' ? 'active' : ''}`}
                            onClick={() => setViewMode('list')}
                            aria-label="List view"
                        >
                            <List size={18} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Filters Panel */}
            {showFilters && (
                <div className="filters-panel">
                    <div className="filter-group">
                        <label>Role Type</label>
                        <div className="filter-buttons">
                            <button
                                className={`filter-btn ${isSystemFilter === 'all' ? 'active' : ''}`}
                                onClick={() => setIsSystemFilter('all')}
                            >
                                All Roles
                            </button>
                            <button
                                className={`filter-btn ${isSystemFilter === 'system' ? 'active' : ''}`}
                                onClick={() => setIsSystemFilter('system')}
                            >
                                System Only
                            </button>
                            <button
                                className={`filter-btn ${isSystemFilter === 'custom' ? 'active' : ''}`}
                                onClick={() => setIsSystemFilter('custom')}
                            >
                                Custom Only
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Content */}
            <div style={{ marginTop: '24px' }}>
                {isLoading ? (
                    <div className="flex center-center h-48">
                        <div className="loading-spinner"></div>
                    </div>
                ) : roles.length === 0 ? (
                    <div className="empty-state">
                        <Shield size={48} />
                        <h3>No roles found</h3>
                        <p>Try adjusting your search or create a new role.</p>
                    </div>
                ) : (
                    <>
                        {viewMode === 'grid' ? (
                            <div className="role-grid">
                                {roles.map(role => (
                                    <div key={role.id} className="role-card" onClick={() => navigate(`/admin/roles/${role.id}/edit`)}>
                                        <div className="role-card-header">
                                            <div className="role-icon-wrapper">
                                                <Shield size={24} />
                                            </div>
                                            <div className="role-actions">
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); navigate(`/admin/roles/${role.id}/edit`); }}
                                                    className="btn-icon"
                                                    title="Edit Role"
                                                >
                                                    <Edit2 size={16} />
                                                </button>
                                                {!role.is_system && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleDeleteClick(role); }}
                                                        className="btn-icon text-error"
                                                        title="Delete Role"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                        <div className="role-card-content">
                                            <h3>
                                                {role.name}
                                                {role.is_system && <span className="system-badge">System</span>}
                                            </h3>
                                            <p>{role.description || "No description provided."}</p>
                                        </div>
                                        <div className="role-card-footer">
                                            <div className="meta-item permission-count">
                                                <Lock size={14} />
                                                <span>{role.permissions.length} Permissions</span>
                                            </div>
                                            <div className="meta-item user-count">
                                                <Users size={14} />
                                                <span>{role.users_count || 0} Users</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="roles-list-view">
                                {/* Simple List View using similar card styles or a table */}
                                <div className="role-grid" style={{ gridTemplateColumns: '1fr' }}>
                                    {roles.map(role => (
                                        <div key={role.id} className="role-card" style={{ flexDirection: 'row', alignItems: 'center' }} onClick={() => navigate(`/admin/roles/${role.id}/edit`)}>
                                            <div className="role-icon-wrapper" style={{ width: '40px', height: '40px' }}>
                                                <Shield size={20} />
                                            </div>
                                            <div className="role-card-content" style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '20px' }}>
                                                <div style={{ flex: 1 }}>
                                                    <h3>
                                                        {role.name}
                                                        {role.is_system && <span className="system-badge">System</span>}
                                                    </h3>
                                                    <p className="line-clamp-1">{role.description || "No description provided."}</p>
                                                </div>
                                                <div style={{ display: 'flex', gap: '16px' }}>
                                                    <div className="meta-item permission-count">
                                                        <Lock size={14} />
                                                        <span>{role.permissions.length}</span>
                                                    </div>
                                                    <div className="meta-item user-count">
                                                        <Users size={14} />
                                                        <span>{role.users_count || 0}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="role-actions" style={{ opacity: 1, transform: 'none' }}>
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); navigate(`/admin/roles/${role.id}/edit`); }}
                                                    className="btn-icon"
                                                >
                                                    <Edit2 size={16} />
                                                </button>
                                                {!role.is_system && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleDeleteClick(role); }}
                                                        className="btn-icon text-error"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                )}

                {!isLoading && total > 0 && (
                    <div style={{ marginTop: '20px' }}>
                        <Pagination
                            currentPage={page}
                            totalItems={total}
                            pageSize={pageSize}
                            onPageChange={setPage}
                        />
                    </div>
                )}
            </div>

            <ConfirmModal
                isOpen={!!roleToDelete}
                onClose={() => setRoleToDelete(null)}
                onConfirm={handleConfirmDelete}
                title="Delete Role"
                message={`Are you sure you want to delete the "${roleToDelete?.name}" role? This action cannot be undone.`}
                confirmText="Delete Role"
                isDestructive={true}
                isLoading={isDeleting}
            />
        </div>
    );
}
