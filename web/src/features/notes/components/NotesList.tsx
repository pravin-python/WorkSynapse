import React from 'react';
import { Note } from '../api/notesService';
import { FileText, Plus } from 'lucide-react';
import { NoteCard } from './NoteCard';
import { formatDistanceToNow } from 'date-fns';
import { Star, Folder } from 'lucide-react';

interface NotesListProps {
    notes: Note[];
    selectedNoteId: number | null;
    onSelectNote: (note: Note) => void;
    onToggleStar: (e: React.MouseEvent, note: Note) => void;
    onDeleteNote: (e: React.MouseEvent, noteId: number) => void;
    onShareNote: (e: React.MouseEvent, note: Note) => void;
    viewMode: 'grid' | 'list';
    onCreateNote?: () => void;
}

export const NotesList: React.FC<NotesListProps> = ({
    notes,
    selectedNoteId,
    onSelectNote,
    onToggleStar,
    onDeleteNote,
    onShareNote,
    viewMode,
    onCreateNote
}) => {

    if (notes.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4 text-gray-300 dark:text-gray-600">
                    <FileText size={32} />
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">No notes found</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 max-w-xs text-center">
                    Get started by creating a new note or try adjusting your filters.
                </p>
                {onCreateNote && (
                    <button
                        onClick={onCreateNote}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        <Plus size={16} />
                        Create Note
                    </button>
                )}
            </div>
        );
    }

    if (viewMode === 'list') {
        return (
            <div className="flex flex-col h-full overflow-y-auto">
                <div className="sticky top-0 z-10 grid grid-cols-12 gap-4 px-6 py-3 bg-gray-50/90 dark:bg-gray-900/90 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <div className="col-span-6 md:col-span-5">Title</div>
                    <div className="col-span-3 hidden md:block">Folder</div>
                    <div className="col-span-3 hidden lg:block">Tags</div>
                    <div className="col-span-3 md:col-span-2 lg:col-span-1 text-right">Updated</div>
                </div>
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                    {notes.map(note => (
                        <div
                            key={note.id}
                            onClick={() => onSelectNote(note)}
                            className={`group grid grid-cols-12 gap-4 px-6 py-3 items-center cursor-pointer transition-colors ${selectedNoteId === note.id
                                ? 'bg-indigo-50/50 dark:bg-indigo-900/10'
                                : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                                }`}
                        >
                            <div className="col-span-6 md:col-span-5 flex items-center gap-3 overflow-hidden">
                                <button
                                    onClick={(e) => onToggleStar(e, note)}
                                    className={`flex-shrink-0 transition-colors ${note.is_starred ? 'text-amber-400 fill-amber-400' : 'text-gray-300 hover:text-amber-400'}`}
                                >
                                    <Star size={16} fill={note.is_starred ? "currentColor" : "none"} />
                                </button>
                                <span className={`truncate font-medium ${selectedNoteId === note.id ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-900 dark:text-gray-100'}`}>
                                    {note.title || 'Untitled'}
                                </span>
                            </div>

                            <div className="col-span-3 hidden md:flex items-center text-sm text-gray-500">
                                {note.folder && (
                                    <div className="flex items-center gap-2 max-w-full">
                                        <Folder size={14} className="flex-shrink-0" style={{ color: note.folder.color || '#9ca3af' }} />
                                        <span className="truncate">{note.folder.name}</span>
                                    </div>
                                )}
                            </div>

                            <div className="col-span-3 hidden lg:flex items-center gap-1 flex-wrap">
                                {note.tags && note.tags.slice(0, 2).map(tag => (
                                    <span
                                        key={tag.id}
                                        className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium"
                                        style={{ backgroundColor: tag.color ? `${tag.color}20` : '#e5e7eb', color: tag.color || '#374151' }}
                                    >
                                        {tag.name}
                                    </span>
                                ))}
                                {note.tags && note.tags.length > 2 && (
                                    <span className="text-[10px] text-gray-400">+{note.tags.length - 2}</span>
                                )}
                            </div>

                            <div className="col-span-3 md:col-span-2 lg:col-span-1 text-right text-xs text-gray-400 whitespace-nowrap">
                                {formatDistanceToNow(new Date(note.updated_at), { addSuffix: true })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6 p-6 pb-20 overflow-y-auto h-full place-content-start">
            {notes.map(note => (
                <NoteCard
                    key={note.id}
                    note={note}
                    isSelected={selectedNoteId === note.id}
                    onClick={() => onSelectNote(note)}
                    onToggleStar={onToggleStar}
                    onDelete={onDeleteNote}
                    onShare={onShareNote}
                />
            ))}
        </div>
    );
};
