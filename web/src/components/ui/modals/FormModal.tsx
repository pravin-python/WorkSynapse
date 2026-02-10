import React from 'react';
import { Modal } from './ModalRoot';

interface FormModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    onSubmit: (e: React.FormEvent) => void;
    size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
    isLoading?: boolean;
    submitText?: string;
    cancelText?: string;
    isSubmitDisabled?: boolean;
    className?: string;
}

export function FormModal({
    isOpen,
    onClose,
    title,
    children,
    onSubmit,
    size = 'md',
    isLoading = false,
    submitText = 'Save',
    cancelText = 'Cancel',
    isSubmitDisabled = false,
    className = ''
}: FormModalProps) {
    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={title}
            size={size}
            className={className}
            footer={
                <>
                    <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        {cancelText}
                    </button>
                    <button
                        type="submit"
                        form="modal-form"
                        className="btn btn-primary"
                        disabled={isSubmitDisabled || isLoading}
                    >
                        {isLoading ? <div className="loading-spinner-small"></div> : submitText}
                    </button>
                </>
            }
        >
            <form
                id="modal-form"
                onSubmit={onSubmit}
                style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
            >
                {children}
            </form>
        </Modal>
    );
}
