/**
 * WorkSynapse Theme Switcher Component
 * =====================================
 * Beautiful real-time theme switching with preview dots.
 */
import React, { useState } from 'react';
import { useTheme, ThemeName, THEMES } from '../../context/ThemeContext';
import { Sun, Moon, Palette, ChevronDown } from 'lucide-react';
import './ThemeSwitcher.css';

interface ThemeSwitcherProps {
    variant?: 'compact' | 'full' | 'dropdown';
}

export function ThemeSwitcher({ variant = 'compact' }: ThemeSwitcherProps) {
    const { theme, setTheme, isDark, toggleDarkMode, themes } = useTheme();
    const [isOpen, setIsOpen] = useState(false);

    if (variant === 'compact') {
        return (
            <div className="theme-switcher-compact">
                {/* Dark/Light Toggle */}
                <button
                    className="theme-toggle-btn"
                    onClick={toggleDarkMode}
                    title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                    {isDark ? <Sun size={18} /> : <Moon size={18} />}
                </button>

                {/* Theme Palette */}
                <div className="theme-dots">
                    {themes.map((t) => (
                        <button
                            key={t.name}
                            className={`theme-dot ${theme === t.name ? 'active' : ''}`}
                            data-theme={t.name}
                            onClick={() => setTheme(t.name)}
                            title={t.label}
                        />
                    ))}
                </div>
            </div>
        );
    }

    if (variant === 'dropdown') {
        return (
            <div className="theme-switcher-dropdown">
                <button
                    className="theme-dropdown-trigger"
                    onClick={() => setIsOpen(!isOpen)}
                >
                    <Palette size={18} />
                    <span>{THEMES.find(t => t.name === theme)?.label}</span>
                    <ChevronDown size={14} className={isOpen ? 'rotate' : ''} />
                </button>

                {isOpen && (
                    <div className="theme-dropdown-menu">
                        {themes.map((t) => (
                            <button
                                key={t.name}
                                className={`theme-dropdown-item ${theme === t.name ? 'active' : ''}`}
                                onClick={() => {
                                    setTheme(t.name);
                                    setIsOpen(false);
                                }}
                            >
                                <span className="theme-item-icon">{t.icon}</span>
                                <div className="theme-item-content">
                                    <span className="theme-item-label">{t.label}</span>
                                    <span className="theme-item-desc">{t.description}</span>
                                </div>
                                {theme === t.name && (
                                    <span className="theme-item-check">✓</span>
                                )}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    // Full variant
    return (
        <div className="theme-switcher-full">
            <h3 className="theme-switcher-title">Theme</h3>
            <div className="theme-grid">
                {themes.map((t) => (
                    <button
                        key={t.name}
                        className={`theme-card ${theme === t.name ? 'active' : ''}`}
                        onClick={() => setTheme(t.name)}
                    >
                        <div className="theme-card-preview" data-theme={t.name}>
                            <div className="preview-sidebar"></div>
                            <div className="preview-content">
                                <div className="preview-bar"></div>
                                <div className="preview-cards">
                                    <div className="preview-card"></div>
                                    <div className="preview-card"></div>
                                </div>
                            </div>
                        </div>
                        <div className="theme-card-info">
                            <span className="theme-card-icon">{t.icon}</span>
                            <span className="theme-card-label">{t.label}</span>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
}

export default ThemeSwitcher;
