import React, { useState } from 'react';
import { FormModal } from '../../../components/ui/modals/FormModal';
import { ShareNotePayload, SharePermission, Note, notesService } from '../api/notesService';

interface ShareModalProps {
    isOpen: boolean;
    onClose: () => void;
    note: Note | null;
    onSuccess: () => void;
}

export const ShareModal: React.FC<ShareModalProps> = ({ isOpen, onClose, note, onSuccess }) => {
    const [email, setEmail] = useState('');
    const [permission, setPermission] = useState<SharePermission>(SharePermission.VIEW);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!note) return;

        setLoading(true);
        setError(null);

        try {
            const payload: ShareNotePayload = { email, permission };
            await notesService.shareNote(note.id, payload);
            setEmail('');
            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to share note');
        } finally {
            setLoading(false);
        }
    };

    if (!note) return null;

    return (
        <FormModal
            isOpen={isOpen}
            onClose={onClose}
            title={`Share "${note.title}"`}
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
                        User Email
                    </label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-white"
                        placeholder="colleague@example.com"
                        required
                        autoFocus
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Permission
                    </label>
                    <select
                        value={permission}
                        onChange={(e) => setPermission(e.target.value as SharePermission)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-white"
                    >
                        <option value={SharePermission.VIEW}>View Only</option>
                        <option value={SharePermission.EDIT}>Can Edit</option>
                    </select>
                </div>
            </div>

            {/* List of existing shares could be added here later */}
        </FormModal>
    );
};
