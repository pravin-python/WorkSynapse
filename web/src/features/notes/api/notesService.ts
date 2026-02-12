import { api } from '../../../services/apiClient';

// ===========================================
// TYPES
// ===========================================

export enum NoteVisibility {
    PRIVATE = "PRIVATE",
    SHARED = "SHARED",
    PROJECT = "PROJECT",
    ORGANIZATION = "ORGANIZATION"
}

export enum SharePermission {
    VIEW = "VIEW",
    EDIT = "EDIT"
}

export interface NoteFolder {
    id: number;
    name: string;
    owner_id: number;
    color?: string;
    icon?: string;
    created_at: string;
    // position?: number; // Backend has it, frontend might use it later
}

export interface NoteTag {
    id: number;
    name: string;
    color?: string;
    owner_id: number;
}

export interface NoteShare {
    id: number;
    note_id: number;
    shared_with_user_id: number;
    shared_by_user_id: number;
    permission: SharePermission;
    created_at: string;
    shared_with_email?: string;
    shared_by_email?: string;
}

export interface Note {
    id: number;
    title: string;
    content?: string;
    owner_id: number;
    folder_id?: number;
    is_starred: boolean;
    is_archived: boolean;
    created_at: string;
    updated_at: string;
    folder?: NoteFolder;
    tags: NoteTag[];
    shares: NoteShare[];
    is_owner: boolean;
    shared_permission?: SharePermission;
}

export interface NoteFilterParams {
    search?: string;
    folder_id?: number;
    tag_id?: number;
    is_starred?: boolean;
    shared?: boolean;
    skip?: number;
    limit?: number;
}

export interface CreateNotePayload {
    title: string;
    content?: string;
    folder_id?: number;
    tag_ids?: number[];
    is_starred?: boolean;
}

export interface UpdateNotePayload {
    title?: string;
    content?: string;
    folder_id?: number;
    tag_ids?: number[];
    is_starred?: boolean;
    is_archived?: boolean;
}

export interface CreateFolderPayload {
    name: string;
    color?: string;
}

export interface CreateTagPayload {
    name: string;
    color?: string;
}

export interface ShareNotePayload {
    email: string;
    permission: SharePermission;
}

// ===========================================
// SERVICE
// ===========================================

export const notesService = {
    // Notes
    getNotes: async (params?: NoteFilterParams) => {
        return api.get<Note[]>('/notes/', {
            params: {
                q: params?.search,
                folder_id: params?.folder_id,
                tag_id: params?.tag_id,
                starred: params?.is_starred,
                shared: params?.shared,
                skip: params?.skip,
                limit: params?.limit
            }
        });
    },

    getNote: async (id: number) => {
        return api.get<Note>(`/notes/${id}/`);
    },

    createNote: async (payload: CreateNotePayload) => {
        return api.post<Note>('/notes/', payload);
    },

    updateNote: async (id: number, payload: UpdateNotePayload) => {
        return api.put<Note>(`/notes/${id}`, payload);
    },

    deleteNote: async (id: number) => {
        return api.delete(`/notes/${id}`);
    },

    toggleNoteStar: async (id: number, isStarred: boolean) => {
        return api.post<Note>(`/notes/${id}/${isStarred ? 'star' : 'unstar'}`);
    },

    starNote: async (id: number) => {
        return api.post<Note>(`/notes/${id}/star`);
    },

    unstarNote: async (id: number) => {
        return api.post<Note>(`/notes/${id}/unstar`);
    },

    shareNote: async (id: number, payload: ShareNotePayload) => {
        return api.post<NoteShare>(`/notes/${id}/share`, payload);
    },

    // Folders
    getFolders: async () => {
        return api.get<NoteFolder[]>('/notes/folders/all');
    },

    createFolder: async (payload: CreateFolderPayload) => {
        return api.post<NoteFolder>('/notes/folders', payload);
    },

    updateFolder: async (id: number, payload: any) => {
        return api.put<NoteFolder>(`/notes/folders/${id}`, payload);
    },

    deleteFolder: async (id: number) => {
        return api.delete(`/notes/folders/${id}`);
    },

    // Tags
    getTags: async () => {
        return api.get<NoteTag[]>('/notes/tags/all');
    },

    createTag: async (payload: CreateTagPayload) => {
        return api.post<NoteTag>('/notes/tags', payload);
    },

    updateTag: async (id: number, payload: any) => {
        return api.put<NoteTag>(`/notes/tags/${id}`, payload);
    },

    deleteTag: async (id: number) => {
        return api.delete(`/notes/tags/${id}`);
    }
};

export default notesService;
