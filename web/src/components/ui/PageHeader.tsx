import React from 'react';
import './PageHeader.css';

interface PageHeaderProps {
    title: string;
    subtitle?: string;
    action?: React.ReactNode;
}

export function PageHeader({ title, subtitle, action }: PageHeaderProps) {
    return (
        <header className="page-header-component">
            <div className="page-header-content">
                <h1 className="page-title">{title}</h1>
                {subtitle && <p className="page-subtitle">{subtitle}</p>}
            </div>
            {action && <div className="page-header-action">{action}</div>}
        </header>
    );
}
