/**
 * WorkSynapse Dashboard Page
 * ==========================
 * Role-based dashboard with stats, charts, and quick actions.
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/apiClient';
import {
    FolderKanban,
    CheckSquare,
    Clock,
    Users,
    TrendingUp,
    TrendingDown,
    ArrowRight,
    Plus,
    Calendar,
    Bot,
    BarChart3,
    Activity,
    Zap,
} from 'lucide-react';
import './Dashboard.css';

interface DashboardStats {
    active_projects: number;
    total_tasks: number;
    completed_tasks: number;
    hours_tracked: number;
    team_members?: number;
    active_sprints?: number;
    pending_tasks: number;
    overdue_tasks: number;
}

interface RecentActivity {
    id: number;
    type: string;
    message: string;
    timestamp: string;
    user_name?: string;
}

export function DashboardPage() {
    const { user, isAdmin, hasRole } = useAuth();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [activities, setActivities] = useState<RecentActivity[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const greeting = getGreeting();

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            // Simulated data - replace with actual API calls
            setStats({
                active_projects: 8,
                total_tasks: 156,
                completed_tasks: 124,
                hours_tracked: 234.5,
                team_members: isAdmin() ? 24 : undefined,
                active_sprints: hasRole('MANAGER') ? 3 : undefined,
                pending_tasks: 32,
                overdue_tasks: 4,
            });

            setActivities([
                { id: 1, type: 'task_complete', message: 'Completed task "API Integration"', timestamp: '10 min ago', user_name: 'You' },
                { id: 2, type: 'project_update', message: 'Updated project "WorkSynapse v2.0"', timestamp: '25 min ago', user_name: 'Sarah' },
                { id: 3, type: 'comment', message: 'Commented on "Database Migration"', timestamp: '1 hour ago', user_name: 'Mike' },
                { id: 4, type: 'task_assign', message: 'Assigned new task to you', timestamp: '2 hours ago', user_name: 'Alex' },
                { id: 5, type: 'sprint_start', message: 'Sprint 12 has started', timestamp: '3 hours ago', user_name: 'System' },
            ]);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const completionRate = stats
        ? Math.round((stats.completed_tasks / stats.total_tasks) * 100)
        : 0;

    return (
        <div className="dashboard-page">
            {/* Header */}
            <header className="page-header">
                <div className="header-content">
                    <h1>{greeting}, {user?.full_name?.split(' ')[0] || 'there'}!</h1>
                    <p>Here's what's happening in your workspace today.</p>
                </div>
                <div className="header-actions">
                    <Link to="/projects/new" className="btn btn-primary">
                        <Plus size={18} />
                        <span>New Project</span>
                    </Link>
                </div>
            </header>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card gradient-primary">
                    <div className="stat-icon">
                        <FolderKanban size={24} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-value">{stats?.active_projects || 0}</span>
                        <span className="stat-label">Active Projects</span>
                    </div>
                    <div className="stat-trend up">
                        <TrendingUp size={14} />
                        <span>+2 this week</span>
                    </div>
                </div>

                <div className="stat-card gradient-secondary">
                    <div className="stat-icon">
                        <CheckSquare size={24} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-value">{stats?.pending_tasks || 0}</span>
                        <span className="stat-label">Pending Tasks</span>
                    </div>
                    <div className="stat-trend">
                        <span>{stats?.overdue_tasks} overdue</span>
                    </div>
                </div>

                <div className="stat-card gradient-accent">
                    <div className="stat-icon">
                        <Clock size={24} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-value">{stats?.hours_tracked?.toFixed(1) || 0}h</span>
                        <span className="stat-label">Hours Tracked</span>
                    </div>
                    <div className="stat-trend up">
                        <TrendingUp size={14} />
                        <span>+12% vs last week</span>
                    </div>
                </div>

                <div className="stat-card gradient-success">
                    <div className="stat-icon">
                        <Zap size={24} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-value">{completionRate}%</span>
                        <span className="stat-label">Completion Rate</span>
                    </div>
                    <div className="stat-trend up">
                        <TrendingUp size={14} />
                        <span>+5% this month</span>
                    </div>
                </div>

                {isAdmin() && (
                    <div className="stat-card gradient-info">
                        <div className="stat-icon">
                            <Users size={24} />
                        </div>
                        <div className="stat-content">
                            <span className="stat-value">{stats?.team_members || 0}</span>
                            <span className="stat-label">Team Members</span>
                        </div>
                        <div className="stat-trend">
                            <span>3 online now</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Main Content Grid */}
            <div className="dashboard-grid">
                {/* Progress Overview */}
                <div className="dashboard-card progress-card">
                    <div className="card-header">
                        <h2>Today's Progress</h2>
                        <Link to="/tasks" className="card-link">
                            View all <ArrowRight size={14} />
                        </Link>
                    </div>
                    <div className="progress-content">
                        <div className="progress-ring">
                            <svg viewBox="0 0 100 100">
                                <circle
                                    cx="50"
                                    cy="50"
                                    r="40"
                                    fill="none"
                                    stroke="hsl(var(--color-border))"
                                    strokeWidth="8"
                                />
                                <circle
                                    cx="50"
                                    cy="50"
                                    r="40"
                                    fill="none"
                                    stroke="url(#progressGradient)"
                                    strokeWidth="8"
                                    strokeLinecap="round"
                                    strokeDasharray={`${completionRate * 2.51} 251`}
                                    transform="rotate(-90 50 50)"
                                />
                                <defs>
                                    <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stopColor="hsl(var(--color-primary))" />
                                        <stop offset="100%" stopColor="hsl(var(--color-secondary))" />
                                    </linearGradient>
                                </defs>
                            </svg>
                            <div className="progress-center">
                                <span className="progress-value">{completionRate}%</span>
                                <span className="progress-label">Complete</span>
                            </div>
                        </div>
                        <div className="progress-stats">
                            <div className="progress-stat">
                                <span className="dot success"></span>
                                <span className="label">Completed</span>
                                <span className="value">{stats?.completed_tasks || 0}</span>
                            </div>
                            <div className="progress-stat">
                                <span className="dot warning"></span>
                                <span className="label">In Progress</span>
                                <span className="value">{stats?.pending_tasks || 0}</span>
                            </div>
                            <div className="progress-stat">
                                <span className="dot error"></span>
                                <span className="label">Overdue</span>
                                <span className="value">{stats?.overdue_tasks || 0}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="dashboard-card activity-card">
                    <div className="card-header">
                        <h2>Recent Activity</h2>
                        <Link to="/tracking" className="card-link">
                            View all <ArrowRight size={14} />
                        </Link>
                    </div>
                    <div className="activity-list">
                        {activities.map((activity) => (
                            <div key={activity.id} className="activity-item">
                                <div className={`activity-icon ${activity.type}`}>
                                    <Activity size={14} />
                                </div>
                                <div className="activity-content">
                                    <span className="activity-user">{activity.user_name}</span>
                                    <span className="activity-message">{activity.message}</span>
                                </div>
                                <span className="activity-time">{activity.timestamp}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="dashboard-card quick-actions-card">
                    <div className="card-header">
                        <h2>Quick Actions</h2>
                    </div>
                    <div className="quick-actions">
                        <Link to="/tasks/new" className="quick-action">
                            <div className="action-icon">
                                <Plus size={20} />
                            </div>
                            <span>New Task</span>
                        </Link>
                        <Link to="/notes/new" className="quick-action">
                            <div className="action-icon">
                                <Plus size={20} />
                            </div>
                            <span>New Note</span>
                        </Link>
                        <Link to="/tracking/start" className="quick-action">
                            <div className="action-icon">
                                <Clock size={20} />
                            </div>
                            <span>Start Timer</span>
                        </Link>
                        <Link to="/chat" className="quick-action">
                            <div className="action-icon">
                                <Zap size={20} />
                            </div>
                            <span>Team Chat</span>
                        </Link>
                    </div>
                </div>

                {/* AI Insights (for users with AI access) */}
                {(isAdmin() || hasRole('AI_ENGINEER')) && (
                    <div className="dashboard-card ai-card">
                        <div className="card-header">
                            <h2>
                                <Bot size={20} />
                                AI Insights
                            </h2>
                            <Link to="/ai/agents" className="card-link">
                                Configure <ArrowRight size={14} />
                            </Link>
                        </div>
                        <div className="ai-insights">
                            <div className="insight-item">
                                <div className="insight-icon">💡</div>
                                <div className="insight-content">
                                    <strong>Productivity tip</strong>
                                    <span>Your most productive hours are 10am-12pm. Schedule important tasks then.</span>
                                </div>
                            </div>
                            <div className="insight-item">
                                <div className="insight-icon">⚠️</div>
                                <div className="insight-content">
                                    <strong>Task alert</strong>
                                    <span>4 tasks are approaching deadline. Consider redistributing workload.</span>
                                </div>
                            </div>
                            <div className="insight-item">
                                <div className="insight-icon">🎯</div>
                                <div className="insight-content">
                                    <strong>Sprint health</strong>
                                    <span>Current sprint is 85% on track. Estimated completion: 2 days ahead.</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Upcoming */}
                <div className="dashboard-card upcoming-card">
                    <div className="card-header">
                        <h2>
                            <Calendar size={20} />
                            Upcoming
                        </h2>
                    </div>
                    <div className="upcoming-list">
                        <div className="upcoming-item">
                            <div className="upcoming-date">
                                <span className="day">15</span>
                                <span className="month">Feb</span>
                            </div>
                            <div className="upcoming-content">
                                <strong>Sprint 12 Review</strong>
                                <span>Team meeting at 2:00 PM</span>
                            </div>
                        </div>
                        <div className="upcoming-item">
                            <div className="upcoming-date">
                                <span className="day">18</span>
                                <span className="month">Feb</span>
                            </div>
                            <div className="upcoming-content">
                                <strong>API v2.0 Deadline</strong>
                                <span>Feature freeze</span>
                            </div>
                        </div>
                        <div className="upcoming-item">
                            <div className="upcoming-date">
                                <span className="day">22</span>
                                <span className="month">Feb</span>
                            </div>
                            <div className="upcoming-content">
                                <strong>Client Demo</strong>
                                <span>Product showcase</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
}

export default DashboardPage;
