export interface Permission {
    id: number;
    resource: string;
    action: string;
    description?: string;
}

export interface Role {
    id: number;
    name: string;
    description: string;
    is_system?: boolean;
    permissions: Permission[];
    created_at?: string;
    users_count?: number; // Optional, might need to fetch separately or update backend
}

export interface RoleFormData {
    name: string;
    description: string;
    permission_ids: number[];
}

export interface RoleListResponse {
    items: Role[];
    total: number;
}
