import React, { useState } from 'react';
import { Download, ExternalLink, HardDrive } from 'lucide-react';
import { localModelsService, HuggingFaceModel, ModelSource } from '../api/localModelsService';
import { SearchInput } from '../../../components/ui/SearchInput';
import './ModelSearch.css';

interface ModelSearchProps {
    onDownload: (modelId: string, source: ModelSource, modelType: string) => void;
}

export const ModelSearch: React.FC<ModelSearchProps> = ({ onDownload }) => {
    const [activeTab, setActiveTab] = useState<'huggingface' | 'ollama'>('huggingface');
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<HuggingFaceModel[]>([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const executeSearch = async (searchQuery: string) => {
        if (!searchQuery.trim()) return;

        setLoading(true);
        try {
            if (activeTab === 'huggingface') {
                const response = await localModelsService.searchHuggingFace(searchQuery);
                setResults(response.models);
            }
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setLoading(false);
            setSearched(true);
        }
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        executeSearch(query);
    };

    const formatDownloads = (num?: number) => {
        if (!num) return '0';
        if (num > 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num > 1000) return `${(num / 1000).toFixed(1)}k`;
        return num.toString();
    };

    return (
        <div className="model-search-container">
            <div className="search-tabs">
                <button
                    className={`tab-btn ${activeTab === 'huggingface' ? 'active' : ''}`}
                    onClick={() => setActiveTab('huggingface')}
                >
                    HuggingFace
                </button>
                <button
                    className={`tab-btn ${activeTab === 'ollama' ? 'active' : ''}`}
                    onClick={() => setActiveTab('ollama')}
                >
                    Ollama Library
                </button>
            </div>

            <form onSubmit={handleSearch} className="search-form">
                <SearchInput
                    value={query}
                    onChange={setQuery}
                    onSearch={(val) => executeSearch(val)}
                    placeholder={activeTab === 'huggingface' ? "Search HuggingFace models (e.g., llama-3, mistral)..." : "Search Ollama models..."}
                    className="search-input-wrapper"
                    debounceMs={500}
                />
                <button type="submit" className="search-btn" disabled={loading}>
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </form>

            <div className="search-results">
                {searched && results.length === 0 && !loading && (
                    <div className="no-results">
                        <p>No models found matching "{query}"</p>
                    </div>
                )}

                {results.map((model) => (
                    <div key={model.id} className="model-result-card">
                        <div className="model-info">
                            <div className="model-header">
                                <h3>{model.modelId}</h3>
                                {model.is_downloaded && (
                                    <span className="badge-downloaded">
                                        <HardDrive size={12} /> Installed
                                    </span>
                                )}
                            </div>
                            <div className="model-meta">
                                <span className="meta-item">
                                    <Download size={14} /> {formatDownloads(model.downloads)}
                                </span>
                                {model.pipeline_tag && (
                                    <span className="meta-item tag">{model.pipeline_tag}</span>
                                )}
                                <span className="meta-item">
                                    Author: {model.author || 'Unknown'}
                                </span>
                            </div>
                            <div className="model-tags">
                                {model.tags?.slice(0, 5).map(tag => (
                                    <span key={tag} className="tag-pill">{tag}</span>
                                ))}
                            </div>
                        </div>
                        <div className="model-actions">
                            <a
                                href={`https://huggingface.co/${model.modelId}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn-icon"
                                title="View on HuggingFace"
                            >
                                <ExternalLink size={18} />
                            </a>
                            <button
                                className="btn-download"
                                disabled={model.is_downloaded}
                                onClick={() => onDownload(
                                    model.modelId,
                                    ModelSource.HUGGINGFACE,
                                    model.pipeline_tag || 'text-generation'
                                )}
                            >
                                {model.is_downloaded ? 'Installed' : 'Download'}
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
