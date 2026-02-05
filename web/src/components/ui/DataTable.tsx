import React from 'react';
import './DataTable.css';

export interface Column<T> {
    header: string;
    accessor: (item: T) => React.ReactNode;
    width?: string;
    className?: string;
    align?: 'left' | 'center' | 'right';
}

interface DataTableProps<T> {
    data: T[];
    columns: Column<T>[];
    keyField?: keyof T;
    isLoading?: boolean;
    emptyMessage?: string;
    onRowClick?: (item: T) => void;
}

export function DataTable<T extends { id?: number | string }>({
    data,
    columns,
    keyField = 'id',
    isLoading = false,
    emptyMessage = "No data found",
    onRowClick
}: DataTableProps<T>) {

    if (isLoading) {
        return (
            <div className="data-table-loading">
                <div className="loading-spinner"></div>
                <span>Loading data...</span>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="data-table-empty">
                <p>{emptyMessage}</p>
            </div>
        );
    }

    return (
        <table className="data-table">
            <thead>
                <tr>
                    {columns.map((col, index) => (
                        <th
                            key={index}
                            style={{ width: col.width, textAlign: col.align || 'left' }}
                            className={col.className}
                        >
                            {col.header}
                        </th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {data.map((item, rowIndex) => (
                    <tr
                        key={String(item[keyField]) || rowIndex}
                        onClick={() => onRowClick && onRowClick(item)}
                        className={onRowClick ? 'clickable-row' : ''}
                    >
                        {columns.map((col, colIndex) => (
                            <td
                                key={colIndex}
                                style={{ textAlign: col.align || 'left' }}
                                className={col.className}
                            >
                                {col.accessor(item)}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
}
