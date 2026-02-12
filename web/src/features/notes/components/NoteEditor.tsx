import React, { useState, useEffect } from 'react';
import { Note, UpdateNotePayload, NoteFolder, NoteTag, notesService } from '../api/notesService';
import { Save, Folder, Tag as TagIcon, X, Share2, Star } from 'lucide-react';
import { ShareModal } from './ShareModal';
import { formatDistanceToNow } from 'date-fns';

interface NoteEditorProps {
    note: Note | null;
    folders: NoteFolder[];
    tags: NoteTag[];
    onClose: () => void;
    onUpdate: () => void;
}

export const NoteEditor: React.FC<NoteEditorProps> = ({
    note: initialNote,
    folders,
    tags: availableTags,
    onClose,
    onUpdate
}) => {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
    const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
    const [isStarred, setIsStarred] = useState(false);

    const [isSaving, setIsSaving] = useState(false);
    const [isShareModalOpen, setIsShareModalOpen] = useState(false);
    const [localNote, setLocalNote] = useState<Note | null>(null);

    // Initialize state when note changes
    useEffect(() => {
        if (initialNote) {
            setLocalNote(initialNote);
            setTitle(initialNote.title);
            setContent(initialNote.content || '');
            setSelectedFolderId(initialNote.folder_id || null);
            setSelectedTagIds(initialNote.tags.map(t => t.id));
            setIsStarred(initialNote.is_starred);
        } else {
            setLocalNote(null);
        }
    }, [initialNote]);

    if (!localNote) return null;

    const handleSave = async () => {
        if (!localNote) return;
        setIsSaving(true);
        try {
            const payload: UpdateNotePayload = {
                title,
                content,
                folder_id: selectedFolderId || undefined,
                tag_ids: selectedTagIds,
                is_starred: isStarred
            };
            await notesService.updateNote(localNote.id, payload);
            if (onUpdate) onUpdate();
        } catch (error) {
            console.error('Failed to save note', error);
        } finally {
            setIsSaving(false);
        }
    };

    const toggleTag = (tagId: number) => {
        setSelectedTagIds(prev =>
            prev.includes(tagId)
                ? prev.filter(id => id !== tagId)
                : [...prev, tagId]
        );
    };

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900 shadow-xl border-l border-gray-200 dark:border-gray-800">
            {/* Header / Toolbar */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-gray-100 dark:border-gray-800 shrink-0">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer relative">
                        <Folder size={14} className={selectedFolderId ? 'text-indigo-500' : 'text-gray-400'} />
                        <select
                            value={selectedFolderId || ''}
                            onChange={(e) => setSelectedFolderId(e.target.value ? Number(e.target.value) : null)}
                            className="absolute inset-0 opacity-0 cursor-pointer w-full"
                        >
                            <option value="">Unsorted</option>
                            {folders.map(f => (
                                <option key={f.id} value={f.id}>{f.name}</option>
                            ))}
                        </select>
                        <span className="max-w-[150px] truncate font-medium">
                            {folders.find(f => f.id === selectedFolderId)?.name || 'Unsorted'}
                        </span>
                    </div>

                    <span className="text-gray-300 dark:text-gray-700">|</span>

                    <span className="text-xs text-gray-400">
                        {isSaving ? 'Saving...' : `Last edited ${formatDistanceToNow(new Date(localNote.updated_at), { addSuffix: true })}`}
                    </span>
                </div>

                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setIsStarred(!isStarred)}
                        className={`p-2 rounded-md transition-colors ${isStarred
                            ? 'text-amber-400 bg-amber-50 dark:bg-amber-900/20'
                            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}
                        title={isStarred ? "Unstar" : "Star"}
                    >
                        <Star size={18} fill={isStarred ? "currentColor" : "none"} />
                    </button>

                    <button
                        onClick={() => setIsShareModalOpen(true)}
                        className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-md transition-colors"
                        title="Share"
                    >
                        <Share2 size={18} />
                    </button>

                    <button
                        onClick={handleSave}
                        className={`p-2 rounded-md transition-colors ${isSaving ? 'text-indigo-500' : 'text-gray-400 hover:text-indigo-600 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
                        title="Save"
                    >
                        <Save size={18} />
                    </button>

                    <div className="h-4 w-px bg-gray-200 dark:bg-gray-700 mx-1" />

                    <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md text-gray-400 hover:text-gray-600" title="Close">
                        <X size={20} />
                    </button>
                </div>
            </div>

            {/* Editor Content */}
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-3xl mx-auto px-8 py-10">
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Untitled"
                        className="w-full text-4xl font-bold bg-transparent border-none focus:ring-0 placeholder-gray-300 dark:placeholder-gray-700 text-gray-900 dark:text-white mb-6 px-0"
                    />

                    {/* Properties Row */}
                    <div className="flex items-start gap-4 mb-8">
                        <div className="flex items-center gap-2 text-gray-500 w-24 pt-1">
                            <TagIcon size={16} />
                            <span className="text-sm">Tags</span>
                        </div>
                        <div className="flex flex-wrap gap-2 flex-1">
                            {availableTags.map(tag => (
                                <button
                                    key={tag.id}
                                    onClick={() => toggleTag(tag.id)}
                                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${selectedTagIds.includes(tag.id)
                                        ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300 ring-1 ring-indigo-500/30'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
                                        }`}
                                >
                                    {tag.name}
                                </button>
                            ))}
                            {availableTags.length === 0 && (
                                <span className="text-sm text-gray-400 italic">No tags available</span>
                            )}
                        </div>
                    </div>

                    <div className="h-px bg-gray-100 dark:bg-gray-800 mb-8" />

                    <textarea
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        placeholder="Start writing..."
                        className="w-full min-h-[500px] resize-none bg-transparent border-none focus:ring-0 text-lg leading-loose text-gray-800 dark:text-gray-200 px-0 outline-none"
                        spellCheck={false}
                    />
                </div>
            </div>

            <ShareModal
                isOpen={isShareModalOpen}
                onClose={() => setIsShareModalOpen(false)}
                note={localNote}
                onSuccess={onUpdate}
            />
        </div>
    );
};
