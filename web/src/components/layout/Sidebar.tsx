import React, { useEffect, useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { uiService, UIMenu, UIMenuItem } from '../../services/ui';
import './Sidebar.css';

// Map icon string names to actual components
const IconMap: Record<string, React.ElementType> = {
    ...LucideIcons
};

interface SidebarProps {
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
    mobileOpen: boolean;
    setMobileOpen: (open: boolean) => void;
}

export function Sidebar({ isOpen, mobileOpen, setMobileOpen }: SidebarProps) {
    const { hasRole, logout } = useAuth();
    const [menuData, setMenuData] = useState<UIMenu | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMenu = async () => {
            try {
                const data = await uiService.getMenu('sidebar');
                setMenuData(data);
            } catch (error) {
                console.error("Failed to load sidebar menu:", error);
                // Fallback hardcoded menu could be added here if needed
            } finally {
                setLoading(false);
            }
        };

        fetchMenu();
    }, []);

    const canAccess = (roles?: string[]) => {
        if (!roles || roles.length === 0) return true;
        return roles.some((role: string) => hasRole(role));
    };

    const handleLinkClick = () => {
        if (window.innerWidth <= 1024) {
            setMobileOpen(false);
        }
    };

    // Helper to render icon dynamically
    const renderIcon = (iconName?: string) => {
        if (!iconName) return <LucideIcons.Circle size={20} className="nav-icon" />;
        const IconComponent = IconMap[iconName] || LucideIcons.HelpCircle;
        return <IconComponent size={20} className="nav-icon" />;
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
                        <img src="/logo.png" alt="WorkSynapse" className="logo-icon" style={{ background: 'transparent' }} />
                        <span className={`logo-text ${!isOpen ? 'hidden' : ''}`}>WorkSynapse</span>
                    </Link>
                </div>

                <div className="sidebar-content">
                    {loading ? (
                        <div className="p-4 text-gray-400">Loading menu...</div>
                    ) : (
                        menuData?.items.map((section) => {
                            // Top level items without parent are sections
                            if (section.roles && !canAccess(section.roles)) return null;

                            return (
                                <div key={section.id} className="nav-section">
                                    <div className="nav-section-header">
                                        <span className="section-title">{section.label}</span>
                                        <div className="section-divider"></div>
                                    </div>

                                    <ul className="nav-list">
                                        {section.children?.map(item => {
                                            if (item.roles && !canAccess(item.roles)) return null;

                                            return (
                                                <li key={item.id}>
                                                    <NavLink
                                                        to={item.path || '#'}
                                                        className={({ isActive }) =>
                                                            `nav-item ${isActive ? 'active' : ''}`
                                                        }
                                                        onClick={handleLinkClick}
                                                    >
                                                        {renderIcon(item.icon)}
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
                        })
                    )}
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
