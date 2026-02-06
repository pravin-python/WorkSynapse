/**
 * WorkSynapse - Main Application Entry
 * =====================================
 * Root application with routing, providers, and protected routes.
 */
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { LoaderProvider } from './components/ui/loader/LoaderContext';
import { GlobalLoader } from './components/ui/loader/GlobalLoader';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/layout/Layout';

// Import styles
import './styles/themes.css';

// Lazy load pages for code splitting
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const DashboardPage = lazy(() => import('./pages/dashboard/DashboardPage'));
const ProjectsPage = lazy(() => import('./pages/projects/ProjectsPage'));
const ProjectDetailPage = lazy(() => import('./pages/projects/ProjectDetailPage'));
const TasksPage = lazy(() => import('./pages/tasks/TasksPage'));
const ChatPage = lazy(() => import('./pages/chat/ChatPage'));
const NotesPage = lazy(() => import('./pages/notes/NotesPage'));
const TrackingPage = lazy(() => import('./pages/tracking/TrackingPage'));
const ProfilePage = lazy(() => import('./pages/profile/ProfilePage'));
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage'));
const ActivityDashboardPage = lazy(() => import('./pages/activity/ActivityDashboardPage'));

// Admin pages
const AdminUsersPage = lazy(() => import('./features/accounts/pages/AccountListPage').then(module => ({ default: module.AccountListPage })));
const AccountCreatePage = lazy(() => import('./features/accounts/pages/AccountCreatePage').then(module => ({ default: module.AccountCreatePage })));
const AccountEditPage = lazy(() => import('./features/accounts/pages/AccountEditPage').then(module => ({ default: module.AccountEditPage })));

// Role Management Pages
const AdminRolesPage = lazy(() => import('./features/roles/pages/RoleListPage').then(module => ({ default: module.RoleListPage })));
const RoleCreatePage = lazy(() => import('./features/roles/pages/RoleCreatePage').then(module => ({ default: module.RoleCreatePage })));
const RoleEditPage = lazy(() => import('./features/roles/pages/RoleEditPage').then(module => ({ default: module.RoleEditPage })));

// AI pages
const AISessionsPage = lazy(() => import('./pages/ai/SessionsPage'));

// LLM Key Management pages
const LLMKeysPage = lazy(() => import('./pages/llm/LLMKeysPage'));
const CreateAgentPage = lazy(() => import('./pages/llm/CreateAgentPage'));

// Agent Builder pages
const AgentBuilderListPage = lazy(() => import('./features/agents/pages/AgentListPage'));
const AgentBuilderFormPage = lazy(() => import('./features/agents/components/AgentBuilderForm'));

// AI Model Management pages
const AIModelsPage = lazy(() => import('./features/ai-models/pages/AIModelsPage'));
const LocalModelsPage = lazy(() => import('./features/local-models/pages/LocalModelsPage').then(module => ({ default: module.LocalModelsPage })));

// Loading fallback
function LoadingFallback() {
    return (
        <div className="loading-screen">
            <div className="loading-content">
                <div className="loading-spinner-large"></div>
                <p>Loading...</p>
            </div>
        </div>
    );
}

// Protected Route wrapper
function ProtectedRoute({
    children,
    roles = [],
    redirectTo = '/login'
}: {
    children?: React.ReactNode;
    roles?: string[];
    redirectTo?: string;
}) {
    const { isAuthenticated, isLoading, hasRole, isAdmin } = useAuth();

    if (isLoading) {
        return <LoadingFallback />;
    }

    if (!isAuthenticated) {
        return <Navigate to={redirectTo} replace />;
    }

    // Check role requirements
    if (roles.length > 0) {
        const hasRequiredRole = isAdmin() || roles.some(role => hasRole(role));
        if (!hasRequiredRole) {
            return <Navigate to="/unauthorized" replace />;
        }
    }

    return children ? <>{children}</> : <Outlet />;
}

// Public Route (redirects if already authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return <LoadingFallback />;
    }

    if (isAuthenticated) {
        return <Navigate to="/dashboard" replace />;
    }

    return <>{children}</>;
}

// Layout wrapper for protected routes
function ProtectedLayout() {
    return (
        <Layout>
            <Suspense fallback={<LoadingFallback />}>
                <Outlet />
            </Suspense>
        </Layout>
    );
}

// Main App Component
function AppRoutes() {
    return (
        <Routes>
            {/* Public Routes */}
            <Route path="/login" element={
                <PublicRoute>
                    <Suspense fallback={<LoadingFallback />}>
                        <LoginPage />
                    </Suspense>
                </PublicRoute>
            } />
            <Route path="/register" element={
                <PublicRoute>
                    <Suspense fallback={<LoadingFallback />}>
                        <RegisterPage />
                    </Suspense>
                </PublicRoute>
            } />

            {/* Protected Routes with Layout */}
            <Route element={<ProtectedRoute><ProtectedLayout /></ProtectedRoute>}>
                {/* Dashboard - All authenticated users */}
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/my/activity" element={<ActivityDashboardPage />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />

                {/* Projects - Project Members */}
                <Route path="/projects" element={<ProjectsPage />} />
                <Route path="/projects/:id" element={<ProjectDetailPage />} />

                {/* Tasks - Based on project role */}
                <Route path="/tasks" element={<TasksPage />} />

                {/* Chat - Channel Members */}
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/chat/:channelId" element={<ChatPage />} />

                {/* Notes - Owner + Shared Users */}
                <Route path="/notes" element={<NotesPage />} />

                {/* Tracking - Admins / User self-access */}
                <Route path="/tracking" element={<TrackingPage />} />

                {/* Profile - Logged-in user */}
                <Route path="/profile" element={<ProfilePage />} />

                {/* Settings - All roles */}
                <Route path="/settings" element={<SettingsPage />} />
            </Route>

            {/* Admin Routes */}
            <Route element={<ProtectedRoute roles={['ADMIN', 'SUPER_ADMIN']}><ProtectedLayout /></ProtectedRoute>}>
                <Route path="/admin/users" element={<AdminUsersPage />} />
                <Route path="/accounts/new" element={<AccountCreatePage />} />
                <Route path="/accounts/:id/edit" element={<AccountEditPage />} />
                <Route path="/admin/roles" element={<AdminRolesPage />} />
                <Route path="/admin/roles/new" element={<RoleCreatePage />} />
                <Route path="/admin/roles/:id/edit" element={<RoleEditPage />} />
            </Route>

            {/* AI Routes */}
            <Route element={<ProtectedRoute roles={['ADMIN', 'AI_ENGINEER']}><ProtectedLayout /></ProtectedRoute>}>
                <Route path="/ai/agents" element={<AgentBuilderListPage />} />
                <Route path="/ai/agents/create" element={<AgentBuilderFormPage />} />
                <Route path="/ai/agents/:agentId/edit" element={<AgentBuilderFormPage />} />
                <Route path="/ai/sessions" element={<AISessionsPage />} />
            </Route>

            {/* LLM Key Management Routes - All authenticated users */}
            <Route element={<ProtectedRoute><ProtectedLayout /></ProtectedRoute>}>
                <Route path="/llm/keys" element={<LLMKeysPage />} />
                <Route path="/llm/agents/create" element={<CreateAgentPage />} />
            </Route>

            {/* AI Model Management Routes - Admin/Staff only */}
            <Route element={<ProtectedRoute roles={['ADMIN', 'SUPER_ADMIN', 'STAFF']}><ProtectedLayout /></ProtectedRoute>}>
                <Route path="/ai/models" element={<AIModelsPage />} />
                <Route path="/ai/local-models" element={<LocalModelsPage />} />
            </Route>

            {/* Unauthorized page */}
            <Route path="/unauthorized" element={
                <div className="error-page">
                    <h1>403</h1>
                    <p>You don't have permission to access this page.</p>
                    <a href="/dashboard">Return to Dashboard</a>
                </div>
            } />

            {/* 404 page */}
            <Route path="*" element={
                <div className="error-page">
                    <h1>404</h1>
                    <p>The page you're looking for doesn't exist.</p>
                    <a href="/dashboard">Return to Dashboard</a>
                </div>
            } />
        </Routes>
    );
}

// Root App with Providers
function App() {
    return (
        <ThemeProvider defaultTheme="bento">
            <LoaderProvider>
                <GlobalLoader />
                <AuthProvider>
                    <BrowserRouter>
                        <AppRoutes />
                    </BrowserRouter>
                </AuthProvider>
            </LoaderProvider>
        </ThemeProvider>
    );
}

export default App;
