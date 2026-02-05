export enum AccountType {
    SUPERUSER = 'SUPERUSER',
    STAFF = 'STAFF',
    CLIENT = 'CLIENT',
}

export enum UserRole {
    SUPER_ADMIN = 'SUPER_ADMIN',
    ADMIN = 'ADMIN',
    MANAGER = 'MANAGER',
    TEAM_LEAD = 'TEAM_LEAD',
    DEVELOPER = 'DEVELOPER',
    VIEWER = 'VIEWER',
    GUEST = 'GUEST',
}

export enum UserStatus {
    ACTIVE = 'ACTIVE',
    INACTIVE = 'INACTIVE',
    SUSPENDED = 'SUSPENDED',
    PENDING_VERIFICATION = 'PENDING_VERIFICATION',
    LOCKED = 'LOCKED',
}

export interface UserAccount {
    id: number;
    email: string;
    full_name: string;
    account_type: AccountType;
    status: UserStatus;
    is_active: boolean;
    role: UserRole;
    department?: string;
    company_name?: string;
    company_id?: number;
    avatar_url?: string;
    created_at?: string;
    last_login_at?: string;
}

export interface AccountListResponse {
    accounts: UserAccount[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface CreateStaffRequest {
    email: string;
    full_name: string;
    password: string;
    department: string;
    role: UserRole;
}

export interface CreateClientRequest {
    email: string;
    full_name: string;
    password: string;
    company_name: string;
    company_id?: number;
    project_ids: number[];
}

export interface UpdateStaffRequest {
    full_name?: string;
    department?: string;
    role?: UserRole;
    is_active?: boolean;
}

export interface UpdateClientRequest {
    full_name?: string;
    company_name?: string;
    project_ids?: number[];
    is_active?: boolean;
}

export interface ProjectAssignmentRequest {
    project_ids: number[];
    access_level?: string;
}
