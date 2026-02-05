import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    User, Mail, Lock, UserCog, Building, Briefcase,
    Save, Check, AlertCircle, ChevronDown, CheckCircle, Search, X
} from 'lucide-react';
import {
    AccountType,
    UserRole,
    UserAccount
} from '../types';
import { accountService } from '../api/accountService';
import { roleService } from '../../../features/roles/services/roleService';
import { Role } from '../../../features/roles/types';
import { api } from '../../../services/apiClient';
import { SearchInput } from '../../../components/ui/SearchInput'; // Import reusable SearchInput
import './AccountForm.css';

interface AccountFormProps {
    initialData?: UserAccount;
    mode: 'create' | 'edit';
    accountType?: AccountType; // Required for create mode
    onSuccess?: () => void;
}

// Simple Project interface for selection
interface ProjectSummary {
    id: number;
    name: string;
}

export function AccountForm({ initialData, mode, accountType, onSuccess }: AccountFormProps) {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [projects, setProjects] = useState<ProjectSummary[]>([]);
    const [roles, setRoles] = useState<Role[]>([]);

    // Form state
    const [formData, setFormData] = useState({
        email: initialData?.email || '',
        full_name: initialData?.full_name || '',
        password: '',
        confirmPassword: '',
        department: initialData?.department || '',
        role: initialData?.role || UserRole.DEVELOPER,
        role_id: initialData?.role_id,
        company_name: initialData?.company_name || '',
        company_id: initialData?.company_id || undefined,
        project_ids: [] as number[],
        is_active: initialData?.is_active ?? true,
    });

    // Project Search State
    const [projectSearch, setProjectSearch] = useState('');
    const [filteredProjects, setFilteredProjects] = useState<ProjectSummary[]>([]);
    const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false);

    // NOTE: Removed local ref for click-outside as SearchInput doesn't expose internal ref easily in this context
    // Instead we can use a wrapper ref for the dropdown area
    const dropdownContainerRef = useRef<HTMLDivElement>(null);

    // Determine effective account type
    const type = initialData?.account_type || accountType || AccountType.STAFF;

    // Passwords validation state
    const [passwordsMatch, setPasswordsMatch] = useState(true);

    useEffect(() => {
        if (type === AccountType.STAFF) {
            loadRoles();
        }

        if (type === AccountType.CLIENT) {
            loadProjects();
            // If editing, load already assigned projects logic would go here
        }
    }, [type, mode, initialData]);

    useEffect(() => {
        if (formData.password && formData.confirmPassword) {
            setPasswordsMatch(formData.password === formData.confirmPassword);
        } else {
            setPasswordsMatch(true);
        }
    }, [formData.password, formData.confirmPassword]);

    // Close project dropdown when checking outside wrapper
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownContainerRef.current && !dropdownContainerRef.current.contains(event.target as Node)) {
                setIsProjectDropdownOpen(false);
                setProjectSearch(''); // Optional: clear search on close
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Filter projects based on search
    useEffect(() => {
        if (!projectSearch.trim()) {
            setFilteredProjects([]);
            setIsProjectDropdownOpen(false); // Close if empty
            return;
        }
        const filtered = projects.filter(p =>
            p.name.toLowerCase().includes(projectSearch.toLowerCase()) &&
            !formData.project_ids.includes(p.id) // Don't show already selected
        );
        setFilteredProjects(filtered);
        setIsProjectDropdownOpen(true); // Open if has results or even if 0 results but user typed?
        // Let's keep it open if user typed to show "No results" if we wanted.
        // For now, simple logic. 
    }, [projectSearch, projects, formData.project_ids]);

    const loadRoles = async () => {
        try {
            const data = await roleService.getAll({ limit: 100 });
            setRoles(data.items);
        } catch (err) {
            console.error('Failed to load roles', err);
        }
    };

    const loadProjects = async () => {
        try {
            const data = await api.get<ProjectSummary[]>('/projects');
            setProjects(data || []);
        } catch (err) {
            console.error('Failed to load projects', err);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        if (type === 'checkbox') {
            const checked = (e.target as HTMLInputElement).checked;
            setFormData(prev => ({ ...prev, [name]: checked }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    };

    const addProject = (project: ProjectSummary) => {
        setFormData(prev => ({
            ...prev,
            project_ids: [...prev.project_ids, project.id]
        }));
        setProjectSearch(''); // Clear search after add
        setIsProjectDropdownOpen(false);
    };

    const removeProject = (projectId: number) => {
        setFormData(prev => ({
            ...prev,
            project_ids: prev.project_ids.filter(id => id !== projectId)
        }));
    };

    const getProjectName = (id: number) => projects.find(p => p.id === id)?.name || `Project #${id}`;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        if (mode === 'create' && !formData.password) {
            setError("Password is required for new accounts");
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            setError("Please enter a valid email address");
            return;
        }

        if (type === AccountType.STAFF && !formData.role_id) {
            setError("Please select a role for the staff member");
            return;
        }

        if (type === AccountType.CLIENT && !formData.company_name) {
            setError("Company name is required for client accounts");
            return;
        }

        setIsLoading(true);

        try {
            const payload = {
                ...formData,
                account_type: type
            };
            const { confirmPassword, ...apiPayload } = payload;

            if (mode === 'create') {
                await accountService.createMultiAccount(apiPayload);
            } else {
                // await accountService.updateAccount(initialData!.id, apiPayload);
            }

            if (onSuccess) {
                onSuccess();
            } else {
                navigate('/admin/users');
            }
        } catch (err: any) {
            console.error('Failed to save account', err);
            setError(err.response?.data?.detail || 'Failed to save account. Please check your inputs.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="account-form-container fade-in">
            {error && (
                <div className="form-error mb-6">
                    <AlertCircle size={20} />
                    <span>{error}</span>
                </div>
            )}

            <div className="account-form-grid">
                {/* Personal Information Header */}
                <div className="form-section-header">
                    <User size={20} />
                    <h3>Personal Information</h3>
                </div>

                <div className="form-group">
                    <label>Full Name</label>
                    <div className="input-icon-wrapper">
                        <User size={18} />
                        <input
                            type="text"
                            name="full_name"
                            value={formData.full_name}
                            onChange={handleChange}
                            placeholder="John Doe"
                            required
                        />
                    </div>
                </div>

                <div className="form-group">
                    <label>Email Address</label>
                    <div className="input-icon-wrapper">
                        <Mail size={18} />
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="john@company.com"
                            required
                        />
                    </div>
                </div>

                {/* Password Section */}
                <div className="form-group">
                    <label>Password {mode === 'edit' && '(Leave blank to keep)'}</label>
                    <div className="input-icon-wrapper">
                        <Lock size={18} />
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder={mode === 'create' ? "Create password" : "New password"}
                            required={mode === 'create'}
                            minLength={8}
                        />
                    </div>
                </div>

                <div className="form-group">
                    <label>Confirm Password</label>
                    <div className="input-icon-wrapper">
                        <Lock size={18} />
                        <input
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder="Confirm password"
                            required={mode === 'create' || !!formData.password}
                            className={!passwordsMatch ? 'input-error' : ''}
                        />
                        {formData.confirmPassword && passwordsMatch && (
                            <CheckCircle size={16} className="absolute right-3 text-success" />
                        )}
                    </div>
                    {!passwordsMatch && (
                        <span className="text-xs text-error mt-1">Passwords do not match</span>
                    )}
                </div>

                {/* Account Specific Fields based on Type */}
                {type === AccountType.STAFF && (
                    <>
                        <div className="form-section-header mt-4">
                            <Briefcase size={20} />
                            <h3>Staff Details</h3>
                        </div>

                        <div className="form-group">
                            <label>Department</label>
                            <div className="input-icon-wrapper">
                                <Building size={18} />
                                <input
                                    type="text"
                                    name="department"
                                    value={formData.department}
                                    onChange={handleChange}
                                    placeholder="e.g. Engineering"
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label>System Role</label>
                            <div className="input-icon-wrapper">
                                <UserCog size={18} />
                                <select
                                    name="role_id"
                                    value={formData.role_id || ''}
                                    onChange={handleChange}
                                    className="simple-select"
                                    required
                                >
                                    <option value="">Select Role...</option>
                                    {roles.map(role => (
                                        <option key={role.id} value={role.id}>
                                            {role.name}
                                        </option>
                                    ))}
                                </select>
                                <ChevronDown size={16} className="select-arrow" />
                            </div>
                        </div>
                    </>
                )}

                {type === AccountType.CLIENT && (
                    <>
                        <div className="form-section-header mt-4">
                            <Building size={20} />
                            <h3>Client Organization</h3>
                        </div>

                        <div className="form-group">
                            <label>Company Name</label>
                            <div className="input-icon-wrapper">
                                <Building size={18} />
                                <input
                                    type="text"
                                    name="company_name"
                                    value={formData.company_name}
                                    onChange={handleChange}
                                    placeholder="ACME Corp"
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Industry / Sector</label>
                            <div className="input-icon-wrapper">
                                <Briefcase size={18} />
                                <input
                                    type="text"
                                    name="department"
                                    value={formData.department}
                                    onChange={handleChange}
                                    placeholder="e.g. Retail, FinTech"
                                />
                            </div>
                        </div>

                        <div className="form-section-header mt-4">
                            <Briefcase size={20} />
                            <h3>Project Access</h3>
                        </div>

                        <div className="project-selector-container" ref={dropdownContainerRef}>
                            <p className="text-sm text-muted mb-3">Search and assign projects to this client.</p>

                            <div style={{ position: 'relative' }}>
                                <SearchInput
                                    value={projectSearch}
                                    onChange={setProjectSearch}
                                    placeholder="Search active projects..."
                                    className="w-full"
                                    debounceMs={150}
                                />

                                {isProjectDropdownOpen && filteredProjects.length > 0 && (
                                    <div className="project-search-results" style={{ top: '45px' }}>
                                        {filteredProjects.map(project => (
                                            <div
                                                key={project.id}
                                                className="project-result-item"
                                                onClick={() => addProject(project)}
                                            >
                                                <span>{project.name}</span>
                                                <span className="text-xs text-primary">Assign</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="selected-projects-list mt-3">
                                {formData.project_ids.map(id => (
                                    <div key={id} className="selected-project-tag">
                                        <span>{getProjectName(id)}</span>
                                        <button
                                            type="button"
                                            className="remove-project-btn"
                                            onClick={() => removeProject(id)}
                                        >
                                            <X size={14} />
                                        </button>
                                    </div>
                                ))}
                                {formData.project_ids.length === 0 && (
                                    <span className="text-sm text-muted italic">No projects assigned yet.</span>
                                )}
                            </div>
                        </div>
                    </>
                )}
            </div>

            <div className="form-actions mt-8">
                <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => navigate(-1)}
                    disabled={isLoading}
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <div className="loading-spinner-small"></div>
                    ) : (
                        <>
                            <Save size={18} />
                            {mode === 'create' ? 'Create Account' : 'Save Changes'}
                        </>
                    )}
                </button>
            </div>
        </form>
    );
}
