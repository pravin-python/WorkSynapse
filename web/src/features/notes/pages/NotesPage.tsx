/**
 * WorkSynapse Notes Page
 * ======================
 * Rich text notes with folders and tags.
 */
import React, { useState, useEffect, useCallback } from 'react';

import './NotesPage.css';
import { FolderSidebar } from '../components/FolderSidebar';
import { NotesList } from '../components/NotesList';
import { NotesToolbar } from '../components/NotesToolbar';
import { NoteEditor } from '../components/NoteEditor';
import {
    notesService,
    Note,
    NoteFolder,
    NoteTag,
    NoteFilterParams,
    CreateNotePayload
} from '../api/notesService';

export function NotesPage() {
    // Data State
    const [notes, setNotes] = useState<Note[]>([]);
    const [folders, setFolders] = useState<NoteFolder[]>([]);
    const [tags, setTags] = useState<NoteTag[]>([]);
    const [selectedNote, setSelectedNote] = useState<Note | null>(null);
    const [loading, setLoading] = useState(false);

    // Filter State
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
    const [selectedTagId, setSelectedTagId] = useState<number | null>(null);
    const [isStarred, setIsStarred] = useState(false);
    const [isShared, setIsShared] = useState(false);

    // UI State
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

    // Fetch methods
    const loadFolders = useCallback(async () => {
        try {
            const data = await notesService.getFolders();
            setFolders(data);
        } catch (error) {
            console.error('Failed to load folders', error);
        }
    }, []);

    const loadTags = useCallback(async () => {
        try {
            const data = await notesService.getTags();
            setTags(data);
        } catch (error) {
            console.error('Failed to load tags', error);
        }
    }, []);

    const loadNotes = useCallback(async () => {
        setLoading(true);
        try {
            const params: NoteFilterParams = {
                search: searchQuery || undefined,
                folder_id: selectedFolderId || undefined,
                tag_id: selectedTagId || undefined,
                is_starred: isStarred || undefined,
                shared: isShared || undefined,
            };
            const data = await notesService.getNotes(params);
            setNotes(data);
        } catch (error) {
            console.error('Failed to load notes', error);
        } finally {
            setLoading(false);
        }
    }, [searchQuery, selectedFolderId, selectedTagId, isStarred, isShared]);

    // Initial load
    useEffect(() => {
        loadFolders();
        loadTags();
    }, [loadFolders, loadTags]);

    // Load notes when filters change
    useEffect(() => {
        loadNotes();
    }, [loadNotes]);

    // Handlers
    const handleSelectFolder = (id: number | null) => {
        setSelectedFolderId(id);
        setIsStarred(false);
        setIsShared(false);
        // If selecting a folder, we might want to keep tag filter? Usually yes.
    };

    const handleSelectStarred = () => {
        setIsStarred(true);
        setSelectedFolderId(null);
        setIsShared(false);
    };

    const handleSelectShared = () => {
        setIsShared(true);
        setSelectedFolderId(null);
        setIsStarred(false);
    };

    const handleSelectAll = () => {
        setSelectedFolderId(null);
        setIsStarred(false);
        setIsShared(false);
        setSelectedTagId(null);
        setSearchQuery('');
    };

    const handleSelectTag = (id: number | null) => {
        setSelectedTagId(id);
    };

    const handleSearch = (query: string) => {
        setSearchQuery(query);
    };

    const handleCreateNote = async () => {
        try {
            const payload: CreateNotePayload = {
                title: 'Untitled Note',
                folder_id: selectedFolderId || undefined
            };
            const newNote = await notesService.createNote(payload);
            setNotes(prev => [newNote, ...prev]);
            setSelectedNote(newNote);
        } catch (error) {
            console.error('Failed to create note', error);
        }
    };

    const handleDeleteNote = async (e: React.MouseEvent, noteId: number) => {
        e.stopPropagation();
        if (window.confirm('Are you sure you want to delete this note?')) {
            try {
                await notesService.deleteNote(noteId);
                setNotes(prev => prev.filter(n => n.id !== noteId));
                if (selectedNote?.id === noteId) {
                    setSelectedNote(null);
                }
            } catch (error) {
                console.error('Failed to delete note', error);
            }
        }
    };

    const handleToggleStar = async (e: React.MouseEvent, note: Note) => {
        e.stopPropagation();
        // Optimistic update
        const updatedNote = { ...note, is_starred: !note.is_starred };
        setNotes(prev => prev.map(n => n.id === note.id ? updatedNote : n));
        if (selectedNote?.id === note.id) {
            setSelectedNote(updatedNote);
        }

        try {
            await notesService.toggleNoteStar(note.id, !note.is_starred);
        } catch (error) {
            // Revert
            console.error('Failed to toggle star', error);
            setNotes(prev => prev.map(n => n.id === note.id ? note : n));
            if (selectedNote?.id === note.id) {
                setSelectedNote(note);
            }
        }
    };

    const handleUpdateNote = () => {
        loadNotes(); // Reload list to reflect changes (e.g. title, preview)
        // Update selected note in list if needed, or rely on reload.
        // Also refresh tags/folders if create modal used, but here it is Note update.
    };

    // Derived state for selection callbacks
    // FolderSidebar props
    const folderSidebarProps = {
        folders,
        selectedFolderId,
        isStarred,
        isShared,
        onSelectFolder: handleSelectFolder,
        onSelectStarred: handleSelectStarred,
        onSelectShared: handleSelectShared,
        onSelectAll: handleSelectAll,
        onFolderCreated: loadFolders,
        onFolderDeleted: loadFolders
    };

    return (
        <div className="flex h-full bg-white dark:bg-black overflow-hidden">
            {/* Sidebar */}
            <FolderSidebar {...folderSidebarProps} />

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-black">
                {/* Toolbar */}
                <NotesToolbar
                    onSearch={handleSearch}
                    selectedTagId={selectedTagId}
                    onSelectTag={handleSelectTag}
                    onCreateNote={handleCreateNote}
                    viewMode={viewMode}
                    onViewChange={setViewMode}
                    tags={tags}
                    onTagCreated={loadTags}
                />

                {/* Notes List */}
                <div className="flex-1 overflow-hidden relative">
                    {loading && notes.length === 0 ? (
                        <div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-black/50 z-10">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        </div>
                    ) : (
                        <NotesList
                            notes={notes}
                            selectedNoteId={selectedNote?.id || null}
                            onSelectNote={setSelectedNote}
                            onToggleStar={handleToggleStar}
                            onDeleteNote={handleDeleteNote}
                            onShareNote={(e, note) => {
                                e.stopPropagation();
                                console.log('Share not implemented in list view yet', note.id);
                            }}
                            viewMode={viewMode}
                            onCreateNote={handleCreateNote}
                        />
                    )}
                </div>
            </div>

            {/* Note Editor Overlay/Panel */}
            {selectedNote && (
                <div className="absolute inset-0 z-20 md:relative md:inset-auto md:z-auto md:w-[600px] lg:w-[800px] xl:w-[900px] shadow-2xl md:shadow-none transition-all duration-300 transform translate-x-0">
                    <NoteEditor
                        note={selectedNote}
                        folders={folders}
                        tags={tags}
                        onClose={() => setSelectedNote(null)}
                        onUpdate={handleUpdateNote}
                    />
                </div>
            )}
        </div>
    );
}

export default NotesPage;
