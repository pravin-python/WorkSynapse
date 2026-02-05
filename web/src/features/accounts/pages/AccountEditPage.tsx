import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AccountForm } from '../components/AccountForm';
import { accountService } from '../api/accountService';
import { UserAccount } from '../types';

export function AccountEditPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [account, setAccount] = useState<UserAccount | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (!id) return;
        loadAccount(parseInt(id));
    }, [id]);

    const loadAccount = async (accountId: number) => {
        try {
            const data = await accountService.getAccount(accountId);
            setAccount(data);
        } catch (error) {
            console.error('Failed to load account', error);
            navigate('/accounts');
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="loading-wrapper">
                <div className="loading-spinner-large"></div>
            </div>
        );
    }

    if (!account) return null;

    return (
        <div className="account-edit-page fade-in">
            <header className="page-header">
                <div>
                    <h1>Edit Account</h1>
                    <p>{account.full_name} ({account.email})</p>
                </div>
            </header>

            <div className="content-card">
                <AccountForm
                    mode="edit"
                    initialData={account}
                    accountType={account.account_type}
                />
            </div>
        </div>
    );
}
