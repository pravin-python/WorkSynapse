import React from 'react';
import { Trash2, Play, HardDrive, RefreshCw } from 'lucide-react';
import { LocalModel, ModelStatus } from '../api/localModelsService';
import './LocalModelList.css';

interface LocalModelListProps {
    models: LocalModel[];
    onDelete: (id: number) => void;
    onRefresh: () => void;
}

export const LocalModelList: React.FC<LocalModelListProps> = ({ models, onDelete, onRefresh }) => {

    const formatSize = (bytes?: number) => {
        if (!bytes) return 'Unknown size';
        if (bytes > 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    };

    const getStatusBadge = (status: ModelStatus, progress: number) => {
        switch (status) {
            case ModelStatus.READY:
                return <span className="status-badge ready">Ready</span>;
            case ModelStatus.DOWNLOADING:
                return (
                    <div className="status-downloading">
                        <span className="status-text">Downloading {progress.toFixed(1)}%</span>
                        <div className="progress-bar-mini">
                            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                        </div>
                    </div>
                );
            case ModelStatus.FAILED:
                return <span className="status-badge failed">Failed</span>;
            case ModelStatus.PENDING:
                return <span className="status-badge pending">Pending</span>;
            default:
                return <span className="status-badge">{status}</span>;
        }
    };

    return (
        <div className="local-model-list">
            <div className="list-header">
                <h2>Installed Models</h2>
                <button onClick={onRefresh} className="btn-refresh" title="Refresh list">
                    <RefreshCw size={18} />
                </button>
            </div>

            {models.length === 0 ? (
                <div className="empty-state">
                    <HardDrive size={48} />
                    <p>No local models installed yet.</p>
                    <span className="subtitle">Search and download models to get started.</span>
                </div>
            ) : (
                <div className="models-grid">
                    {models.map((model) => (
                        <div key={model.id} className="model-card">
                            <div className="card-header">
                                <div className="header-top">
                                    <span className={`source-tag ${model.source}`}>{model.source}</span>
                                    {getStatusBadge(model.status, model.progress)}
                                </div>
                                <h3 title={model.model_id}>{model.name}</h3>
                            </div>

                            <div className="card-body">
                                <div className="info-row">
                                    <span className="label">Type:</span>
                                    <span className="value">{model.model_type}</span>
                                </div>
                                <div className="info-row">
                                    <span className="label">Size:</span>
                                    <span className="value">{formatSize(model.size_bytes)}</span>
                                </div>
                                {model.local_path && (
                                    <div className="info-row" title={model.local_path}>
                                        <span className="label">Path:</span>
                                        <span className="value path">{model.local_path.split('/').pop()}</span>
                                    </div>
                                )}
                            </div>

                            <div className="card-footer">
                                <button
                                    className="btn-action delete"
                                    onClick={() => onDelete(model.id)}
                                    disabled={model.status === ModelStatus.DOWNLOADING}
                                    title="Delete Model"
                                >
                                    <Trash2 size={16} /> Delete
                                </button>
                                {model.status === ModelStatus.READY && (
                                    <button className="btn-action use">
                                        <Play size={16} /> Use in Agent
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
