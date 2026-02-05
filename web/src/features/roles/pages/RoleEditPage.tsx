import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { RoleForm } from '../components/RoleForm';
import { roleService } from '../services/roleService';
import { Role } from '../types';
import '../styles.css';

export function RoleEditPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [role, setRole] = useState<Role | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (id) {
            loadRole(parseInt(id));
        }
    }, [id]);

    const loadRole = async (roleId: number) => {
        try {
            const data = await roleService.getById(roleId);
            setRole(data);
        } catch (error) {
            console.error('Failed to load role', error);
            alert('Failed to load role details');
            navigate('/admin/roles');
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex center-center min-h-screen">
                <div className="loading-spinner-large"></div>
            </div>
        );
    }

    if (!role) {
        return <div>Role not found</div>;
    }

    return (
        <div className="role-edit-page fade-in">
            <header className="page-header">
                <div>
                    <h1>Edit Role: {role.name}</h1>
                    <p>Update role details and permissions.</p>
                </div>
            </header>

            <div className="form-card-container">
                <RoleForm mode="edit" initialData={role} />
            </div>
        </div>
    );
}
