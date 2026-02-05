import React, { useEffect, useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import './ConfirmModal.css';

interface ConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    isDestructive?: boolean;
    isLoading?: boolean;
}

export function ConfirmModal({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    isDestructive = false,
    isLoading = false
}: ConfirmModalProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
            // Lock body scroll
            document.body.style.overflow = 'hidden';
        } else {
            const timer = setTimeout(() => setIsVisible(false), 300);
            document.body.style.overflow = 'unset';
            return () => clearTimeout(timer);
        }
    }, [isOpen]);

    // Handle ESC key
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [isOpen, onClose]);

    if (!isVisible && !isOpen) return null;

    return (
        <div
            className={`modal-overlay ${isOpen ? 'open' : ''}`}
            onClick={onClose}
        >
            <div
                className="modal-container"
                onClick={e => e.stopPropagation()}
            >
                <div className="modal-header">
                    <div className={`modal-icon ${isDestructive ? 'destructive' : ''}`}>
                        <AlertTriangle size={24} />
                    </div>
                    <button className="modal-close" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                <div className="modal-content">
                    <h3>{title}</h3>
                    <p>{message}</p>
                </div>

                <div className="modal-actions">
                    <button
                        className="btn btn-ghost"
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        {cancelText}
                    </button>
                    <button
                        className={`btn ${isDestructive ? 'btn-error' : 'btn-primary'}`}
                        onClick={onConfirm}
                        disabled={isLoading}
                    >
                        {isLoading ? <div className="loading-spinner-small"></div> : confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
}
