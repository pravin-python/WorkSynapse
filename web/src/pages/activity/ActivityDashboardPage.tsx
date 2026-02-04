import React, { useEffect, useState } from 'react';
import { userActivityService, UserActivityData } from '../../services/userActivityService';
import {
    Activity,
    Briefcase,
    Bot,
    CheckSquare,
    MessageSquare,
    FileText,
    User,
    Clock
} from 'lucide-react';

const ActivityDashboardPage: React.FC = () => {
    const [data, setData] = useState<UserActivityData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await userActivityService.getUserActivity();
                setData(response);
            } catch (err) {
                console.error("Failed to fetch activity:", err);
                setError("Failed to load your activity data. Please try again.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center p-10">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 text-center">
                <div className="text-red-500 mb-4">{error}</div>
                <button
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!data) return null;

    // Combine recent activities for timeline
    const recentActivities = [
        ...(data.activity_logs || []).map(l => ({ ...l, type: 'Log', date: new Date(l.timestamp) })),
        ...(data.projects || []).map(p => ({ action: 'Created Project', resource_name: p.name, created_at: p.created_at, type: 'Project' })),
        ...(data.tasks || []).map(t => ({ action: 'Created Task', resource_name: t.title, created_at: t.created_at, type: 'Task' })),
        ...(data.agents || []).map(a => ({ action: 'Created Agent', resource_name: a.name, created_at: a.created_at, type: 'Agent' })),
    ].sort((a, b) => {
        const dateA = new Date(a.created_at || a.timestamp || a.date).getTime();
        const dateB = new Date(b.created_at || b.timestamp || b.date).getTime();
        return dateB - dateA;
    }).slice(0, 10);

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Activity className="h-6 w-6 text-primary-500" />
                        My Activity
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Track your contributions across WorkSynapse
                    </p>
                </div>
                <div className="text-sm text-gray-500">
                    Last updated: {new Date().toLocaleTimeString()}
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Projects"
                    count={data.projects.length}
                    icon={<Briefcase className="h-6 w-6 text-blue-500" />}
                    color="bg-blue-500/10"
                />
                <StatCard
                    title="Active Agents"
                    count={data.agents.length}
                    icon={<Bot className="h-6 w-6 text-emerald-500" />}
                    color="bg-emerald-500/10"
                />
                <StatCard
                    title="Tasks Created"
                    count={data.tasks.length}
                    icon={<CheckSquare className="h-6 w-6 text-purple-500" />}
                    color="bg-purple-500/10"
                />
                <StatCard
                    title="Agent Sessions"
                    count={data.sessions.length}
                    icon={<MessageSquare className="h-6 w-6 text-orange-500" />}
                    color="bg-orange-500/10"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Recent Activity Timeline */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
                            <h3 className="font-semibold text-gray-900 dark:text-white">Recent Activity Log</h3>
                        </div>
                        <div className="divide-y divide-gray-100 dark:divide-gray-700">
                            {recentActivities.length > 0 ? (
                                recentActivities.map((item, idx) => (
                                    <div key={idx} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                        <div className="flex items-start justify-between">
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium text-gray-900 dark:text-white">
                                                        {item.resource_name || item.description || 'Unknown Item'}
                                                    </span>
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${getTypeColor(item.type)}`}>
                                                        {item.type || 'Event'}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                                    {item.action || item.description || 'Action performed'}
                                                </p>
                                            </div>
                                            <div className="text-xs text-gray-400 flex items-center gap-1">
                                                <Clock className="w-3 h-3" />
                                                {new Date(item.created_at || item.timestamp || item.date).toLocaleDateString()}
                                            </div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="p-8 text-center text-gray-500">No recent activity found.</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* User Profile Card */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="h-12 w-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400">
                                <User className="h-6 w-6" />
                            </div>
                            <div>
                                <h3 className="font-bold text-gray-900 dark:text-white">My Profile</h3>
                                <p className="text-sm text-gray-500">Contributor</p>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-500">Total Work Logged</span>
                                <span className="font-medium text-gray-900 dark:text-white">{data.work_logs.length} sessions</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-500">Notes Created</span>
                                <span className="font-medium text-gray-900 dark:text-white">{data.notes.length}</span>
                            </div>
                        </div>
                    </div>

                    {/* Quick List: Agents */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                            <h3 className="font-semibold text-gray-900 dark:text-white">My Agents</h3>
                        </div>
                        <div className="divide-y divide-gray-100 dark:divide-gray-700">
                            {data.agents.slice(0, 5).map(agent => (
                                <div key={agent.id} className="px-6 py-3 flex justify-between items-center group hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                    <div className="flex items-center gap-3">
                                        <Bot className="h-4 w-4 text-gray-400 group-hover:text-primary-500" />
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{agent.name}</span>
                                    </div>
                                    <span className="text-xs text-gray-400">{agent.model_name || 'Standard'}</span>
                                </div>
                            ))}
                            {data.agents.length === 0 && (
                                <div className="p-4 text-center text-sm text-gray-500">No agents yet</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Helper Components
const StatCard = ({ title, count, icon, color }: any) => (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 hover:border-primary-500/30 transition-all">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-lg ${color}`}>
                {icon}
            </div>
            <span className="text-xs font-medium text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                Total
            </span>
        </div>
        <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{count}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
    </div>
);

const getTypeColor = (type: string) => {
    switch (type) {
        case 'Project': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
        case 'Agent': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300';
        case 'Task': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300';
        default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
};

export default ActivityDashboardPage;
