import { apiClient } from '../../services/apiClient';
import { User, UserCreateData } from '../types';

export const userService = {
    getAll: async (params?: { skip?: number; limit?: number; search?: string }) => {
        const response = await apiClient.get<User[]>('/users', { params });
        return response.data;
    },

    getById: async (id: number) => {
        const response = await apiClient.get<User>(`/users/${id}`);
        return response.data;
    },

    create: async (data: UserCreateData) => {
        const response = await apiClient.post<User>('/users', data);
        return response.data;
    },

    update: async (id: number, data: Partial<User>) => {
        const response = await apiClient.put<User>(`/users/${id}`, data);
        return response.data;
    },

    delete: async (id: number) => {
        const response = await apiClient.delete<User>(`/users/${id}`);
        return response.data;
    }
};
