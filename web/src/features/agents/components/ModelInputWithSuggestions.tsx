import React, { useState, useEffect, useRef } from 'react';
import './ModelInputWithSuggestions.css';

interface Suggestion {
    id: number | string;
    name: string;
    description?: string;
    meta?: string;
}

interface ModelInputWithSuggestionsProps {
    suggestions: Suggestion[];
    value: string; // Display value (name)
    onSelect: (item: Suggestion) => void;
    onChange: (text: string) => void;
    placeholder?: string;
    disabled?: boolean;
}

export const ModelInputWithSuggestions: React.FC<ModelInputWithSuggestionsProps> = ({
    suggestions,
    value,
    onSelect,
    onChange,
    placeholder = "Type to search...",
    disabled = false
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange(e.target.value);
        setIsOpen(true);
    };

    const handleSelect = (item: Suggestion) => {
        onSelect(item);
        setIsOpen(false);
    };

    // Filter suggestions based on input value if not exactly matching
    const filteredSuggestions = suggestions.filter(item =>
        item.name.toLowerCase().includes(value.toLowerCase())
    );

    return (
        <div className="model-suggestion-container" ref={wrapperRef}>
            <div className="model-input-wrapper">
                <input
                    type="text"
                    className="model-input"
                    value={value}
                    onChange={handleInputChange}
                    onFocus={() => setIsOpen(true)}
                    placeholder={placeholder}
                    disabled={disabled}
                />
            </div>

            {isOpen && !disabled && (
                <div className="suggestions-dropdown">
                    {filteredSuggestions.length > 0 ? (
                        filteredSuggestions.map((item) => (
                            <div
                                key={item.id}
                                className="suggestion-item"
                                onClick={() => handleSelect(item)}
                            >
                                <span className="model-name">{item.name}</span>
                                {item.meta && <span className="model-meta">{item.meta}</span>}
                            </div>
                        ))
                    ) : (
                        <div className="no-suggestions">
                            No matching models found.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
