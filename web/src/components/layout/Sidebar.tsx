import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
    LayoutDashboard, FolderKanban, CheckSquare, MessageSquare, StickyNote,
    Timer, Bot, Users, Shield, Settings, LogOut
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './Sidebar.css';

interface SidebarProps {
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
    mobileOpen: boolean;
    setMobileOpen: (open: boolean) => void;
}

export function Sidebar({ isOpen, mobileOpen, setMobileOpen }: SidebarProps) {
    const { hasRole, logout } = useAuth();

    interface NavItem {
        icon: React.ElementType;
        label: string;
        path: string;
        roles?: string[];
    }

    interface NavSection {
        title: string;
        items: NavItem[];
        roles?: string[];
    }

    const sections: NavSection[] = [
        {
            title: 'Main',
            items: [
                { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
                { icon: FolderKanban, label: 'Projects', path: '/projects' },
                { icon: CheckSquare, label: 'Tasks', path: '/tasks' },
                { icon: MessageSquare, label: 'Chat', path: '/chat' },
                { icon: StickyNote, label: 'Notes', path: '/notes' },
            ]
        },
        {
            title: 'Tools',
            items: [
                { icon: Timer, label: 'Time Tracking', path: '/tracking' },
                { icon: Bot, label: 'AI Agents', path: '/ai/agents', roles: ['ADMIN', 'Admin', 'AI_ENGINEER', 'SuperUser'] },
            ]
        },
        {
            title: 'Admin',
            roles: ['ADMIN', 'Admin', 'SuperUser'],
            items: [
                { icon: Users, label: 'Users', path: '/admin/users' },
                { icon: Shield, label: 'Roles & Permissions', path: '/admin/roles' },
            ]
        }
    ];

    const canAccess = (roles?: string[]) => {
        if (!roles || roles.length === 0) return true;
        return roles.some(role => hasRole(role));
    };

    const handleLinkClick = () => {
        if (window.innerWidth <= 1024) {
            setMobileOpen(false);
        }
    };

    return (
        <>
            {/* Mobile Overlay */}
            <div
                className={`sidebar-overlay ${mobileOpen ? 'open' : ''}`}
                onClick={() => setMobileOpen(false)}
            />

            <aside className={`sidebar-container ${isOpen ? 'expanded' : 'collapsed'} ${mobileOpen ? 'mobile-open' : ''}`}>
                <div className="sidebar-header">
                    <Link to="/dashboard" className="logo-area" title="WorkSynapse Dashboard">
                        <div className="logo-icon">W</div>
                        <span className={`logo-text ${!isOpen ? 'hidden' : ''}`}>WorkSynapse</span>
                    </Link>

                    {/* Sidebar Toggle - Moved to Header */}
                </div>

                <div className="sidebar-content">
                    {sections.map((section, idx) => {
                        if (section.roles && !canAccess(section.roles)) return null;

                        return (
                            <div key={idx} className="nav-section">
                                <div className="nav-section-header">
                                    <span className="section-title">{section.title}</span>
                                    <div className="section-divider"></div>
                                </div>

                                <ul className="nav-list">
                                    {section.items.map(item => {
                                        if (item.roles && !canAccess(item.roles)) return null;

                                        return (
                                            <li key={item.path}>
                                                <NavLink
                                                    to={item.path}
                                                    className={({ isActive }) =>
                                                        `nav-item ${isActive ? 'active' : ''}`
                                                    }
                                                    onClick={handleLinkClick}
                                                >
                                                    <item.icon size={20} className="nav-icon" />
                                                    <span className="nav-label">{item.label}</span>

                                                    {/* Tooltip for collapsed state */}
                                                    {!isOpen && <div className="nav-tooltip">{item.label}</div>}
                                                </NavLink>
                                            </li>
                                        );
                                    })}
                                </ul>
                            </div>
                        );
                    })}
                </div>

                <div className="sidebar-footer">
                    <NavLink to="/settings" className="nav-item">
                        <Settings size={20} className="nav-icon" />
                        <span className="nav-label">Settings</span>
                        {!isOpen && <div className="nav-tooltip">Settings</div>}
                    </NavLink>

                    <button onClick={() => logout()} className="nav-item logout-item">
                        <LogOut size={20} className="nav-icon" />
                        <span className="nav-label">Logout</span>
                        {!isOpen && <div className="nav-tooltip">Logout</div>}
                    </button>
                </div>
            </aside>
        </>
    );
}
