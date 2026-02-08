import React, { useEffect, useRef } from 'react';
import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard, FolderKanban, CheckSquare, MessageSquare, StickyNote,
    Timer, Bot, Users, Shield, Settings, Cpu, HardDrive, X
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './MegaMenu.css';

interface MegaMenuProps {
    isOpen: boolean;
    onClose: () => void;
}

export function MegaMenu({ isOpen, onClose }: MegaMenuProps) {
    const { hasRole } = useAuth();
    const menuRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                onClose();
            }
        }

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen, onClose]);

    // Close on Escape key
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        if (isOpen) window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const sections = [
        {
            title: 'Main',
            items: [
                { icon: LayoutDashboard, label: 'Dashboard', desc: 'Overview & Stats', path: '/dashboard' },
                { icon: FolderKanban, label: 'Projects', desc: 'Manage Campaigns', path: '/projects' },
                { icon: CheckSquare, label: 'Tasks', desc: 'My To-Dos', path: '/tasks' },
                { icon: MessageSquare, label: 'Chat', desc: 'Team Communication', path: '/chat' },
                { icon: StickyNote, label: 'Notes', desc: 'Personal Memos', path: '/notes' },
            ]
        },
        {
            title: 'Tools',
            items: [
                { icon: Timer, label: 'Time Tracking', desc: 'Log Hours', path: '/tracking' },
                { icon: Bot, label: 'AI Agents', desc: 'Manage Assistants', path: '/ai/agents', roles: ['ADMIN', 'Admin', 'AI_ENGINEER', 'SuperUser'] },
                { icon: Cpu, label: 'AI Models', desc: 'LLM Configuration', path: '/ai/models', roles: ['ADMIN', 'Admin', 'SuperUser', 'STAFF'] },
                { icon: HardDrive, label: 'Local Models', desc: 'On-prem Inference', path: '/ai/local-models', roles: ['ADMIN', 'Admin', 'SuperUser', 'STAFF'] },
            ]
        },
        {
            title: 'Admin',
            roles: ['ADMIN', 'Admin', 'SuperUser'],
            items: [
                { icon: Users, label: 'Users', desc: 'Team Management', path: '/admin/users' },
                { icon: Shield, label: 'Roles', desc: 'Permissions Setup', path: '/admin/roles' },
                { icon: Settings, label: 'Settings', desc: 'System Config', path: '/settings' },
            ]
        }
    ];

    const canAccess = (roles?: string[]) => {
        if (!roles || roles.length === 0) return true;
        return roles.some(role => hasRole(role));
    };

    return (
        <div className="mega-menu-overlay">
            <div className="mega-menu-container glass-panel" ref={menuRef}>
                <button className="mega-menu-close" onClick={onClose}>
                    <X size={24} />
                </button>

                <div className="mega-menu-grid">
                    {sections.map((section, idx) => {
                        if (section.roles && !canAccess(section.roles)) return null;

                        return (
                            <div key={idx} className="mega-menu-section">
                                <h3 className="mega-menu-title">{section.title}</h3>
                                <div className="mega-menu-items">
                                    {section.items.map(item => {
                                        if (item.roles && !canAccess(item.roles)) return null;

                                        return (
                                            <NavLink
                                                key={item.path}
                                                to={item.path}
                                                className="mega-menu-item"
                                                onClick={onClose}
                                            >
                                                <div className="mega-menu-icon-box">
                                                    <item.icon size={20} />
                                                </div>
                                                <div className="mega-menu-content">
                                                    <span className="mega-menu-label">{item.label}</span>
                                                    <span className="mega-menu-desc">{item.desc}</span>
                                                </div>
                                            </NavLink>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
