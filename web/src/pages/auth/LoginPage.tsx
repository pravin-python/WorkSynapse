/**
 * WorkSynapse Login Page
 * ======================
 * Secure JWT authentication with form validation and error handling.
 */
import React, { useState, FormEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { validateForm, loginSchema } from '../../utils/validation';
import { Mail, Lock, Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react';
import ThemeSwitcher from '../../components/ui/ThemeSwitcher';
import './Auth.css';

export function LoginPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { login, isLoading } = useAuth();
    const { theme } = useTheme();

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        remember_me: false,
    });
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [showPassword, setShowPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [serverError, setServerError] = useState('');

    const from = (location.state as any)?.from?.pathname || '/dashboard';

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));

        // Clear field error on change
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
        setServerError('');
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();

        // Validate form
        const validation = validateForm(formData, loginSchema);
        if (!validation.isValid) {
            setErrors(validation.fieldErrors);
            return;
        }

        setIsSubmitting(true);
        setServerError('');

        try {
            await login({
                email: formData.email,
                password: formData.password,
                remember_me: formData.remember_me,
            });
            navigate(from, { replace: true });
        } catch (error: any) {
            setServerError(error.message || 'Invalid email or password');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-background">
                <div className="bg-gradient"></div>
                <div className="bg-grid"></div>
            </div>

            <div className="auth-container">
                <div className="auth-card">
                    <div className="auth-header">
                        <div className="auth-logo">
                            <div className="logo-icon">W</div>
                            <span className="logo-text">WorkSynapse</span>
                        </div>
                        <h1>Welcome back</h1>
                        <p>Sign in to continue to your workspace</p>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        {serverError && (
                            <div className="error-banner">
                                <AlertCircle size={18} />
                                <span>{serverError}</span>
                            </div>
                        )}

                        <div className="form-group">
                            <label htmlFor="email" className="form-label">Email</label>
                            <div className={`input-wrapper ${errors.email ? 'error' : ''}`}>
                                <Mail size={18} />
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    placeholder="you@company.com"
                                    autoComplete="email"
                                    autoFocus
                                    aria-invalid={!!errors.email}
                                    aria-describedby={errors.email ? 'email-error' : undefined}
                                />
                            </div>
                            {errors.email && (
                                <span id="email-error" className="field-error">{errors.email}</span>
                            )}
                        </div>

                        <div className="form-group">
                            <div className="form-label-row">
                                <label htmlFor="password" className="form-label">Password</label>
                                <Link to="/forgot-password" className="form-link">Forgot password?</Link>
                            </div>
                            <div className={`input-wrapper ${errors.password ? 'error' : ''}`}>
                                <Lock size={18} />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    id="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    placeholder="••••••••"
                                    autoComplete="current-password"
                                    aria-invalid={!!errors.password}
                                    aria-describedby={errors.password ? 'password-error' : undefined}
                                />
                                <button
                                    type="button"
                                    className="input-addon"
                                    onClick={() => setShowPassword(!showPassword)}
                                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                            {errors.password && (
                                <span id="password-error" className="field-error">{errors.password}</span>
                            )}
                        </div>

                        <div className="form-group checkbox-group">
                            <label className="checkbox-label">
                                <input
                                    type="checkbox"
                                    name="remember_me"
                                    checked={formData.remember_me}
                                    onChange={handleChange}
                                />
                                <span className="checkbox-custom"></span>
                                <span>Remember me for 30 days</span>
                            </label>
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary btn-full"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? (
                                <span className="loading-spinner"></span>
                            ) : (
                                <>
                                    <LogIn size={18} />
                                    <span>Sign in</span>
                                </>
                            )}
                        </button>
                    </form>

                    <div className="auth-footer">
                        <p>
                            Don't have an account?{' '}
                            <Link to="/register" className="form-link">Sign up</Link>
                        </p>
                    </div>

                    <div className="auth-theme">
                        <ThemeSwitcher variant="compact" />
                    </div>
                </div>

                <div className="auth-features">
                    <h2>AI-Powered Workspace</h2>
                    <ul className="feature-list">
                        <li>
                            <span className="feature-icon">🤖</span>
                            <div>
                                <strong>AI Project Manager</strong>
                                <span>Automate project planning and task generation</span>
                            </div>
                        </li>
                        <li>
                            <span className="feature-icon">⏱️</span>
                            <div>
                                <strong>Smart Time Tracking</strong>
                                <span>Automatic work detection and productivity insights</span>
                            </div>
                        </li>
                        <li>
                            <span className="feature-icon">💬</span>
                            <div>
                                <strong>Real-time Collaboration</strong>
                                <span>Secure team chat with instant messaging</span>
                            </div>
                        </li>
                        <li>
                            <span className="feature-icon">🔒</span>
                            <div>
                                <strong>Enterprise Security</strong>
                                <span>JWT auth, RBAC, and anti-replay protection</span>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

export default LoginPage;
