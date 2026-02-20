/**
 * UI Service
 * ==========
 * Fetches dynamic UI configuration from the backend.
 */
import { api } from './apiClient';

// Interfaces matching the backend schemas
export interface UIMenuItem {
    id: number;
    label: string;
    path?: string;
    icon?: string;
    order: number;
    roles?: string[];
    children?: UIMenuItem[];
}

export interface UIMenu {
    id: number;
    name: string;
    description?: string;
    items: UIMenuItem[];
}

export const uiService = {
    /**
     * Get a menu structure by name (e.g., 'sidebar')
     */
    getMenu: async (name: string): Promise<UIMenu> => {
        return api.get<UIMenu>(`/ui/menus/${name}`);
    },

    /**
     * Get a page configuration by slug
     */
    getPage: async (slug: string) => {
        return api.get(`/ui/pages/${slug}`);
    }
};
