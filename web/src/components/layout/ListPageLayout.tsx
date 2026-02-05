import React from 'react';
import './ListPageLayout.css';

interface ListPageLayoutProps {
    header: React.ReactNode;
    filterBar: React.ReactNode;
    table: React.ReactNode;
    pagination?: React.ReactNode;
    className?: string;
}

export function ListPageLayout({
    header,
    filterBar,
    table,
    pagination,
    className = ""
}: ListPageLayoutProps) {
    return (
        <div className={`list-page-layout fade-in ${className}`}>
            <div className="list-page-header-section">
                {header}
            </div>

            <div className="list-page-content">
                <div className="list-filter-card">
                    {filterBar}
                </div>

                <div className="list-data-card">
                    <div className="table-wrapper">
                        {table}
                    </div>
                </div>
            </div>

            {pagination && (
                <div className="list-page-footer">
                    {pagination}
                </div>
            )}
        </div>
    );
}
