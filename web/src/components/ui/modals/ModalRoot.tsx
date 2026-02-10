import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import './ModalRoot.css';
import { createPortal } from 'react-dom';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title?: React.ReactNode;
    children: React.ReactNode;
    size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
    footer?: React.ReactNode;
    closeOnOverlayClick?: boolean;
    showCloseButton?: boolean;
    className?: string;
}

export function Modal({
    isOpen,
    onClose,
    title,
    children,
    size = 'md',
    footer,
    closeOnOverlayClick = true,
    showCloseButton = true,
    className = ''
}: ModalProps) {
    const [isVisible, setIsVisible] = useState(false);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
            document.body.style.overflow = 'hidden';
        } else {
            const timer = setTimeout(() => setIsVisible(false), 200);
            document.body.style.overflow = '';
            return () => clearTimeout(timer);
        }

        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [isOpen, onClose]);

    if (!mounted) return null;

    if (!isVisible && !isOpen) return null;

    const content = (
        <div
            className={`modal-overlay ${isOpen ? 'open' : ''}`}
            onClick={closeOnOverlayClick ? onClose : undefined}
            style={{ zIndex: 1000 }} // Ensure it's on top
        >
            <div
                className={`modal-container modal-${size} ${className}`}
                onClick={e => e.stopPropagation()}
                role="dialog"
                aria-modal="true"
            >
                {(title || showCloseButton) && (
                    <div className="modal-header">
                        {title ? <h3>{title}</h3> : <div />}
                        {showCloseButton && (
                            <button className="modal-close" onClick={onClose} aria-label="Close modal">
                                <X size={20} />
                            </button>
                        )}
                    </div>
                )}

                <div className="modal-content">
                    {children}
                </div>

                {footer && (
                    <div className="modal-footer">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    );

    return createPortal(content, document.body);
}
