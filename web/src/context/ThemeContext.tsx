/**
 * WorkSynapse Theme Context
 * =========================
 * Provides real-time theme switching with 6 premium themes.
 * Persists user preference to localStorage.
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Available themes
export type ThemeName = 'minimalist' | 'bento' | 'retro' | 'brutalist' | 'pastel' | 'neon';

export interface ThemeInfo {
    name: ThemeName;
    label: string;
    description: string;
    icon: string;
    type: 'light' | 'dark';
}

export const THEMES: ThemeInfo[] = [
    {
        name: 'minimalist',
        label: 'Minimalist',
        description: 'Clean and modern with high whitespace',
        icon: '☀️',
        type: 'light',
    },
    {
        name: 'bento',
        label: 'Bento Box',
        description: 'Modern tile layout with iOS-style cards',
        icon: '🍱',
        type: 'dark',
    },
    {
        name: 'retro',
        label: 'Retro',
        description: '80s nostalgia with pixel fonts and sepia tones',
        icon: '🕹️',
        type: 'light',
    },
    {
        name: 'brutalist',
        label: 'Brutalist',
        description: 'Bold, sharp contrast with big typography',
        icon: '🏛️',
        type: 'light',
    },
    {
        name: 'pastel',
        label: 'Pastel',
        description: 'Soothing muted luxury tones',
        icon: '🌸',
        type: 'light',
    },
    {
        name: 'neon',
        label: 'Neon Futurist',
        description: 'Cyberpunk electric purple and green on black',
        icon: '🌃',
        type: 'dark',
    },
];

// Context interface
interface ThemeContextType {
    theme: ThemeName;
    themeInfo: ThemeInfo;
    setTheme: (theme: ThemeName) => void;
    toggleDarkMode: () => void;
    isDark: boolean;
    themes: ThemeInfo[];
}

// Create context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Storage key
const THEME_STORAGE_KEY = 'worksynapse-theme';

// Provider component
interface ThemeProviderProps {
    children: ReactNode;
    defaultTheme?: ThemeName;
}

export function ThemeProvider({ children, defaultTheme = 'bento' }: ThemeProviderProps) {
    // Initialize from localStorage or default
    const [theme, setThemeState] = useState<ThemeName>(() => {
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem(THEME_STORAGE_KEY);
            if (stored && THEMES.some(t => t.name === stored)) {
                return stored as ThemeName;
            }
        }
        return defaultTheme;
    });

    // Get current theme info
    const themeInfo = THEMES.find(t => t.name === theme) || THEMES[0];

    // Apply theme to document
    useEffect(() => {
        const root = document.documentElement;

        // Remove all theme classes
        THEMES.forEach(t => {
            root.classList.remove(`theme-${t.name}`);
        });

        // Set data attribute for CSS selectors
        root.setAttribute('data-theme', theme);

        // Add theme class
        root.classList.add(`theme-${theme}`);

        // Update meta color for mobile browsers
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            const colors: Record<ThemeName, string> = {
                minimalist: '#ffffff',
                bento: '#0f0d15',
                retro: '#f5f0e8',
                brutalist: '#ffffff',
                pastel: '#faf8f5',
                neon: '#0d0812',
            };
            metaThemeColor.setAttribute('content', colors[theme]);
        }

        // Persist to localStorage
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    }, [theme]);

    // Set theme function
    const setTheme = (newTheme: ThemeName) => {
        setThemeState(newTheme);
    };

    // Toggle between light and dark themes
    const toggleDarkMode = () => {
        const currentIsDark = themeInfo.type === 'dark';
        if (currentIsDark) {
            // Switch to closest light theme
            setTheme('minimalist');
        } else {
            // Switch to closest dark theme
            setTheme('bento');
        }
    };

    const value: ThemeContextType = {
        theme,
        themeInfo,
        setTheme,
        toggleDarkMode,
        isDark: themeInfo.type === 'dark',
        themes: THEMES,
    };

    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    );
}

// Custom hook for using theme
export function useTheme(): ThemeContextType {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}

// Export theme utilities
export function getThemeInfo(name: ThemeName): ThemeInfo {
    return THEMES.find(t => t.name === name) || THEMES[0];
}
