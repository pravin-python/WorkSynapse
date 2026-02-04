/**
 * WorkSynapse Register Page
 * =========================
 * New user registration with comprehensive validation.
 */
import React, { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { validateForm, registerSchema } from '../../utils/validation';
import { Mail, Lock, Eye, EyeOff, User, UserPlus, AlertCircle, Check } from 'lucide-react';
import ThemeSwitcher from '../../components/ui/ThemeSwitcher';
import './Auth.css';

export function RegisterPage() {
    const navigate = useNavigate();
    const { register } = useAuth();

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirm_password: '',
        full_name: '',
        username: '',
    });
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [serverError, setServerError] = useState('');

    // Password strength indicators
    const passwordChecks = {
        length: formData.password.length >= 8,
        uppercase: /[A-Z]/.test(formData.password),
        lowercase: /[a-z]/.test(formData.password),
        number: /\d/.test(formData.password),
        special: /[@$!%*?&]/.test(formData.password),
    };
    const passwordStrength = Object.values(passwordChecks).filter(Boolean).length;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));

        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
        setServerError('');
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();

        const validation = validateForm(formData, registerSchema);
        if (!validation.isValid) {
            setErrors(validation.fieldErrors);
            return;
        }

        setIsSubmitting(true);
        setServerError('');

        try {
            await register({
                email: formData.email,
                password: formData.password,
                full_name: formData.full_name,
                username: formData.username || undefined,
            });
            navigate('/dashboard', { replace: true });
        } catch (error: any) {
            setServerError(error.message || 'Registration failed. Please try again.');
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
                        <h1>Create your account</h1>
                        <p>Start your 14-day free trial, no credit card required</p>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        {serverError && (
                            <div className="error-banner">
                                <AlertCircle size={18} />
                                <span>{serverError}</span>
                            </div>
                        )}

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="full_name" className="form-label">Full Name</label>
                                <div className={`input-wrapper ${errors.full_name ? 'error' : ''}`}>
                                    <User size={18} />
                                    <input
                                        type="text"
                                        id="full_name"
                                        name="full_name"
                                        value={formData.full_name}
                                        onChange={handleChange}
                                        placeholder="John Doe"
                                        autoComplete="name"
                                        autoFocus
                                    />
                                </div>
                                {errors.full_name && (
                                    <span className="field-error">{errors.full_name}</span>
                                )}
                            </div>

                            <div className="form-group">
                                <label htmlFor="username" className="form-label">
                                    Username <span className="optional">(optional)</span>
                                </label>
                                <div className={`input-wrapper ${errors.username ? 'error' : ''}`}>
                                    <span className="at-symbol">@</span>
                                    <input
                                        type="text"
                                        id="username"
                                        name="username"
                                        value={formData.username}
                                        onChange={handleChange}
                                        placeholder="johndoe"
                                        autoComplete="username"
                                    />
                                </div>
                                {errors.username && (
                                    <span className="field-error">{errors.username}</span>
                                )}
                            </div>
                        </div>

                        <div className="form-group">
                            <label htmlFor="email" className="form-label">Work Email</label>
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
                                />
                            </div>
                            {errors.email && (
                                <span className="field-error">{errors.email}</span>
                            )}
                        </div>

                        <div className="form-group">
                            <label htmlFor="password" className="form-label">Password</label>
                            <div className={`input-wrapper ${errors.password ? 'error' : ''}`}>
                                <Lock size={18} />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    id="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    placeholder="••••••••"
                                    autoComplete="new-password"
                                />
                                <button
                                    type="button"
                                    className="input-addon"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>

                            {/* Password strength indicator */}
                            {formData.password && (
                                <div className="password-strength">
                                    <div className="strength-bar">
                                        <div
                                            className={`strength-fill strength-${passwordStrength}`}
                                            style={{ width: `${(passwordStrength / 5) * 100}%` }}
                                        ></div>
                                    </div>
                                    <div className="strength-checks">
                                        <span className={passwordChecks.length ? 'valid' : ''}>
                                            {passwordChecks.length ? <Check size={12} /> : '○'} 8+ characters
                                        </span>
                                        <span className={passwordChecks.uppercase ? 'valid' : ''}>
                                            {passwordChecks.uppercase ? <Check size={12} /> : '○'} Uppercase
                                        </span>
                                        <span className={passwordChecks.lowercase ? 'valid' : ''}>
                                            {passwordChecks.lowercase ? <Check size={12} /> : '○'} Lowercase
                                        </span>
                                        <span className={passwordChecks.number ? 'valid' : ''}>
                                            {passwordChecks.number ? <Check size={12} /> : '○'} Number
                                        </span>
                                        <span className={passwordChecks.special ? 'valid' : ''}>
                                            {passwordChecks.special ? <Check size={12} /> : '○'} Special char
                                        </span>
                                    </div>
                                </div>
                            )}

                            {errors.password && (
                                <span className="field-error">{errors.password}</span>
                            )}
                        </div>

                        <div className="form-group">
                            <label htmlFor="confirm_password" className="form-label">Confirm Password</label>
                            <div className={`input-wrapper ${errors.confirm_password ? 'error' : ''}`}>
                                <Lock size={18} />
                                <input
                                    type={showConfirmPassword ? 'text' : 'password'}
                                    id="confirm_password"
                                    name="confirm_password"
                                    value={formData.confirm_password}
                                    onChange={handleChange}
                                    placeholder="••••••••"
                                    autoComplete="new-password"
                                />
                                <button
                                    type="button"
                                    className="input-addon"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                >
                                    {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                            {errors.confirm_password && (
                                <span className="field-error">{errors.confirm_password}</span>
                            )}
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
                                    <UserPlus size={18} />
                                    <span>Create account</span>
                                </>
                            )}
                        </button>

                        <p className="terms-text">
                            By creating an account, you agree to our{' '}
                            <Link to="/terms">Terms of Service</Link> and{' '}
                            <Link to="/privacy">Privacy Policy</Link>.
                        </p>
                    </form>

                    <div className="auth-footer">
                        <p>
                            Already have an account?{' '}
                            <Link to="/login" className="form-link">Sign in</Link>
                        </p>
                    </div>

                    <div className="auth-theme">
                        <ThemeSwitcher variant="compact" />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default RegisterPage;
