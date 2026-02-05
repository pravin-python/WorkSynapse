import React, { useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import './Layout.css';

interface LayoutProps {
    children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
    // Initialize sidebar state from localStorage, default to true (expanded)
    const [sidebarOpen, setSidebarOpen] = useState(() => {
        const saved = localStorage.getItem('worksynapse_sidebar_state');
        if (saved !== null) {
            return saved === 'expanded';
        }
        return window.innerWidth > 1024;
    });

    const [mobileOpen, setMobileOpen] = useState(false);

    // Save state to localStorage whenever it changes
    useEffect(() => {
        localStorage.setItem('worksynapse_sidebar_state', sidebarOpen ? 'expanded' : 'collapsed');
    }, [sidebarOpen]);

    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth <= 1024 && sidebarOpen) {
                setSidebarOpen(false);
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [sidebarOpen]);

    const toggleSidebar = () => setSidebarOpen(prev => !prev);

    return (
        <div className="layout-root">
            <Sidebar
                isOpen={sidebarOpen}
                setIsOpen={setSidebarOpen}
                mobileOpen={mobileOpen}
                setMobileOpen={setMobileOpen}
            />

            <div className={`layout-content ${sidebarOpen ? 'expanded' : 'collapsed'}`}>
                <Header
                    onMobileMenuClick={() => setMobileOpen(true)}
                    onSidebarToggle={toggleSidebar}
                    isSidebarOpen={sidebarOpen}
                />
                <main className="main-viewport">
                    {children}
                </main>
            </div>
        </div>
    );
}

export default Layout; // Export default for lazy loading compatibility
