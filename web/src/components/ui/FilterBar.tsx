import React from 'react';
import { X, Filter } from 'lucide-react';
import { SearchInput } from './SearchInput';
import './FilterBar.css';

interface FilterOption {
    label: string;
    value: string;
}

interface FilterProps {
    type: 'select' | 'text';
    placeholder?: string;
    options?: FilterOption[];
    value: string;
    onChange: (value: string) => void;
    icon?: React.ElementType;
}

interface FilterBarProps {
    onSearch?: (query: string) => void;
    searchPlaceholder?: string;
    filters?: FilterProps[];
    onReset?: () => void;
    className?: string;
}

export function FilterBar({
    onSearch,
    searchPlaceholder = "Search...",
    filters = [],
    onReset,
    className = ""
}: FilterBarProps) {
    return (
        <div className={`filter-bar ${className}`}>
            <div className="filter-bar-left">
                {onSearch && (
                    <SearchInput
                        placeholder={searchPlaceholder}
                        onChange={onSearch}
                        debounceMs={0} // Parent handles debounce via useEffect
                    />
                )}

                {filters.map((filter, index) => (
                    <div key={index} className="filter-group">
                        {filter.type === 'select' ? (
                            <select
                                value={filter.value}
                                onChange={(e) => filter.onChange(e.target.value)}
                                className="filter-select"
                            >
                                <option value="">{filter.placeholder || "Select..."}</option>
                                {filter.options?.map(opt => (
                                    <option key={opt.value} value={opt.value}>
                                        {opt.label}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <input
                                type="text"
                                value={filter.value}
                                onChange={(e) => filter.onChange(e.target.value)}
                                placeholder={filter.placeholder}
                                className="filter-input"
                            />
                        )}
                        <Filter size={14} className="filter-icon-indicator" />
                    </div>
                ))}
            </div>

            {onReset && (
                <button onClick={onReset} className="filter-reset-btn">
                    <X size={14} />
                    <span>Reset Filters</span>
                </button>
            )}
        </div>
    );
}
