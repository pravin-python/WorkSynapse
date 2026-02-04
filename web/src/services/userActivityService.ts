import { api } from './apiClient';

export interface UserActivityData {
    agents: any[];
    projects: any[];
    tasks: any[];
    notes: any[];
    sessions: any[];
    work_logs: any[];
    activity_logs: any[];
}

export const userActivityService = {
    /**
     * Get all activity and entities created by the current user
     */
    getUserActivity: async (): Promise<UserActivityData> => {
        return await api.get<UserActivityData>('/user/activity/');
    },

    /**
     * Get user activity logs
     */
    getActivityLogs: async (limit: number = 50, skip: number = 0) => {
        return await api.get('/user/activity/logs', { params: { limit, skip } });
    }
};
