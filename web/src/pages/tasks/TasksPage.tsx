/**
 * WorkSynapse Tasks Page
 * =======================
 * Kanban board or list view for task management.
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import {
    CheckSquare,
    Plus,
    Filter,
    Search,
    Calendar,
    User,
    Tag,
    Clock,
    AlertCircle,
    ChevronDown,
    MoreVertical,
    GripVertical,
} from 'lucide-react';
import './Tasks.css';

interface Task {
    id: number;
    title: string;
    description: string;
    status: 'TODO' | 'IN_PROGRESS' | 'IN_REVIEW' | 'DONE';
    priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
    assignee?: string;
    assignee_avatar?: string;
    due_date?: string;
    tags: string[];
    project_name?: string;
}

const statusColumns = [
    { key: 'TODO', label: 'To Do', color: 'var(--color-text-muted)' },
    { key: 'IN_PROGRESS', label: 'In Progress', color: 'var(--color-primary)' },
    { key: 'IN_REVIEW', label: 'In Review', color: 'var(--color-warning)' },
    { key: 'DONE', label: 'Done', color: 'var(--color-success)' },
];

export function TasksPage() {
    const { user } = useAuth();
    const [tasks, setTasks] = useState<Task[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [filterAssignee, setFilterAssignee] = useState<string>('all');

    useEffect(() => {
        loadTasks();
    }, []);

    const loadTasks = async () => {
        // Simulated data
        const mockTasks: Task[] = [
            { id: 1, title: 'Implement JWT Authentication', description: 'Add secure JWT-based auth with refresh tokens', status: 'DONE', priority: 'HIGH', assignee: 'Alex', tags: ['backend', 'security'], project_name: 'WorkSynapse v2.0', due_date: '2024-02-10' },
            { id: 2, title: 'Design Dashboard UI', description: 'Create modern dashboard with stats cards and charts', status: 'IN_REVIEW', priority: 'MEDIUM', assignee: 'Sarah', tags: ['frontend', 'design'], project_name: 'WorkSynapse v2.0', due_date: '2024-02-12' },
            { id: 3, title: 'Add WebSocket Support', description: 'Real-time messaging with WebSocket connections', status: 'IN_PROGRESS', priority: 'HIGH', assignee: 'Alex', tags: ['backend', 'realtime'], project_name: 'WorkSynapse v2.0', due_date: '2024-02-15' },
            { id: 4, title: 'Create API Documentation', description: 'Swagger/OpenAPI docs for all endpoints', status: 'TODO', priority: 'LOW', assignee: 'Mike', tags: ['docs'], project_name: 'API Migration' },
            { id: 5, title: 'Mobile Responsive Layout', description: 'Ensure all pages work on mobile devices', status: 'TODO', priority: 'MEDIUM', assignee: 'Sarah', tags: ['frontend', 'mobile'], project_name: 'Mobile App Redesign' },
            { id: 6, title: 'Setup CI/CD Pipeline', description: 'GitHub Actions for automated testing and deployment', status: 'IN_PROGRESS', priority: 'URGENT', assignee: 'Mike', tags: ['devops'], project_name: 'WorkSynapse v2.0', due_date: '2024-02-08' },
        ];
        setTasks(mockTasks);
        setIsLoading(false);
    };

    const getTasksByStatus = (status: string) => tasks.filter(t => t.status === status);

    const getPriorityBadge = (priority: string) => {
        const config: Record<string, string> = {
            LOW: 'low',
            MEDIUM: 'medium',
            HIGH: 'high',
            URGENT: 'urgent',
        };
        return <span className={`priority-badge ${config[priority]}`}>{priority.toLowerCase()}</span>;
    };

    const isOverdue = (dueDate?: string) => {
        if (!dueDate) return false;
        return new Date(dueDate) < new Date();
    };

    return (
        <div className="tasks-page">
            <header className="page-header">
                <div className="header-content">
                    <h1>
                        <CheckSquare size={28} />
                        Tasks
                    </h1>
                    <p>Manage and track your work</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-secondary">
                        <Filter size={18} />
                        <span>Filter</span>
                    </button>
                    <button className="btn btn-primary">
                        <Plus size={18} />
                        <span>New Task</span>
                    </button>
                </div>
            </header>

            {/* Kanban Board */}
            <div className="kanban-board">
                {statusColumns.map((column) => (
                    <div key={column.key} className="kanban-column">
                        <div className="column-header" style={{ '--column-color': column.color } as React.CSSProperties}>
                            <div className="column-title">
                                <span className="column-dot"></span>
                                <h3>{column.label}</h3>
                                <span className="column-count">{getTasksByStatus(column.key).length}</span>
                            </div>
                            <button className="btn-icon">
                                <Plus size={16} />
                            </button>
                        </div>

                        <div className="column-tasks">
                            {getTasksByStatus(column.key).map((task) => (
                                <div key={task.id} className="task-card" draggable>
                                    <div className="task-drag">
                                        <GripVertical size={14} />
                                    </div>

                                    <div className="task-header">
                                        <span className="task-project">{task.project_name}</span>
                                        <button className="btn-icon small">
                                            <MoreVertical size={14} />
                                        </button>
                                    </div>

                                    <h4 className="task-title">{task.title}</h4>
                                    <p className="task-description">{task.description}</p>

                                    <div className="task-tags">
                                        {task.tags.map((tag) => (
                                            <span key={tag} className="tag">{tag}</span>
                                        ))}
                                    </div>

                                    <div className="task-footer">
                                        <div className="task-meta">
                                            {getPriorityBadge(task.priority)}
                                            {task.due_date && (
                                                <span className={`task-due ${isOverdue(task.due_date) ? 'overdue' : ''}`}>
                                                    <Calendar size={12} />
                                                    {new Date(task.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                                </span>
                                            )}
                                        </div>
                                        {task.assignee && (
                                            <div className="task-assignee" title={task.assignee}>
                                                {task.assignee[0]}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default TasksPage;
