import React, { useState } from 'react';
// import { Sidebar } from './Sidebar'; // Removed global sidebar
import { Header } from './Header';
import './Layout.css';

interface LayoutProps {
    children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
    // Top-heavy layout: No sidebar state needed here anymore
    // Sidebar will be context-based on specific pages if needed

    const [mobileOpen, setMobileOpen] = useState(false);



    return (
        <div className="layout-root">
            <div className="layout-content">
                <Header />
                <main className="main-viewport">
                    {children}
                </main>
            </div>
        </div>
    );
}

export default Layout; // Export default for lazy loading compatibility
