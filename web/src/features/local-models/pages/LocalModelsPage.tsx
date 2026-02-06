import React, { useEffect, useState, useRef } from 'react';
import { HardDrive, Download } from 'lucide-react';
import { localModelsService, LocalModel, ModelStats, ModelSource, ModelStatus } from '../api/localModelsService';
import { ModelSearch } from '../components/ModelSearch';
import { LocalModelList } from '../components/LocalModelList';
import './LocalModelsPage.css';

export const LocalModelsPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'installed' | 'search'>('installed');
    const [models, setModels] = useState<LocalModel[]>([]);
    const [stats, setStats] = useState<ModelStats | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [downloadingModels, setDownloadingModels] = useState<Set<number>>(new Set());

    // WebSocket connections
    const wsRef = useRef<Map<number, WebSocket>>(new Map());

    useEffect(() => {
        fetchData();
        return () => {
            // Cleanup WebSockets
            wsRef.current.forEach(ws => ws.close());
        };
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [modelsData, statsData] = await Promise.all([
                localModelsService.getModels(),
                localModelsService.getStats()
            ]);
            setModels(modelsData.models);
            setStats(statsData);

            // Reconnect WebSockets for downloading models
            modelsData.models.forEach(model => {
                if (model.status === ModelStatus.DOWNLOADING) {
                    trackDownloadProgress(model.id);
                }
            });

        } catch (err) {
            console.error('Failed to fetch data:', err);
            setError('Failed to load local models');
        } finally {
            setLoading(false);
        }
    };

    const trackDownloadProgress = (modelId: number) => {
        if (wsRef.current.has(modelId)) return;

        setDownloadingModels(prev => new Set(prev).add(modelId));

        const wsUrl = localModelsService.getWebSocketUrl(modelId);
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                setModels(prev => prev.map(m => {
                    if (m.id === modelId) {
                        // Update progress
                        const updated = {
                            ...m,
                            progress: data.progress,
                            status: data.status as ModelStatus
                        };

                        // If finished, remove from tracking and refresh stats
                        if (['ready', 'failed', 'cancelled'].includes(data.status)) {
                            ws.close();
                            wsRef.current.delete(modelId);
                            setDownloadingModels(prevModelIds => {
                                const newSet = new Set(prevModelIds);
                                newSet.delete(modelId);
                                return newSet;
                            });
                            // Refresh stats after slight delay
                            setTimeout(() => {
                                localModelsService.getStats().then(setStats);
                            }, 1000);
                        }

                        return updated;
                    }
                    return m;
                }));
            } catch (e) {
                console.error('WebSocket message error:', e);
            }
        };

        ws.onerror = (e) => {
            console.error('WebSocket error:', e);
        };

        wsRef.current.set(modelId, ws);
    };

    const handleDownload = async (modelId: string, source: ModelSource, modelType: string) => {
        try {
            const response = await localModelsService.downloadModel({
                model_id: modelId,
                source,
                model_type: modelType
            });

            // Add temp model to list immediately
            const newModel: LocalModel = {
                id: response.model_id,
                name: modelId.split('/').pop() || modelId,
                model_id: modelId,
                source,
                model_type: modelType,
                status: ModelStatus.PENDING,
                progress: 0,
                is_active: true,
                created_at: new Date().toISOString()
            };

            setModels(prev => [newModel, ...prev]);

            // Start tracking
            trackDownloadProgress(response.model_id);

            // Switch to list view
            setActiveTab('installed');

        } catch (err) {
            console.error('Download failed:', err);
            // Show toast or alert
            alert('Failed to start download. Check console for details.');
        }
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm('Are you sure you want to delete this model and all its files?')) {
            return;
        }

        try {
            await localModelsService.deleteModel(id);
            setModels(prev => prev.filter(m => m.id !== id));
            if (stats) {
                const deletedModel = models.find(m => m.id === id);
                if (deletedModel) {
                    setStats({
                        ...stats,
                        total_models: stats.total_models - 1,
                        ready_models: deletedModel.status === ModelStatus.READY ? stats.ready_models - 1 : stats.ready_models,
                        // Update size roughly
                        total_size_gb: stats.total_size_gb - (deletedModel.size_gb || 0)
                    });
                }
            }
        } catch (err) {
            console.error('Delete failed:', err);
            alert('Failed to delete model');
        }
    };

    return (
        <div className="local-models-page">
            <header className="page-header">
                <div>
                    <h1>Local LLM Models</h1>
                    <p>Manage, download, and run AI models locally on your server.</p>
                </div>
                {stats && (
                    <div className="models-stats">
                        <div className="stat-item">
                            <span className="label">Installed</span>
                            <span className="value">{stats.ready_models}</span>
                        </div>
                        <div className="stat-item">
                            <span className="label">Total Size</span>
                            <span className="value">{stats.total_size_gb.toFixed(1)} GB</span>
                        </div>
                        <div className="stat-item">
                            <span className="label">Disk Free</span>
                            <span className="value">{stats.disk_free_gb.toFixed(1)} GB</span>
                        </div>
                    </div>
                )}
            </header>

            <div className="page-content">
                <div className="tabs-nav">
                    <button
                        className={`nav-tab ${activeTab === 'installed' ? 'active' : ''}`}
                        onClick={() => setActiveTab('installed')}
                    >
                        <HardDrive size={18} />
                        Installed Models
                        {downloadingModels.size > 0 && <span className="badge-count">{downloadingModels.size} Downloading</span>}
                    </button>
                    <button
                        className={`nav-tab ${activeTab === 'search' ? 'active' : ''}`}
                        onClick={() => setActiveTab('search')}
                    >
                        <Download size={18} />
                        Download New
                    </button>
                </div>

                <div className="tab-content">
                    {error && (
                        <div className="error-banner">
                            {error}
                        </div>
                    )}
                    {loading && models.length === 0 ? (
                        <div className="loading-state">Loading models...</div>
                    ) : activeTab === 'installed' ? (
                        <LocalModelList
                            models={models}
                            onDelete={handleDelete}
                            onRefresh={fetchData}
                        />
                    ) : (
                        <ModelSearch onDownload={handleDownload} />
                    )}
                </div>
            </div>
        </div>
    );
};
