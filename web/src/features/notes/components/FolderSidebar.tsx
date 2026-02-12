import React, { useState } from 'react';
import {
    Folder, Star, Users, FileText, Plus, Trash2
} from 'lucide-react';
import { NoteFolder, notesService } from '../api/notesService';
import { FolderModal } from './FolderModal';

interface FolderSidebarProps {
    selectedFolderId: number | null;
    isStarred: boolean;
    isShared: boolean;
    onSelectFolder: (id: number | null) => void;
    onSelectStarred: () => void;
    onSelectShared: () => void;
    onSelectAll: () => void;
    folders: NoteFolder[];
    onFolderCreated: () => void;
    onFolderDeleted: () => void;
}



export const FolderSidebar: React.FC<FolderSidebarProps> = ({
    folders,
    selectedFolderId,
    isStarred,
    isShared,
    onSelectFolder,
    onSelectStarred,
    onSelectShared,
    onSelectAll,
    onFolderCreated,
    onFolderDeleted
}) => {
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    // Removed internal fetchFolders logic


    const handleDeleteFolder = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        if (window.confirm('Are you sure you want to delete this folder? Notes inside will lose their folder association.')) {
            try {
                await notesService.deleteFolder(id);
                onFolderDeleted();
                if (selectedFolderId === id) {
                    onSelectAll();
                }
            } catch (error) {
                console.error('Failed to delete folder', error);
            }
        }
    };

    const NavItem = ({
        icon: Icon,
        label,
        active,
        onClick,
        color,
        count,
        onDelete
    }: {
        icon: any,
        label: string,
        active: boolean,
        onClick: () => void,
        color?: string,
        count?: number,
        onDelete?: (e: React.MouseEvent) => void
    }) => (
        <button
            onClick={onClick}
            className={`group w-full flex items-center gap-3 px-3 py-2 text-sm font-medium transition-all rounded-md mx-2 mb-0.5 ${active
                ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
        >
            <Icon size={18} className={`transition-colors ${active ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'}`} style={{ color: active && color ? color : undefined }} />
            <span className="flex-1 text-left truncate">{label}</span>
            {count !== undefined && (
                <span className="text-xs text-gray-400 dark:text-gray-500 font-normal">
                    {count}
                </span>
            )}
            {onDelete && (
                <div
                    role="button"
                    onClick={onDelete}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-gray-400 hover:text-red-500 transition-all"
                    title="Delete"
                >
                    <Trash2 size={13} />
                </div>
            )}
        </button>
    );

    return (
        <div className="flex flex-col h-full bg-gray-50/50 dark:bg-gray-900/50 border-r border-gray-200 dark:border-gray-800 w-[260px] flex-shrink-0">
            {/* Quick Filters */}
            <div className="pt-6 pb-2">
                <div className="px-5 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Library
                </div>
                <NavItem
                    icon={FileText}
                    label="All Notes"
                    active={!isStarred && !isShared && selectedFolderId === null}
                    onClick={onSelectAll}
                />
                <NavItem
                    icon={Star}
                    label="Starred"
                    active={isStarred}
                    onClick={onSelectStarred}
                    color="#f59e0b"
                />
                <NavItem
                    icon={Users}
                    label="Shared with me"
                    active={isShared}
                    onClick={onSelectShared}
                    color="#3b82f6"
                />
            </div>

            {/* Folders */}
            <div className="flex-1 overflow-y-auto py-2">
                <div className="px-5 mb-2 flex items-center justify-between group">
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        Folders
                    </div>
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-gray-500"
                        title="New Folder"
                    >
                        <Plus size={14} />
                    </button>
                </div>

                <div className="space-y-0.5">
                    {folders.map(folder => (
                        <NavItem
                            key={folder.id}
                            icon={Folder}
                            label={folder.name}
                            active={selectedFolderId === folder.id}
                            onClick={() => onSelectFolder(folder.id)}
                            color={folder.color || '#6366f1'}
                            onDelete={(e) => handleDeleteFolder(e, folder.id)}
                        />
                    ))}
                    {folders.length === 0 && (
                        <div className="px-5 py-2 text-sm text-gray-400 italic">
                            No folders yet
                        </div>
                    )}
                </div>
            </div>

            {/* Bottom Action */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-800">
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400 transition-colors w-full px-2 py-1"
                >
                    <Plus size={16} />
                    <span>New Folder</span>
                </button>
            </div>

            <FolderModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSuccess={onFolderCreated}
            />
        </div>
    );
};
