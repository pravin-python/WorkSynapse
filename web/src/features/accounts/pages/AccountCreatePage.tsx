import React, { useState } from 'react';
import { AccountForm } from '../components/AccountForm';
import { AccountType } from '../types';
import { Users, Briefcase, CheckCircle2 } from 'lucide-react';
import '../styles.css';

export function AccountCreatePage() {
    // Default to STAFF, ensuring stable initial state
    const [selectedType, setSelectedType] = useState<AccountType>(AccountType.STAFF);

    return (
        <div className="account-create-page fade-in">
            <header className="page-header">
                <div>
                    <h1>Create New Account</h1>
                    <p>Add a new user to the system. Choose the account type below.</p>
                </div>
            </header>

            <div className="type-selector-grid">
                <button
                    className={`type-selection-card ${selectedType === AccountType.STAFF ? 'active' : ''}`}
                    onClick={() => setSelectedType(AccountType.STAFF)}
                    type="button"
                >
                    <div className="card-icon-wrapper">
                        <Users size={28} />
                    </div>
                    <div className="card-content">
                        <h3>Staff Member</h3>
                        <p>Internal employees with access to company resources, AI tools, and system administrative features.</p>
                    </div>
                    {selectedType === AccountType.STAFF && (
                        <div className="card-check">
                            <CheckCircle2 size={24} />
                        </div>
                    )}
                </button>

                <button
                    className={`type-selection-card ${selectedType === AccountType.CLIENT ? 'active' : ''}`}
                    onClick={() => setSelectedType(AccountType.CLIENT)}
                    type="button"
                >
                    <div className="card-icon-wrapper">
                        <Briefcase size={28} />
                    </div>
                    <div className="card-content">
                        <h3>Client Account</h3>
                        <p>External stakeholders with restricted access to specific projects, tasks, and progress reports.</p>
                    </div>
                    {selectedType === AccountType.CLIENT && (
                        <div className="card-check">
                            <CheckCircle2 size={24} />
                        </div>
                    )}
                </button>
            </div>

            <div className="form-card-container">
                <AccountForm mode="create" accountType={selectedType} />
            </div>
        </div>
    );
}
