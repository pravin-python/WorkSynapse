import React, { useState } from 'react';
import { FormModal } from '../../../components/ui/modals/FormModal';
import { CreateFolderPayload, notesService } from '../api/notesService';

interface FolderModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const FolderModal: React.FC<FolderModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const [name, setName] = useState('');
    const [color, setColor] = useState('#6366f1'); // Default indigo
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const payload: CreateFolderPayload = { name, color };
            await notesService.createFolder(payload);
            setName('');
            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create folder');
        } finally {
            setLoading(false);
        }
    };

    return (
        <FormModal
            isOpen={isOpen}
            onClose={onClose}
            title="Create Folder"
            onSubmit={handleSubmit}
            isLoading={loading}
        >
            <div className="space-y-4">
                {error && (
                    <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        {error}
                    </div>
                )}
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Folder Name
                    </label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-white"
                        placeholder="e.g. Personal, Work, Ideas"
                        required
                        autoFocus
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Color Tag
                    </label>
                    <div className="flex gap-2">
                        {['#6366f1', '#ef4444', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'].map((c) => (
                            <button
                                key={c}
                                type="button"
                                onClick={() => setColor(c)}
                                className={`w-8 h-8 rounded-full border-2 ${color === c ? 'border-gray-900 dark:border-white' : 'border-transparent'
                                    }`}
                                style={{ backgroundColor: c }}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </FormModal>
    );
};
