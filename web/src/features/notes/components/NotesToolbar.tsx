import React, { useState } from 'react';
import { SearchInput } from '../../../components/ui/SearchInput';
import { NoteTag } from '../api/notesService';
import { Filter, Plus, LayoutGrid, List } from 'lucide-react';
import { TagModal } from './TagModal';

interface NotesToolbarProps {
    onSearch: (query: string) => void;
    selectedTagId: number | null;
    onSelectTag: (tagId: number | null) => void;
    onCreateNote: () => void;
    viewMode: 'grid' | 'list';
    onViewChange: (mode: 'grid' | 'list') => void;
    tags: NoteTag[];
    onTagCreated: () => void;
}

export const NotesToolbar: React.FC<NotesToolbarProps> = ({
    onSearch,
    selectedTagId,
    onSelectTag,
    onCreateNote,
    viewMode,
    onViewChange,
    tags,
    onTagCreated
}) => {
    const [isTagModalOpen, setIsTagModalOpen] = useState(false);

    // Removed internal fetchTags logic

    const selectedTag = tags.find(t => t.id === selectedTagId);

    return (
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md sticky top-0 z-10 transition-all">
            <div className="flex items-center gap-3 flex-1">
                <div className="w-full max-w-[320px]">
                    <SearchInput
                        placeholder="Search notes..."
                        onSearch={onSearch}
                        debounceMs={500}
                    />
                </div>

                <div className="h-6 w-px bg-gray-200 dark:bg-gray-700 mx-1" />

                <div className="relative group">
                    <button className={`flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border transition-all ${selectedTagId
                        ? 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-900/20 dark:border-indigo-800 dark:text-indigo-400'
                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700'
                        }`}>
                        <Filter size={14} />
                        <span>{selectedTag ? selectedTag.name : 'Filter'}</span>
                    </button>

                    <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 hidden group-hover:block p-1 z-20 animate-in fade-in zoom-in-95 duration-100 origin-top-left">
                        <div className="mb-1 px-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-100 dark:border-gray-700">
                            Filter by Tag
                        </div>
                        <div className="space-y-0.5 max-h-64 overflow-y-auto">
                            <button
                                onClick={() => onSelectTag(null)}
                                className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${selectedTagId === null
                                    ? 'bg-gray-100 dark:bg-gray-700 font-medium text-gray-900 dark:text-white'
                                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                                    }`}
                            >
                                All Tags
                            </button>
                            {tags.map(tag => (
                                <button
                                    key={tag.id}
                                    onClick={() => onSelectTag(tag.id)}
                                    className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors flex items-center gap-2 ${selectedTagId === tag.id
                                        ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-900/20 dark:text-indigo-400 font-medium'
                                        : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                                        }`}
                                >
                                    <span
                                        className="w-2 h-2 rounded-full flex-shrink-0"
                                        style={{ backgroundColor: tag.color || '#9ca3af' }}
                                    />
                                    <span className="truncate">{tag.name}</span>
                                </button>
                            ))}
                        </div>
                        <div className="border-t border-gray-200 dark:border-gray-700 mt-1 pt-1">
                            <button
                                onClick={() => setIsTagModalOpen(true)}
                                className="w-full text-left px-3 py-2 text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 flex items-center gap-2 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-md transition-colors"
                            >
                                <Plus size={14} /> Create New Tag
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-3">
                <div className="flex items-center bg-gray-100 dark:bg-gray-800 p-1 rounded-lg border border-gray-200 dark:border-gray-700">
                    <button
                        onClick={() => onViewChange('grid')}
                        className={`p-1.5 rounded transition-all ${viewMode === 'grid'
                            ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                            : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                            }`}
                        title="Grid View"
                    >
                        <LayoutGrid size={16} />
                    </button>
                    <button
                        onClick={() => onViewChange('list')}
                        className={`p-1.5 rounded transition-all ${viewMode === 'list'
                            ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                            : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                            }`}
                        title="List View"
                    >
                        <List size={16} />
                    </button>
                </div>

                <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" />

                <button
                    onClick={onCreateNote}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors"
                >
                    <Plus size={16} />
                    <span>New Note</span>
                </button>
            </div>

            <TagModal
                isOpen={isTagModalOpen}
                onClose={() => setIsTagModalOpen(false)}
                onSuccess={onTagCreated}
            />
        </div>
    );
};
