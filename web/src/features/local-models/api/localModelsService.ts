import apiClient from '../../../services/apiClient';

// Types
export enum ModelSource {
    HUGGINGFACE = 'huggingface',
    OLLAMA = 'ollama',
    CUSTOM = 'custom'
}

export enum ModelStatus {
    PENDING = 'pending',
    DOWNLOADING = 'downloading',
    READY = 'ready',
    FAILED = 'failed',
    CANCELLED = 'cancelled'
}

export interface LocalModel {
    id: number;
    name: string;
    model_id: string;
    source: ModelSource;
    model_type: string;
    description?: string;
    author?: string;
    version?: string;
    local_path?: string;
    size_bytes?: number;
    size_mb?: number;
    size_gb?: number;
    status: ModelStatus;
    progress: number;
    error_message?: string;
    is_active: boolean;
    created_at: string;
    download_started_at?: string;
    download_completed_at?: string;
}

export interface LocalModelListResponse {
    models: LocalModel[];
    total: number;
    downloading_count: number;
    ready_count: number;
}

export interface ModelStats {
    total_models: number;
    ready_models: number;
    downloading_models: number;
    failed_models: number;
    total_size_gb: number;
    disk_free_gb: number;
    disk_used_percent: number;
}

export interface DownloadRequest {
    model_id: string;
    source: ModelSource;
    model_type?: string;
}

export interface DownloadStartResponse {
    model_id: number;
    task_id: string;
    message: string;
    websocket_url: string;
}

export interface HuggingFaceModel {
    id: string;
    modelId: string;
    author?: string;
    pipeline_tag?: string;
    tags?: string[];
    downloads?: number;
    likes?: number;
    is_downloaded: boolean;
}

export interface HuggingFaceSearchResponse {
    models: HuggingFaceModel[];
    total: number;
    query: string;
}

export interface OllamaModel {
    name: string;
    model: string;
    size?: number;
    is_downloaded: boolean;
}

export interface OllamaListResponse {
    models: OllamaModel[];
    total: number;
}

// Service
export const localModelsService = {
    // List models
    getModels: async (params?: {
        source?: string;
        status?: string;
        ready_only?: boolean;
        limit?: number;
        offset?: number
    }) => {
        const response = await apiClient.get<LocalModelListResponse>('/local-models', { params });
        return response.data;
    },

    // Get stats
    getStats: async () => {
        const response = await apiClient.get<ModelStats>('/local-models/stats');
        return response.data;
    },

    // Get model details
    getModel: async (id: number) => {
        const response = await apiClient.get<LocalModel>(`/local-models/${id}`);
        return response.data;
    },

    // Delete model
    deleteModel: async (id: number) => {
        const response = await apiClient.delete(`/local-models/${id}`);
        return response.data;
    },

    // Start download
    downloadModel: async (data: DownloadRequest) => {
        const response = await apiClient.post<DownloadStartResponse>('/local-models/download', data);
        return response.data;
    },

    // Cancel download
    cancelDownload: async (id: number) => {
        const response = await apiClient.post(`/local-models/${id}/cancel`);
        return response.data;
    },

    // Search HuggingFace
    searchHuggingFace: async (query: string, task?: string) => {
        const response = await apiClient.post<HuggingFaceSearchResponse>('/local-models/search/huggingface', {
            query,
            task,
            limit: 20
        });
        return response.data;
    },

    // List Ollama models
    listOllamaAvailable: async () => {
        const response = await apiClient.get<OllamaListResponse>('/local-models/ollama/available');
        return response.data;
    },

    // Get ready models for agent use
    getModelsForAgent: async () => {
        const response = await apiClient.get<LocalModel[]>('/local-models/for-agent');
        return response.data;
    },

    // Get download progress websocket URL
    getWebSocketUrl: (modelId: number) => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host; // Use frontend host which proxies to backend
        // Or if you have a specific backend URL configured
        // const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        // const wsHost = backendUrl.replace(/^http/, 'ws');

        return `/ws/model-download/${modelId}`;
    }
};
