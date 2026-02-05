import { apiClient } from '../../../services/apiClient';
import { Role, RoleFormData, RoleListResponse, Permission } from '../types';

export const roleService = {
    getAll: async (params?: { skip?: number; limit?: number; search?: string; is_system?: boolean }) => {
        const response = await apiClient.get<RoleListResponse>('/roles', { params });
        return response.data;
    },

    getPermissions: async () => {
        const response = await apiClient.get<Permission[]>('/roles/permissions');
        return response.data;
    },

    getById: async (id: number) => {
        const response = await apiClient.get<Role>(`/roles/${id}`);
        return response.data;
    },

    create: async (data: RoleFormData) => {
        const response = await apiClient.post<Role>('/roles', data);
        return response.data;
    },

    update: async (id: number, data: RoleFormData) => {
        const response = await apiClient.put<Role>(`/roles/${id}`, data);
        return response.data;
    },

    delete: async (id: number) => {
        const response = await apiClient.delete<Role>(`/roles/${id}`);
        return response.data;
    }
};
