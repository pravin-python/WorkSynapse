import React, { useState } from 'react';
import { FormModal } from '../../../components/ui/modals/FormModal';
import { CreateTagPayload, notesService } from '../api/notesService';

interface TagModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const TagModal: React.FC<TagModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const [name, setName] = useState('');
    const [color, setColor] = useState('#10b981'); // Default green
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const payload: CreateTagPayload = { name, color };
            await notesService.createTag(payload);
            setName('');
            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create tag');
        } finally {
            setLoading(false);
        }
    };

    return (
        <FormModal
            isOpen={isOpen}
            onClose={onClose}
            title="Create Tag"
            onSubmit={handleSubmit}
            isLoading={loading}
            submitText="Create Tag"
        >
            <div className="space-y-4">
                {error && (
                    <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        {error}
                    </div>
                )}
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Tag Name
                    </label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-white"
                        placeholder="e.g. Urgent, Ideas, Todo"
                        required
                        autoFocus
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Color
                    </label>
                    <div className="flex gap-2">
                        {['#10b981', '#3b82f6', '#ef4444', '#f59e0b', '#8b5cf6', '#6366f1'].map((c) => (
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
