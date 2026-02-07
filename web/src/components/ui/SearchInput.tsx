import React, { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';
import './SearchInput.css';

interface SearchInputProps {
    value?: string;
    onChange?: (value: string) => void;
    onSearch?: (value: string) => void;
    placeholder?: string;
    debounceMs?: number;
    className?: string;
    disabled?: boolean;
    autoFocus?: boolean;
    endAdornment?: React.ReactNode;
}

export const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(({
    value = '',
    onChange,
    onSearch,
    placeholder = "Search...",
    debounceMs = 300,
    className = "",
    disabled = false,
    autoFocus = false,
    endAdornment
}, ref) => {
    const [localValue, setLocalValue] = useState(value);
    const [isFocused, setIsFocused] = useState(false);
    const internalInputRef = useRef<HTMLInputElement>(null);
    const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

    // Use internal ref if external ref is not provided, or merge them if necessary
    // Simpler approach: use useImperativeHandle to expose the internal ref to the parent
    React.useImperativeHandle(ref, () => internalInputRef.current as HTMLInputElement);

    // Sync specific value prop changes to local state
    useEffect(() => {
        if (value !== undefined && value !== localValue) {
            setLocalValue(value);
        }
    }, [value]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value;
        setLocalValue(newValue);

        // Immediate update for controlled inputs
        if (onChange) {
            onChange(newValue);
        }

        // Debounced search trigger
        if (onSearch) {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
            debounceTimerRef.current = setTimeout(() => {
                onSearch(newValue);
            }, debounceMs);
        }
    };

    const handleClear = () => {
        setLocalValue('');
        if (onChange) onChange('');
        if (onSearch) onSearch('');
        internalInputRef.current?.focus();
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && onSearch) {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
            onSearch(localValue);
        }
    };

    return (
        <div
            className={`search-input-container ${className}`} // Removed isFocused/disabled from container classes as styling moves to input
        >
            <Search size={18} className="search-icon-svg" />

            <input
                ref={internalInputRef}
                type="text"
                className={`search-input-field ${isFocused ? 'focused' : ''} ${disabled ? 'disabled' : ''}`}
                value={localValue}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder={placeholder}
                disabled={disabled}
                autoFocus={autoFocus}
            />

            {localValue && !disabled && (
                <button
                    className="search-clear-btn"
                    onClick={(e) => {
                        e.stopPropagation();
                        handleClear();
                    }}
                    type="button"
                    aria-label="Clear search"
                >
                    <X size={14} />
                </button>
            )}

            {endAdornment && !localValue && (
                <div className="search-end-adornment">
                    {endAdornment}
                </div>
            )}
        </div>
    );
});

SearchInput.displayName = 'SearchInput';
