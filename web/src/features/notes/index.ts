/**
 * Notes Feature Module
 * ====================
 * 
 * Feature module for managing notes, folders, and tags.
 */

// API Service
export { default as notesService } from './api/notesService';
export * from './api/notesService';

// Pages
export { default as NotesPage } from './pages/NotesPage'; // Note: check if default export

// Components
export { FolderModal } from './components/FolderModal';
export { FolderSidebar } from './components/FolderSidebar';
export { NoteCard } from './components/NoteCard';
export { NoteEditor } from './components/NoteEditor';
export { NotesList } from './components/NotesList';
export { NotesToolbar } from './components/NotesToolbar';
export { ShareModal } from './components/ShareModal';
export { TagModal } from './components/TagModal';
