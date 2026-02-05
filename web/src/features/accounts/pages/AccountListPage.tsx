import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
    Users, Plus,
    Shield, Briefcase, Building,
    Edit, Trash2
} from 'lucide-react';

// Shared Layout & UI Components
import { ListPageLayout } from '../../../components/layout/ListPageLayout';
import { PageHeader } from '../../../components/ui/PageHeader';
import { FilterBar } from '../../../components/ui/FilterBar';
import { DataTable, Column } from '../../../components/ui/DataTable';
import { Pagination } from '../../../components/ui/Pagination';

import { accountService } from '../api/accountService';
import { AccountType, UserAccount } from '../types';

export function AccountListPage() {
    const navigate = useNavigate();
    const [accounts, setAccounts] = useState<UserAccount[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [typeFilter, setTypeFilter] = useState<AccountType | 'ALL'>('ALL');

    // Pagination
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);
    const [total, setTotal] = useState(0);

    useEffect(() => {
        const timer = setTimeout(() => {
            loadAccounts();
        }, 300);
        return () => clearTimeout(timer);
    }, [page, typeFilter, searchQuery]);

    const loadAccounts = async () => {
        setIsLoading(true);
        try {
            const response = await accountService.listAccounts(
                page,
                pageSize,
                typeFilter === 'ALL' ? undefined : typeFilter,
                searchQuery || undefined
            );
            setAccounts(response.accounts);
            setTotal(response.total);
        } catch (error) {
            console.error('Failed to load accounts', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm('Are you sure you want to delete this account?')) return;
        try {
            await accountService.deleteAccount(id);
            loadAccounts();
        } catch (error) {
            console.error('Failed to delete account', error);
            alert('Failed to delete account');
        }
    };

    const columns: Column<UserAccount>[] = useMemo(() => [
        {
            header: 'User',
            accessor: (account) => (
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center overflow-hidden text-gray-500 font-medium" style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'var(--bg-active)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {account.avatar_url ? (
                            <img src={account.avatar_url} alt={account.full_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                            account.full_name.charAt(0)
                        )}
                    </div>
                    <div>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{account.full_name}</div>
                        <div style={{ fontSize: '0.85em', color: 'var(--text-secondary)' }}>{account.email}</div>
                    </div>
                </div>
            )
        },
        {
            header: 'Role',
            accessor: (account) => {
                let badgeClass = "badge-gray";
                let icon = null;

                if (account.account_type === AccountType.SUPERUSER) {
                    badgeClass = "badge-purple";
                    icon = <Shield size={12} style={{ marginRight: '4px' }} />;
                } else if (account.account_type === AccountType.STAFF) {
                    badgeClass = "badge-blue";
                    icon = <Users size={12} style={{ marginRight: '4px' }} />;
                } else {
                    badgeClass = "badge-green";
                    icon = <Briefcase size={12} style={{ marginRight: '4px' }} />;
                }

                // Since we don't have tailwind, we use inline styles/classes that we know exist or inline
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className={`badge ${badgeClass}`} style={{ display: 'inline-flex', alignItems: 'center', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>
                            {icon}
                            {account.account_type}
                        </span>
                        {account.role && (
                            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{account.role.replace('_', ' ')}</span>
                        )}
                    </div>
                );
            }
        },
        {
            header: 'Organization',
            accessor: (account) => (
                <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                    {account.department && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Building size={14} />
                            {account.department}
                        </div>
                    )}
                    {account.company_name && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Briefcase size={14} />
                            {account.company_name}
                        </div>
                    )}
                    {!account.department && !account.company_name && <span>-</span>}
                </div>
            )
        },
        {
            header: 'Status',
            accessor: (account) => (
                <span style={{
                    display: 'inline-block',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 500,
                    backgroundColor: account.is_active ? 'var(--success-bg)' : 'var(--error-bg)',
                    color: account.is_active ? 'var(--success-text)' : 'var(--error-text)'
                }}>
                    {account.is_active ? 'Active' : 'Inactive'}
                </span>
            )
        },
        {
            header: 'Joined',
            accessor: (account) => (
                <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                    {account.created_at ? new Date(account.created_at).toLocaleDateString() : '-'}
                </span>
            )
        },
        {
            header: 'Actions',
            align: 'right',
            accessor: (account) => (
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                    <button
                        style={{ padding: '6px', color: 'var(--text-secondary)', background: 'transparent', border: 'none', cursor: 'pointer' }}
                        onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/accounts/${account.id}/edit`);
                        }}
                        title="Edit"
                    >
                        <Edit size={16} />
                    </button>
                    <button
                        style={{ padding: '6px', color: 'var(--error-text)', background: 'transparent', border: 'none', cursor: 'pointer' }}
                        onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(account.id);
                        }}
                        title="Delete"
                    >
                        <Trash2 size={16} />
                    </button>
                </div>
            )
        }
    ], [navigate]);

    return (
        <ListPageLayout
            header={
                <PageHeader
                    title="Account Management"
                    subtitle="Manage access for staff, clients, and administrators."
                    action={
                        <Link to="/accounts/new" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Plus size={18} />
                            <span>Create Account</span>
                        </Link>
                    }
                />
            }
            filterBar={
                <FilterBar
                    onSearch={(query) => {
                        setPage(1);
                        setSearchQuery(query);
                    }}
                    searchPlaceholder="Search by name, email..."
                    filters={[
                        {
                            type: 'select',
                            value: typeFilter,
                            onChange: (val) => setTypeFilter(val as any),
                            placeholder: "All Types",
                            options: [
                                { label: 'All Types', value: 'ALL' },
                                { label: 'Staff', value: AccountType.STAFF },
                                { label: 'Clients', value: AccountType.CLIENT },
                                { label: 'SuperUsers', value: AccountType.SUPERUSER }
                            ]
                        }
                    ]}
                    onReset={() => {
                        setSearchQuery('');
                        setTypeFilter('ALL');
                        setPage(1);
                    }}
                />
            }
            table={
                <DataTable
                    data={accounts}
                    columns={columns}
                    isLoading={isLoading}
                    onRowClick={(account) => navigate(`/accounts/${account.id}/edit`)}
                    emptyMessage="No accounts found. Create one or adjust filters."
                />
            }
            pagination={
                <Pagination
                    currentPage={page}
                    totalItems={total}
                    pageSize={pageSize}
                    onPageChange={setPage}
                />
            }
        />
    );
}
