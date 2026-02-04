/**
 * WorkSynapse Main Layout
 * =======================
 * Responsive layout with collapsible sidebar, header with theme switcher,
 * and main content area.
 */
import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import ThemeSwitcher from '../ui/ThemeSwitcher';
import {
    LayoutDashboard,
    FolderKanban,
    CheckSquare,
    MessageSquare,
    StickyNote,
    Bot,
    Timer,
    Users,
    Shield,
    Settings,
    LogOut,
    Menu,
    X,
    Bell,
    Search,
    ChevronDown,
    ChevronRight,
} from 'lucide-react';
import './Layout.css';

interface NavItem {
    icon: React.ElementType;
    label: string;
    path: string;
    roles?: string[];
    badge?: number;
    children?: NavItem[];
}

const navigation: NavItem[] = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: FolderKanban, label: 'Projects', path: '/projects' },
    { icon: CheckSquare, label: 'Tasks', path: '/tasks' },
    { icon: MessageSquare, label: 'Chat', path: '/chat' },
    { icon: StickyNote, label: 'Notes', path: '/notes' },
    { icon: Timer, label: 'Time Tracking', path: '/tracking' },
    { icon: Bot, label: 'AI Agents', path: '/ai/agents', roles: ['ADMIN', 'AI_ENGINEER'] },
];

const adminNavigation: NavItem[] = [
    { icon: Users, label: 'Users', path: '/admin/users', roles: ['ADMIN'] },
    { icon: Shield, label: 'Roles & Permissions', path: '/admin/roles', roles: ['ADMIN'] },
];

interface LayoutProps {
    children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
    const { user, logout, hasRole, isAdmin } = useAuth();
    const { theme, isDark } = useTheme();
    const navigate = useNavigate();
    const location = useLocation();
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [userMenuOpen, setUserMenuOpen] = useState(false);

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const isActive = (path: string) => {
        return location.pathname === path || location.pathname.startsWith(path + '/');
    };

    const canAccess = (roles?: string[]) => {
        if (!roles || roles.length === 0) return true;
        return roles.some(role => hasRole(role));
    };

    return (
        <div className={`layout ${sidebarOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}>
            {/* Sidebar */}
            <aside className={`sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
                <div className="sidebar-header">
                    <Link to="/dashboard" className="logo">
                        <div className="logo-icon">W</div>
                        {sidebarOpen && <span className="logo-text">WorkSynapse</span>}
                    </Link>
                    <button
                        className="sidebar-toggle desktop-only"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                    >
                        {sidebarOpen ? <ChevronRight size={18} /> : <Menu size={18} />}
                    </button>
                    <button
                        className="sidebar-close mobile-only"
                        onClick={() => setMobileMenuOpen(false)}
                    >
                        <X size={20} />
                    </button>
                </div>

                <nav className="sidebar-nav">
                    <div className="nav-section">
                        {sidebarOpen && <span className="nav-section-title">Main</span>}
                        <ul className="nav-list">
                            {navigation.filter(item => canAccess(item.roles)).map((item) => (
                                <li key={item.path}>
                                    <Link
                                        to={item.path}
                                        className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
                                        onClick={() => setMobileMenuOpen(false)}
                                    >
                                        <item.icon size={20} />
                                        {sidebarOpen && <span>{item.label}</span>}
                                        {item.badge && sidebarOpen && (
                                            <span className="nav-badge">{item.badge}</span>
                                        )}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {isAdmin() && (
                        <div className="nav-section">
                            {sidebarOpen && <span className="nav-section-title">Admin</span>}
                            <ul className="nav-list">
                                {adminNavigation.filter(item => canAccess(item.roles)).map((item) => (
                                    <li key={item.path}>
                                        <Link
                                            to={item.path}
                                            className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
                                            onClick={() => setMobileMenuOpen(false)}
                                        >
                                            <item.icon size={20} />
                                            {sidebarOpen && <span>{item.label}</span>}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </nav>

                <div className="sidebar-footer">
                    <Link to="/settings" className={`nav-item ${isActive('/settings') ? 'active' : ''}`}>
                        <Settings size={20} />
                        {sidebarOpen && <span>Settings</span>}
                    </Link>
                    <button className="nav-item logout-btn" onClick={handleLogout}>
                        <LogOut size={20} />
                        {sidebarOpen && <span>Logout</span>}
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="main-wrapper">
                {/* Header */}
                <header className="main-header">
                    <div className="header-left">
                        <button
                            className="mobile-menu-btn mobile-only"
                            onClick={() => setMobileMenuOpen(true)}
                        >
                            <Menu size={24} />
                        </button>
                        <div className="search-bar">
                            <Search size={18} />
                            <input
                                type="text"
                                placeholder="Search..."
                                className="search-input"
                            />
                            <kbd className="search-kbd">⌘K</kbd>
                        </div>
                    </div>

                    <div className="header-right">
                        <ThemeSwitcher variant="compact" />

                        <button className="header-btn notification-btn">
                            <Bell size={20} />
                            <span className="notification-dot"></span>
                        </button>

                        <div className="user-menu">
                            <button
                                className="user-menu-trigger"
                                onClick={() => setUserMenuOpen(!userMenuOpen)}
                            >
                                <div className="user-avatar">
                                    {user?.avatar_url ? (
                                        <img src={user.avatar_url} alt={user.full_name} />
                                    ) : (
                                        <span>{user?.full_name?.[0] || 'U'}</span>
                                    )}
                                </div>
                                {sidebarOpen && (
                                    <>
                                        <div className="user-info">
                                            <span className="user-name">{user?.full_name}</span>
                                            <span className="user-role">{user?.role}</span>
                                        </div>
                                        <ChevronDown size={14} className={userMenuOpen ? 'rotate' : ''} />
                                    </>
                                )}
                            </button>

                            {userMenuOpen && (
                                <div className="user-dropdown">
                                    <Link to="/profile" className="dropdown-item" onClick={() => setUserMenuOpen(false)}>
                                        Profile
                                    </Link>
                                    <Link to="/settings" className="dropdown-item" onClick={() => setUserMenuOpen(false)}>
                                        Settings
                                    </Link>
                                    <hr className="dropdown-divider" />
                                    <button className="dropdown-item logout" onClick={handleLogout}>
                                        Logout
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </header>

                {/* Main Content */}
                <main className="main-content">
                    {children}
                </main>
            </div>

            {/* Mobile Overlay */}
            {mobileMenuOpen && (
                <div
                    className="mobile-overlay"
                    onClick={() => setMobileMenuOpen(false)}
                />
            )}
        </div>
    );
}

export default Layout;
