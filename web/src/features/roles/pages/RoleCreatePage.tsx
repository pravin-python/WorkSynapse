import { RoleForm } from '../components/RoleForm';
import '../styles.css';

export function RoleCreatePage() {
    return (
        <div className="role-create-page fade-in">
            <header className="page-header">
                <div>
                    <h1>Create New Role</h1>
                    <p>Define a new role and assign permissions.</p>
                </div>
            </header>

            <div className="form-card-container">
                <RoleForm mode="create" />
            </div>
        </div>
    );
}
