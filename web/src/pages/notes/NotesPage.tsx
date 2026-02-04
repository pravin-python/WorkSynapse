/**
 * WorkSynapse Notes Page
 * ======================
 * Rich text notes with folders and tags.
 */
import React, { useState } from 'react';
import { StickyNote, Plus, Search, FolderOpen, Tag, Star, Clock, MoreVertical } from 'lucide-react';
import './Notes.css';

interface Note {
    id: number;
    title: string;
    content: string;
    folder?: string;
    tags: string[];
    is_starred: boolean;
    updated_at: string;
}

export function NotesPage() {
    const [notes, setNotes] = useState<Note[]>([
        { id: 1, title: 'Project Requirements', content: 'Key requirements for WorkSynapse v2.0...', folder: 'Work', tags: ['requirements', 'important'], is_starred: true, updated_at: '2024-02-10' },
        { id: 2, title: 'Meeting Notes - Sprint Planning', content: 'Sprint 12 planning session notes...', folder: 'Work', tags: ['meetings'], is_starred: false, updated_at: '2024-02-09' },
        { id: 3, title: 'API Design Ideas', content: 'Thoughts on REST vs GraphQL...', folder: 'Ideas', tags: ['api', 'design'], is_starred: true, updated_at: '2024-02-08' },
        { id: 4, title: 'Personal Tasks', content: 'Things to do this week...', folder: 'Personal', tags: ['tasks'], is_starred: false, updated_at: '2024-02-07' },
    ]);
    const [selectedNote, setSelectedNote] = useState<Note | null>(notes[0]);
    const [searchQuery, setSearchQuery] = useState('');

    return (
        <div className="notes-page">
            {/* Notes Sidebar */}
            <aside className="notes-sidebar">
                <div className="sidebar-header">
                    <h2>Notes</h2>
                    <button className="btn btn-primary btn-sm">
                        <Plus size={16} />
                    </button>
                </div>

                <div className="notes-search">
                    <Search size={16} />
                    <input
                        type="text"
                        placeholder="Search notes..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="notes-folders">
                    <button className="folder-btn active">
                        <StickyNote size={16} />
                        <span>All Notes</span>
                        <span className="count">{notes.length}</span>
                    </button>
                    <button className="folder-btn">
                        <Star size={16} />
                        <span>Starred</span>
                        <span className="count">{notes.filter(n => n.is_starred).length}</span>
                    </button>
                    <button className="folder-btn">
                        <FolderOpen size={16} />
                        <span>Work</span>
                        <span className="count">2</span>
                    </button>
                    <button className="folder-btn">
                        <FolderOpen size={16} />
                        <span>Ideas</span>
                        <span className="count">1</span>
                    </button>
                </div>

                <div className="notes-list">
                    {notes.filter(n => n.title.toLowerCase().includes(searchQuery.toLowerCase())).map((note) => (
                        <button
                            key={note.id}
                            className={`note-item ${selectedNote?.id === note.id ? 'active' : ''}`}
                            onClick={() => setSelectedNote(note)}
                        >
                            <div className="note-item-header">
                                <h4>{note.title}</h4>
                                {note.is_starred && <Star size={14} className="starred" />}
                            </div>
                            <p className="note-preview">{note.content}</p>
                            <div className="note-meta">
                                <Clock size={12} />
                                <span>{note.updated_at}</span>
                            </div>
                        </button>
                    ))}
                </div>
            </aside>

            {/* Note Editor */}
            <main className="note-editor">
                {selectedNote ? (
                    <>
                        <div className="editor-header">
                            <div className="editor-info">
                                <input
                                    type="text"
                                    className="note-title-input"
                                    value={selectedNote.title}
                                    onChange={(e) => setSelectedNote({ ...selectedNote, title: e.target.value })}
                                />
                                <div className="note-tags">
                                    {selectedNote.tags.map((tag) => (
                                        <span key={tag} className="tag">
                                            <Tag size={10} />
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div className="editor-actions">
                                <button className="btn-icon">
                                    <Star size={18} className={selectedNote.is_starred ? 'starred' : ''} />
                                </button>
                                <button className="btn-icon">
                                    <MoreVertical size={18} />
                                </button>
                            </div>
                        </div>

                        <textarea
                            className="note-content"
                            value={selectedNote.content}
                            onChange={(e) => setSelectedNote({ ...selectedNote, content: e.target.value })}
                            placeholder="Start writing..."
                        />
                    </>
                ) : (
                    <div className="empty-state">
                        <StickyNote size={48} />
                        <h3>Select a note</h3>
                        <p>Choose a note from the sidebar or create a new one</p>
                    </div>
                )}
            </main>
        </div>
    );
}

export default NotesPage;
