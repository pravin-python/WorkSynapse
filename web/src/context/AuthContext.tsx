/**
 * WorkSynapse Auth Context
 * ========================
 * JWT-based authentication with session management.
 * Handles login, logout, token refresh, and RBAC.
 */
import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { apiClient, setAuthToken, clearAuthToken } from '../services/apiClient';

// User interface
export interface User {
    id: number;
    email: string;
    full_name: string;
    username?: string;
    avatar_url?: string;
    role: string;
    is_superuser: boolean;
    is_active: boolean;
    roles: string[];
    permissions: string[];
}

// Auth state interface
interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}

// Login credentials
interface LoginCredentials {
    email: string;
    password: string;
    remember_me?: boolean;
}

// Register credentials
interface RegisterCredentials {
    email: string;
    password: string;
    full_name: string;
    username?: string;
}

// Auth context interface
interface AuthContextType extends AuthState {
    login: (credentials: LoginCredentials) => Promise<void>;
    logout: () => Promise<void>;
    register: (credentials: RegisterCredentials) => Promise<void>;
    refreshAccessToken: () => Promise<boolean>;
    updateUser: (user: Partial<User>) => void;
    hasPermission: (permission: string) => boolean;
    hasRole: (role: string) => boolean;
    isAdmin: () => boolean;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Storage keys
const ACCESS_TOKEN_KEY = 'worksynapse-access-token';
const REFRESH_TOKEN_KEY = 'worksynapse-refresh-token';
const USER_KEY = 'worksynapse-user';

// Provider component
interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [state, setState] = useState<AuthState>({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: true,
    });

    // Initialize auth from localStorage
    useEffect(() => {
        const initAuth = async () => {
            const storedAccessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
            const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
            const storedUser = localStorage.getItem(USER_KEY);

            if (storedAccessToken) {
                // Set token immediately to allow request to proceed
                setAuthToken(storedAccessToken);

                try {
                    // Always verifying token by fetching latest user data
                    // This ensures roles/permissions are up to date
                    const response = await apiClient.get('/users/me');
                    const user = response.data;

                    // Update cache
                    localStorage.setItem(USER_KEY, JSON.stringify(user));

                    setState({
                        user: user,
                        accessToken: storedAccessToken,
                        refreshToken: storedRefreshToken,
                        isAuthenticated: true,
                        isLoading: false,
                    });
                } catch (error) {
                    console.error("Auth initialization failed:", error);
                    // Token expired or invalid, try refresh
                    if (storedRefreshToken) {
                        try {
                            const refreshed = await refreshTokenRequest(storedRefreshToken);
                            if (refreshed) {
                                return; // State updated by refreshTokenRequest
                            }
                        } catch {
                            // Refresh failed
                        }
                    }

                    // Clear invalid auth
                    clearAuth();
                    setState(prev => ({ ...prev, isLoading: false }));
                }
            } else {
                setState(prev => ({ ...prev, isLoading: false }));
            }
        };

        initAuth();
    }, []);

    // Refresh token request
    const refreshTokenRequest = async (refreshToken: string): Promise<boolean> => {
        try {
            const response = await apiClient.post('/auth/refresh', {
                refresh_token: refreshToken,
            });

            const { access_token, refresh_token, user } = response.data;

            localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
            localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
            localStorage.setItem(USER_KEY, JSON.stringify(user));

            setAuthToken(access_token);

            setState({
                user,
                accessToken: access_token,
                refreshToken: refresh_token,
                isAuthenticated: true,
                isLoading: false,
            });

            return true;
        } catch {
            return false;
        }
    };

    // Clear auth data
    const clearAuth = () => {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        clearAuthToken();

        setState({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
        });
    };

    // Login function
    const login = async (credentials: LoginCredentials) => {
        try {
            const response = await apiClient.post('/auth/login', credentials);
            const { access_token, refresh_token, user } = response.data;

            localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
            localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
            localStorage.setItem(USER_KEY, JSON.stringify(user));

            setAuthToken(access_token);

            setState({
                user,
                accessToken: access_token,
                refreshToken: refresh_token,
                isAuthenticated: true,
                isLoading: false,
            });
        } catch (error: any) {
            throw new Error(error.response?.data?.detail || 'Login failed');
        }
    };

    // Logout function
    const logout = async () => {
        try {
            if (state.accessToken) {
                await apiClient.post('/auth/logout');
            }
        } catch {
            // Ignore logout errors
        } finally {
            clearAuth();
        }
    };

    // Register function
    const register = async (credentials: RegisterCredentials) => {
        try {
            const response = await apiClient.post('/auth/register', credentials);
            const { access_token, refresh_token, user } = response.data;

            localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
            localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
            localStorage.setItem(USER_KEY, JSON.stringify(user));

            setAuthToken(access_token);

            setState({
                user,
                accessToken: access_token,
                refreshToken: refresh_token,
                isAuthenticated: true,
                isLoading: false,
            });
        } catch (error: any) {
            throw new Error(error.response?.data?.detail || 'Registration failed');
        }
    };

    // Refresh access token
    const refreshAccessToken = useCallback(async (): Promise<boolean> => {
        if (!state.refreshToken) {
            return false;
        }
        return refreshTokenRequest(state.refreshToken);
    }, [state.refreshToken]);

    // Update user
    const updateUser = (userData: Partial<User>) => {
        if (state.user) {
            const updatedUser = { ...state.user, ...userData };
            localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
            setState(prev => ({ ...prev, user: updatedUser }));
        }
    };

    // Check permission
    const hasPermission = useCallback((permission: string): boolean => {
        if (!state.user) return false;
        if (state.user.is_superuser) return true;
        return state.user.permissions?.includes(permission) ?? false;
    }, [state.user]);

    // Check role
    const hasRole = useCallback((role: string): boolean => {
        if (!state.user) return false;
        if (state.user.is_superuser) return true;
        return (state.user.roles?.includes(role) ?? false) || state.user.role === role;
    }, [state.user]);

    // Check admin
    const isAdmin = useCallback((): boolean => {
        if (!state.user) return false;
        return state.user.is_superuser || hasRole('ADMIN') || hasRole('SUPER_ADMIN');
    }, [state.user, hasRole]);

    const value: AuthContextType = {
        ...state,
        login,
        logout,
        register,
        refreshAccessToken,
        updateUser,
        hasPermission,
        hasRole,
        isAdmin,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

// Custom hook for using auth
export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

// HOC for protected routes
export function withAuth<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    options?: { roles?: string[]; permissions?: string[]; redirectTo?: string }
) {
    return function WithAuthComponent(props: P) {
        const { isAuthenticated, isLoading, hasRole, hasPermission } = useAuth();

        if (isLoading) {
            return <div className="loading">Loading...</div>;
        }

        if (!isAuthenticated) {
            window.location.href = options?.redirectTo || '/login';
            return null;
        }

        // Check roles
        if (options?.roles && options.roles.length > 0) {
            const hasRequiredRole = options.roles.some(role => hasRole(role));
            if (!hasRequiredRole) {
                window.location.href = '/unauthorized';
                return null;
            }
        }

        // Check permissions
        if (options?.permissions && options.permissions.length > 0) {
            const hasRequiredPermission = options.permissions.some(perm => hasPermission(perm));
            if (!hasRequiredPermission) {
                window.location.href = '/unauthorized';
                return null;
            }
        }

        return <WrappedComponent {...props} />;
    };
}
