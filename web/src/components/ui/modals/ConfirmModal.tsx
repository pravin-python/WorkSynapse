import { Modal } from './ModalRoot';
import { AlertTriangle } from 'lucide-react';

interface ConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title?: string;
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
    title = 'Confirm Action',
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    isDestructive = false,
    isLoading = false
}: ConfirmModalProps) {

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isDestructive && <AlertTriangle size={20} style={{ color: 'hsl(var(--color-error))' }} />}
                    <span>{title}</span>
                </div>
            }
            size="sm"
            footer={
                <>
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
                </>
            }
        >
            <p style={{ margin: 0, color: 'hsl(var(--color-text-muted))', lineHeight: 1.5 }}>
                {message}
            </p>
        </Modal>
    );
}
