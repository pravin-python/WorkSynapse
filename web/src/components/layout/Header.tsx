import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Menu, User, Settings, LogOut, ChevronDown, PanelLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { SearchInput } from '../ui/SearchInput';
import { MegaMenu } from './MegaMenu';
import './Header.css';

interface HeaderProps {
    onSidebarToggle?: () => void;
    isSidebarOpen?: boolean;
}

export function Header({ onSidebarToggle, isSidebarOpen }: HeaderProps) {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [isMegaMenuOpen, setIsMegaMenuOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsProfileOpen(false);
            }
        }

        if (isProfileOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isProfileOpen]);

    // Close on ESC key
    useEffect(() => {
        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === 'Escape') {
                setIsProfileOpen(false);
            }
        }

        if (isProfileOpen) {
            document.addEventListener('keydown', handleKeyDown);
        }

        return () => {
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [isProfileOpen]);

    // Handle Global Keyboard Shortcuts
    useEffect(() => {
        function handleGlobalKeyDown(event: KeyboardEvent) {
            // Ctrl + R to focus search
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'r') {
                event.preventDefault(); // Prevent browser refresh
                searchInputRef.current?.focus();
            }
        }

        document.addEventListener('keydown', handleGlobalKeyDown);
        return () => {
            document.removeEventListener('keydown', handleGlobalKeyDown);
        };
    }, []);

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <header className="app-header">
            <div className="header-left">
                <button
                    className={`menu-trigger ${isMegaMenuOpen ? 'active' : ''}`}
                    onClick={() => setIsMegaMenuOpen(!isMegaMenuOpen)}
                    aria-label="Open menu"
                >
                    <Menu size={20} />
                </button>

                <Link to="/dashboard" className="header-logo">
                    <img src="/logo.png" alt="WorkSynapse" className="header-logo-icon" style={{ background: 'transparent' }} />
                    <span className="header-logo-text">WorkSynapse</span>
                </Link>



                <SearchInput
                    ref={searchInputRef}
                    className="global-search"
                    placeholder="Search..."
                    endAdornment={<div className="kbd-shortcut">Ctrl + R</div>}
                />
            </div>

            <div className="header-right">
                <button className="icon-btn notification-btn" aria-label="Notifications">
                    <Bell size={20} />
                    <span className="badge-dot"></span>
                </button>

                <div className="profile-menu" ref={dropdownRef}>
                    <button
                        className={`profile-trigger ${isProfileOpen ? 'active' : ''}`}
                        onClick={() => setIsProfileOpen(!isProfileOpen)}
                        aria-expanded={isProfileOpen}
                    >
                        <div className="avatar">
                            {user?.avatar_url ? (
                                <img src={user.avatar_url} alt={user.full_name} />
                            ) : (
                                <span>{user?.full_name?.[0] || 'U'}</span>
                            )}
                        </div>
                        <div className="user-info desktop-only">
                            <span className="user-name">{user?.full_name}</span>
                            <span className="user-role">{user?.role?.replace('_', ' ')}</span>
                        </div>
                        <ChevronDown size={14} className={`chevron ${isProfileOpen ? 'rotate' : ''}`} />
                    </button>

                    {isProfileOpen && (
                        <div className="dropdown-menu">
                            <div className="dropdown-header mobile-only">
                                <span className="user-name">{user?.full_name}</span>
                                <span className="user-role">{user?.role?.replace('_', ' ')}</span>
                            </div>

                            <Link to="/profile" className="dropdown-item" onClick={() => setIsProfileOpen(false)}>
                                <User size={16} />
                                <span>Profile</span>
                            </Link>
                            <Link to="/settings" className="dropdown-item" onClick={() => setIsProfileOpen(false)}>
                                <Settings size={16} />
                                <span>Settings</span>
                            </Link>

                            <div className="dropdown-divider"></div>

                            <button className="dropdown-item text-error" onClick={handleLogout}>
                                <LogOut size={16} />
                                <span>Logout</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>
            {/* Mega Menu Component */}
            <MegaMenu isOpen={isMegaMenuOpen} onClose={() => setIsMegaMenuOpen(false)} />
        </header>
    );
}
