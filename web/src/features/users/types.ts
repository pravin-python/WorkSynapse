export interface User {
    id: number;
    email: string;
    full_name: string;
    username?: string;
    role: string; // Enum role
    roles: string[]; // Dynamic Roles
    is_superuser: boolean;
    is_active: boolean;
    created_at?: string;
    last_login?: string;
}

export interface UserCreateData {
    email: string;
    full_name: string;
    password: string;
    username?: string;
    role_id?: number;
}
