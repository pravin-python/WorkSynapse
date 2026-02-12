import React from 'react';
import { Note } from '../api/notesService';
import { Star, Clock, Share2, Trash2, Folder } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface NoteCardProps {
    note: Note;
    isSelected: boolean;
    onClick: () => void;
    onToggleStar: (e: React.MouseEvent, note: Note) => void;
    onDelete: (e: React.MouseEvent, noteId: number) => void;
    onShare: (e: React.MouseEvent, note: Note) => void;
}

export const NoteCard: React.FC<NoteCardProps> = ({
    note,
    isSelected,
    onClick,
    onToggleStar,
    onDelete,
    onShare
}) => {
    return (
        <div
            onClick={onClick}
            className={`group relative flex flex-col p-5 rounded-2xl border transition-all duration-200 cursor-pointer h-64 ${isSelected
                ? 'bg-white dark:bg-gray-800 border-indigo-500 ring-1 ring-indigo-500 shadow-md transform scale-[1.02]'
                : 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 hover:shadow-xl hover:-translate-y-1 hover:border-gray-200 dark:hover:border-gray-600'
                }`}
        >
            <div className="flex justify-between items-start mb-3">
                <div className="flex-1 pr-8">
                    {note.folder && (
                        <div className="flex items-center gap-1.5 text-xs font-medium text-gray-400 dark:text-gray-500 mb-1.5">
                            <Folder size={12} className={note.folder.color ? '' : 'text-gray-400'} style={{ color: note.folder.color }} />
                            <span className="truncate max-w-[120px]">{note.folder.name}</span>
                        </div>
                    )}
                    <h3 className={`font-semibold text-lg line-clamp-1 ${isSelected ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-900 dark:text-gray-100'}`}>
                        {note.title || 'Untitled'}
                    </h3>
                </div>
                <button
                    onClick={(e) => onToggleStar(e, note)}
                    className={`absolute top-5 right-5 p-1 rounded-full transition-colors ${note.is_starred
                        ? 'text-amber-400 fill-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20'
                        : 'text-gray-300 dark:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-amber-400'
                        }`}
                >
                    <Star size={18} fill={note.is_starred ? "currentColor" : "none"} />
                </button>
            </div>

            <div className="flex-1 overflow-hidden relative mb-4">
                <p className="text-sm text-gray-500 dark:text-gray-400 whitespace-pre-wrap line-clamp-5 leading-relaxed">
                    {note.content || <span className="italic opacity-50">No additional text</span>}
                </p>
                <div className="absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t from-white dark:from-gray-800 to-transparent pointer-events-none" />
            </div>

            <div className="mt-auto pt-3 border-t border-gray-50 dark:border-gray-700/50 flex flex-col gap-3">
                {/* Tags */}
                {note.tags && note.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 min-h-[20px]">
                        {note.tags.slice(0, 3).map(tag => (
                            <span
                                key={tag.id}
                                className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase"
                                style={{
                                    backgroundColor: tag.color ? `${tag.color}15` : '#f3f4f6',
                                    color: tag.color || '#4b5563'
                                }}
                            >
                                {tag.name}
                            </span>
                        ))}
                        {note.tags.length > 3 && (
                            <span className="text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-500 px-1.5 py-0.5 rounded-full">+{note.tags.length - 3}</span>
                        )}
                    </div>
                )}

                <div className="flex items-center justify-between text-xs text-gray-400 font-medium">
                    <span className="flex items-center gap-1.5">
                        <Clock size={12} />
                        {formatDistanceToNow(new Date(note.updated_at), { addSuffix: true })}
                    </span>

                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all transform translate-y-2 group-hover:translate-y-0">
                        <button
                            onClick={(e) => onShare(e, note)}
                            className="p-1.5 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded text-gray-400 hover:text-indigo-600 transition-colors"
                            title="Share"
                        >
                            <Share2 size={14} />
                        </button>
                        <button
                            onClick={(e) => onDelete(e, note.id)}
                            className="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/30 rounded text-gray-400 hover:text-red-600 transition-colors"
                            title="Delete"
                        >
                            <Trash2 size={14} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
