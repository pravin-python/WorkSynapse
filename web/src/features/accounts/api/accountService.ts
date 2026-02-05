import { api } from '../../../services/apiClient';
import {
    AccountListResponse,
    CreateStaffRequest,
    CreateClientRequest,
    UpdateStaffRequest,
    UpdateClientRequest,
    UserAccount,
    AccountType,
    ProjectAssignmentRequest
} from '../types';

export const accountService = {
    listAccounts: async (
        page: number = 1,
        pageSize: number = 20,
        accountType?: AccountType,
        search?: string,
        isActive?: boolean
    ): Promise<AccountListResponse> => {
        const params: any = { page, page_size: pageSize };
        if (accountType) params.account_type = accountType;
        if (search) params.search = search;
        if (isActive !== undefined) params.is_active = isActive;

        return api.get<AccountListResponse>('/accounts', { params });
    },

    getAccount: async (id: number): Promise<UserAccount> => {
        return api.get<UserAccount>(`/accounts/${id}`);
    },

    createStaff: async (data: CreateStaffRequest): Promise<UserAccount> => {
        return api.post<UserAccount>('/accounts/staff', data);
    },

    createClient: async (data: CreateClientRequest): Promise<UserAccount> => {
        return api.post<UserAccount>('/accounts/client', data);
    },

    // Unified create method for multi-account form
    createMultiAccount: async (data: any): Promise<UserAccount> => {
        // Route to specific endpoint based on type
        if (data.account_type === AccountType.CLIENT) {
            return api.post<UserAccount>('/accounts/client', data);
        } else {
            // Default to staff
            return api.post<UserAccount>('/accounts/staff', data);
        }
    },

    updateStaff: async (id: number, data: UpdateStaffRequest): Promise<UserAccount> => {
        return api.put<UserAccount>(`/accounts/${id}/staff`, data);
    },

    updateClient: async (id: number, data: UpdateClientRequest): Promise<UserAccount> => {
        return api.put<UserAccount>(`/accounts/${id}/client`, data);
    },

    deleteAccount: async (id: number): Promise<void> => {
        return api.delete(`/accounts/${id}`);
    },

    assignProjects: async (clientId: number, data: ProjectAssignmentRequest): Promise<void> => {
        return api.post(`/accounts/${clientId}/projects`, data);
    },

    removeProject: async (clientId: number, projectId: number): Promise<void> => {
        return api.delete(`/accounts/${clientId}/projects/${projectId}`);
    }
};
