import React, { useState, useEffect } from 'react';
import { Download, ExternalLink, HardDrive, Terminal, FileCode } from 'lucide-react';
import { localModelsService, HuggingFaceModel, OllamaModel, ModelSource } from '../api/localModelsService';
import { SearchInput } from '../../../components/ui/SearchInput';
import './ModelSearch.css';

interface ModelSearchProps {
    onDownload: (modelId: string, source: ModelSource, modelType: string) => void;
}

export const ModelSearch: React.FC<ModelSearchProps> = ({ onDownload }) => {
    const [activeTab, setActiveTab] = useState<'huggingface' | 'ollama'>('huggingface');
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<(HuggingFaceModel | OllamaModel)[]>([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    // Clear state when switching tabs
    useEffect(() => {
        setQuery('');
        setResults([]);
        setSearched(false);
    }, [activeTab]);

    const executeSearch = async (searchQuery: string) => {
        if (!searchQuery.trim() && activeTab === 'huggingface') return;

        setLoading(true);
        try {
            if (activeTab === 'huggingface') {
                const response = await localModelsService.searchHuggingFace(searchQuery);
                setResults(response.models);
            } else {
                // For Ollama, we fetch the available list and filter client-side
                const response = await localModelsService.listOllamaAvailable();
                let models = response.models;

                if (searchQuery.trim()) {
                    const lowerQuery = searchQuery.toLowerCase();
                    models = models.filter(m =>
                        m.name.toLowerCase().includes(lowerQuery) ||
                        m.model.toLowerCase().includes(lowerQuery)
                    );
                }
                setResults(models);
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

    const formatSize = (bytes?: number) => {
        if (!bytes) return 'Unknown size';
        return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
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
                    placeholder={activeTab === 'huggingface' ? "Search HuggingFace models (e.g., llama-3, mistral)..." : "Search Ollama models (e.g., llama3, mistral)..."}
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

                {/* Initial state for Ollama - show suggestion if not searched yet */}
                {!searched && activeTab === 'ollama' && !loading && (
                    <div className="start-search-hint">
                        <p className="hint-text">Search for popular models like "llama3", "mistral", "gemma", etc.</p>
                        <button className="btn-link" onClick={() => executeSearch('')}>
                            View popular Ollama models
                        </button>
                    </div>
                )}

                {results.map((model) => {
                    // Type guard/check
                    const isHuggingFace = 'modelId' in model;

                    return (
                        <div key={isHuggingFace ? (model as HuggingFaceModel).modelId : (model as OllamaModel).name} className="model-result-card">
                            <div className="model-info">
                                <div className="model-header">
                                    <h3>{isHuggingFace ? (model as HuggingFaceModel).modelId : (model as OllamaModel).name}</h3>
                                    {model.is_downloaded && (
                                        <span className="badge-downloaded">
                                            <HardDrive size={12} /> Installed
                                        </span>
                                    )}
                                </div>

                                {isHuggingFace ? (
                                    // HuggingFace Meta
                                    <div className="model-meta">
                                        <span className="meta-item">
                                            <Download size={14} /> {formatDownloads((model as HuggingFaceModel).downloads)}
                                        </span>
                                        {(model as HuggingFaceModel).pipeline_tag && (
                                            <span className="meta-item tag">{(model as HuggingFaceModel).pipeline_tag}</span>
                                        )}
                                        <span className="meta-item">
                                            Author: {(model as HuggingFaceModel).author || 'Unknown'}
                                        </span>
                                    </div>
                                ) : (
                                    // Ollama Meta
                                    <div className="model-meta">
                                        <span className="meta-item">
                                            <Terminal size={14} /> {(model as OllamaModel).model}
                                        </span>
                                        <span className="meta-item">
                                            <FileCode size={14} /> {formatSize((model as OllamaModel).size)}
                                        </span>
                                    </div>
                                )}

                                {isHuggingFace && (
                                    <div className="model-tags">
                                        {(model as HuggingFaceModel).tags?.slice(0, 5).map(tag => (
                                            <span key={tag} className="tag-pill">{tag}</span>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="model-actions">
                                {isHuggingFace && (
                                    <a
                                        href={`https://huggingface.co/${(model as HuggingFaceModel).modelId}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="btn-icon"
                                        title="View on HuggingFace"
                                    >
                                        <ExternalLink size={18} />
                                    </a>
                                )}
                                <button
                                    className="btn-download"
                                    disabled={model.is_downloaded}
                                    onClick={() => onDownload(
                                        isHuggingFace ? (model as HuggingFaceModel).modelId : (model as OllamaModel).name,
                                        isHuggingFace ? ModelSource.HUGGINGFACE : ModelSource.OLLAMA,
                                        isHuggingFace ? ((model as HuggingFaceModel).pipeline_tag || 'text-generation') : 'text-generation'
                                    )}
                                >
                                    {model.is_downloaded ? 'Installed' : 'Download'}
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
