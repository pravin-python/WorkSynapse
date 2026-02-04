/**
 * WorkSynapse Projects Page
 * =========================
 * Project listing with filters, search, and CRUD operations.
 */
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/apiClient';
import {
    FolderKanban,
    Plus,
    Search,
    Filter,
    Grid3X3,
    List,
    MoreVertical,
    Users,
    Calendar,
    CheckCircle2,
    Clock,
    AlertCircle,
    ChevronRight,
    Trash2,
    Edit,
    Archive,
} from 'lucide-react';
import './Projects.css';

interface Project {
    id: number;
    name: string;
    description: string;
    status: 'ACTIVE' | 'COMPLETED' | 'ARCHIVED' | 'ON_HOLD';
    visibility: 'PRIVATE' | 'PUBLIC' | 'TEAM';
    created_at: string;
    updated_at: string;
    owner_id: number;
    owner_name: string;
    member_count: number;
    task_count: number;
    completed_task_count: number;
    color?: string;
}

export function ProjectsPage() {
    const navigate = useNavigate();
    const { user, hasPermission } = useAuth();
    const [projects, setProjects] = useState<Project[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [showFilters, setShowFilters] = useState(false);

    useEffect(() => {
        loadProjects();
    }, [statusFilter]);

    const loadProjects = async () => {
        try {
            // Simulated data - replace with actual API call
            const mockProjects: Project[] = [
                {
                    id: 1,
                    name: 'WorkSynapse v2.0',
                    description: 'Next-generation AI-powered project management platform',
                    status: 'ACTIVE',
                    visibility: 'TEAM',
                    created_at: '2024-01-15T10:00:00Z',
                    updated_at: '2024-02-10T15:30:00Z',
                    owner_id: 1,
                    owner_name: 'Alex Johnson',
                    member_count: 8,
                    task_count: 45,
                    completed_task_count: 32,
                    color: '#8b5cf6',
                },
                {
                    id: 2,
                    name: 'Mobile App Redesign',
                    description: 'Complete redesign of mobile application with new UI/UX',
                    status: 'ACTIVE',
                    visibility: 'PRIVATE',
                    created_at: '2024-01-20T09:00:00Z',
                    updated_at: '2024-02-09T11:20:00Z',
                    owner_id: 2,
                    owner_name: 'Sarah Chen',
                    member_count: 5,
                    task_count: 28,
                    completed_task_count: 18,
                    color: '#06b6d4',
                },
                {
                    id: 3,
                    name: 'API Migration',
                    description: 'Migrate legacy APIs to GraphQL with improved performance',
                    status: 'ON_HOLD',
                    visibility: 'TEAM',
                    created_at: '2024-02-01T14:00:00Z',
                    updated_at: '2024-02-08T16:45:00Z',
                    owner_id: 1,
                    owner_name: 'Alex Johnson',
                    member_count: 3,
                    task_count: 15,
                    completed_task_count: 5,
                    color: '#f59e0b',
                },
                {
                    id: 4,
                    name: 'Security Audit 2024',
                    description: 'Annual security audit and penetration testing',
                    status: 'COMPLETED',
                    visibility: 'PRIVATE',
                    created_at: '2023-12-01T10:00:00Z',
                    updated_at: '2024-01-30T12:00:00Z',
                    owner_id: 3,
                    owner_name: 'Mike Rivera',
                    member_count: 4,
                    task_count: 22,
                    completed_task_count: 22,
                    color: '#10b981',
                },
            ];

            setProjects(mockProjects);
        } catch (error) {
            console.error('Failed to load projects:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const filteredProjects = projects.filter(project => {
        const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            project.description.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === 'all' || project.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const getStatusBadge = (status: string) => {
        const statusConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
            ACTIVE: { icon: <Clock size={12} />, color: 'primary', label: 'Active' },
            COMPLETED: { icon: <CheckCircle2 size={12} />, color: 'success', label: 'Completed' },
            ON_HOLD: { icon: <AlertCircle size={12} />, color: 'warning', label: 'On Hold' },
            ARCHIVED: { icon: <Archive size={12} />, color: 'muted', label: 'Archived' },
        };
        const config = statusConfig[status] || statusConfig.ACTIVE;
        return (
            <span className={`status-badge ${config.color}`}>
                {config.icon}
                {config.label}
            </span>
        );
    };

    const getProgress = (completed: number, total: number) => {
        if (total === 0) return 0;
        return Math.round((completed / total) * 100);
    };

    return (
        <div className="projects-page">
            {/* Header */}
            <header className="page-header">
                <div className="header-content">
                    <h1>
                        <FolderKanban size={28} />
                        Projects
                    </h1>
                    <p>{projects.length} projects in your workspace</p>
                </div>
                <div className="header-actions">
                    <Link to="/projects/new" className="btn btn-primary">
                        <Plus size={18} />
                        <span>New Project</span>
                    </Link>
                </div>
            </header>

            {/* Toolbar */}
            <div className="page-toolbar">
                <div className="search-wrapper">
                    <Search size={18} />
                    <input
                        type="text"
                        placeholder="Search projects..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="search-input"
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

            {/* Filters */}
            {showFilters && (
                <div className="filters-panel">
                    <div className="filter-group">
                        <label>Status</label>
                        <div className="filter-buttons">
                            {['all', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'ARCHIVED'].map((status) => (
                                <button
                                    key={status}
                                    className={`filter-btn ${statusFilter === status ? 'active' : ''}`}
                                    onClick={() => setStatusFilter(status)}
                                >
                                    {status === 'all' ? 'All' : status.replace('_', ' ')}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Projects Grid/List */}
            {isLoading ? (
                <div className="loading-state">
                    <div className="loading-spinner-large"></div>
                    <p>Loading projects...</p>
                </div>
            ) : filteredProjects.length === 0 ? (
                <div className="empty-state">
                    <FolderKanban size={48} />
                    <h3>No projects found</h3>
                    <p>{searchQuery ? 'Try adjusting your search or filters' : 'Create your first project to get started'}</p>
                    <Link to="/projects/new" className="btn btn-primary">
                        <Plus size={18} />
                        Create Project
                    </Link>
                </div>
            ) : (
                <div className={`projects-${viewMode}`}>
                    {filteredProjects.map((project) => (
                        <div key={project.id} className="project-card" style={{ '--project-color': project.color } as React.CSSProperties}>
                            <div className="project-header">
                                <div
                                    className="project-color"
                                    style={{ background: project.color }}
                                ></div>
                                <div className="project-meta">
                                    {getStatusBadge(project.status)}
                                    <button className="btn-icon" aria-label="More options">
                                        <MoreVertical size={16} />
                                    </button>
                                </div>
                            </div>

                            <Link to={`/projects/${project.id}`} className="project-content">
                                <h3>{project.name}</h3>
                                <p>{project.description}</p>
                            </Link>

                            <div className="project-progress">
                                <div className="progress-header">
                                    <span>Progress</span>
                                    <span>{getProgress(project.completed_task_count, project.task_count)}%</span>
                                </div>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{
                                            width: `${getProgress(project.completed_task_count, project.task_count)}%`,
                                            background: project.color,
                                        }}
                                    ></div>
                                </div>
                                <div className="progress-tasks">
                                    {project.completed_task_count} of {project.task_count} tasks
                                </div>
                            </div>

                            <div className="project-footer">
                                <div className="project-members">
                                    <Users size={14} />
                                    <span>{project.member_count} members</span>
                                </div>
                                <div className="project-date">
                                    <Calendar size={14} />
                                    <span>{new Date(project.updated_at).toLocaleDateString()}</span>
                                </div>
                            </div>

                            <Link to={`/projects/${project.id}`} className="project-link">
                                Open Project <ChevronRight size={14} />
                            </Link>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default ProjectsPage;
