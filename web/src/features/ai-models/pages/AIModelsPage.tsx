/**
 * AI Models Management Page
 * =========================
 * 
 * Comprehensive page for managing AI model providers and encrypted API keys.
 * Admin/Staff only access for provider management.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import {
    Key, Shield, RefreshCw, Check,
    Database, Cpu, AlertTriangle, Plus
} from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { ProviderCard } from '../components/ProviderCard';
import { ApiKeyTable } from '../components/ApiKeyTable';
import { AddApiKeyModal } from '../components/AddApiKeyModal';
import aiModelsService, {
    LLMProvider,
    LLMApiKey,
    LLMApiKeyCreate,
    LLMProviderCreate, LLMProviderUpdate,
    createProvider, updateProvider, deleteProvider
} from '../api/aiModelsService';
import { AgentRegistry } from '../components/AgentRegistry';
import { ProviderFormModal } from '../components/ProviderFormModal';
import { ConfirmModal } from '../../../components/ui/modals';
import './AIModelsPage.css';

export function AIModelsPage() {
    const { isAdmin } = useAuth();

    // State
    const [activeTab, setActiveTab] = useState<'providers' | 'registry'>('providers');
    const [providers, setProviders] = useState<LLMProvider[]>([]);
    const [keys, setKeys] = useState<LLMApiKey[]>([]);
    const [selectedProvider, setSelectedProvider] = useState<LLMProvider | null>(null);
    const [showAddModal, setShowAddModal] = useState(false);

    // Provider Access State
    const [showProviderModal, setShowProviderModal] = useState(false);
    const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null);

    // Confirm Modal State
    const [confirmModal, setConfirmModal] = useState<{
        isOpen: boolean;
        title: string;
        message: string;
        onConfirm: () => void;
        isDestructive?: boolean;
    }>({
        isOpen: false,
        title: '',
        message: '',
        onConfirm: () => { },
        isDestructive: false
    });

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [seeding, setSeeding] = useState(false);

    // Load data on mount
    const loadData = useCallback(async () => {
        setLoading(true);
        setError('');

        try {
            const [providersData, keysData] = await Promise.all([
                aiModelsService.getProviders(),
                aiModelsService.getApiKeys()
            ]);
            setProviders(providersData);
            setKeys(keysData);
        } catch (err: any) {
            console.error('Failed to load AI models data:', err);
            setError(err.response?.data?.detail || 'Failed to load data');
        } finally {
            setLoading(false);
        }
    }, []);

    const mounted = useRef(false);

    useEffect(() => {
        if (!mounted.current) {
            mounted.current = true;
            loadData();
        }
    }, [loadData]);

    // Handlers
    const handleAddKey = (provider: LLMProvider) => {
        setSelectedProvider(provider);
        setShowAddModal(true);
        setError('');
    };

    const handleSubmitKey = async (data: LLMApiKeyCreate) => {
        setSubmitting(true);
        try {
            const newKey = await aiModelsService.createApiKey(data);

            // Update local state
            setKeys(prev => [...prev, newKey]);
            setProviders(prev => prev.map(p =>
                p.id === data.provider_id
                    ? { ...p, has_api_key: true, key_count: p.key_count + 1 }
                    : p
            ));

            setShowAddModal(false);
            setSelectedProvider(null);
            setSuccess(`API key for ${selectedProvider?.display_name} added successfully!`);
            setTimeout(() => setSuccess(''), 4000);
        } catch (err: any) {
            throw err; // Let the modal handle the error display
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteKey = async (keyId: number) => {
        const keyToDelete = keys.find(k => k.id === keyId);
        if (!keyToDelete) return;

        const confirmed = window.confirm(
            `Are you sure you want to delete the API key "${keyToDelete.label}" for ${keyToDelete.provider_name}? This action cannot be undone.`
        );
        if (!confirmed) return;

        try {
            await aiModelsService.deleteApiKey(keyId);

            // Update local state
            setKeys(prev => prev.filter(k => k.id !== keyId));
            setProviders(prev => prev.map(p =>
                p.id === keyToDelete.provider_id
                    ? {
                        ...p,
                        has_api_key: p.key_count - 1 > 0,
                        key_count: p.key_count - 1
                    }
                    : p
            ));

            setSuccess('API key deleted successfully');
            setTimeout(() => setSuccess(''), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to delete API key');
        }
    };

    const handleToggleActive = async (key: LLMApiKey) => {
        try {
            const updated = await aiModelsService.updateApiKey(key.id, {
                is_active: !key.is_active
            });

            setKeys(prev => prev.map(k =>
                k.id === key.id ? updated : k
            ));

            setSuccess(`API key ${updated.is_active ? 'activated' : 'deactivated'}`);
            setTimeout(() => setSuccess(''), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update API key');
        }
    };

    const handleSeedProviders = async () => {
        setSeeding(true);
        try {
            const result = await aiModelsService.seedProviders();
            await loadData();
            setSuccess(result.message);
            setTimeout(() => setSuccess(''), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to seed providers');
        } finally {
            setSeeding(false);
        }
    };

    // Provider Management Handlers
    const handleAddProvider = () => {
        setEditingProvider(null);
        setShowProviderModal(true);
        setError('');
    };

    const handleEditProvider = (provider: LLMProvider) => {
        setEditingProvider(provider);
        setShowProviderModal(true);
        setError('');
    };

    const handleSubmitProvider = async (data: LLMProviderCreate | LLMProviderUpdate) => {
        setSubmitting(true);
        try {
            if (editingProvider) {
                const updated = await updateProvider(editingProvider.id, data);
                setProviders(prev => prev.map(p => p.id === updated.id ? { ...p, ...updated } : p));
                setSuccess(`Provider ${updated.display_name} updated successfully`);
            } else {
                const created = await createProvider(data as LLMProviderCreate);
                setProviders(prev => [...prev, created]);
                setSuccess(`Provider ${created.display_name} created successfully`);
            }
            setShowProviderModal(false);
            setEditingProvider(null);
            setTimeout(() => setSuccess(''), 4000);
        } catch (err: any) {
            throw err; // FormModal will handle error display if we passed setError
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteProvider = async (provider: LLMProvider) => {
        setConfirmModal({
            isOpen: true,
            title: 'Delete Provider',
            message: `Are you sure you want to delete ${provider.display_name}? This will remove all associated API keys and model configurations. This action cannot be undone.`,
            isDestructive: true,
            onConfirm: async () => {
                try {
                    await deleteProvider(provider.id);
                    setProviders(prev => prev.filter(p => p.id !== provider.id));
                    setSuccess('Provider deleted successfully');
                    setTimeout(() => setSuccess(''), 3000);
                } catch (err: any) {
                    setError(err.response?.data?.detail || 'Failed to delete provider');
                } finally {
                    setConfirmModal(prev => ({ ...prev, isOpen: false }));
                }
            }
        });
    };

    // Stats calculations
    const stats = {
        totalProviders: providers.length,
        activeProviders: providers.filter(p => p.has_api_key).length,
        totalKeys: keys.length,
        activeKeys: keys.filter(k => k.is_active && k.is_valid).length
    };

    return (
        <div className="ai-models-page">
            {/* Header */}
            <header className="page-header">
                <div className="header-content">
                    <div className="header-title">
                        <h1><Cpu size={28} /> AI Models & Providers</h1>
                        <p>Manage API keys and AI Agent Model Registry</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="tabs-nav">
                    <button
                        className={`tab-btn ${activeTab === 'providers' ? 'active' : ''}`}
                        onClick={() => setActiveTab('providers')}
                    >
                        Providers (API Keys)
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'registry' ? 'active' : ''}`}
                        onClick={() => setActiveTab('registry')}
                    >
                        Agent Model Registry
                    </button>
                </div>
            </header>

            {activeTab === 'registry' ? (
                <AgentRegistry />
            ) : (
                <>
                    <div className="header-actions" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                        {isAdmin() && (
                            <button className="btn btn-secondary" onClick={handleAddProvider}>
                                <Plus size={16} />
                                Add Custom Provider
                            </button>
                        )}
                        <button
                            className="btn btn-secondary"
                            onClick={loadData}
                            disabled={loading}
                        >
                            <RefreshCw size={16} className={loading ? 'spinning' : ''} />
                            Refresh
                        </button>
                        {isAdmin() && (
                            <button
                                className="btn btn-primary"
                                onClick={handleSeedProviders}
                                disabled={seeding}
                            >
                                {seeding ? (
                                    <>
                                        <span className="spinner" />
                                        Seeding...
                                    </>
                                ) : (
                                    <>
                                        <Database size={16} />
                                        Seed Providers
                                    </>
                                )}
                            </button>
                        )}
                    </div>
                    {/* ... existing provider content ... */}


                    {/* Alerts */}
                    {success && (
                        <div className="alert alert-success">
                            <Check size={18} />
                            {success}
                        </div>
                    )}
                    {error && (
                        <div className="alert alert-error">
                            <AlertTriangle size={18} />
                            {error}
                            <button className="alert-close" onClick={() => setError('')}>×</button>
                        </div>
                    )}

                    {/* Stats Cards */}
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-icon providers">
                                <Cpu size={24} />
                            </div>
                            <div className="stat-content">
                                <span className="stat-value">{stats.totalProviders}</span>
                                <span className="stat-label">Available Providers</span>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon active">
                                <Check size={24} />
                            </div>
                            <div className="stat-content">
                                <span className="stat-value">{stats.activeProviders}</span>
                                <span className="stat-label">Configured</span>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon keys">
                                <Key size={24} />
                            </div>
                            <div className="stat-content">
                                <span className="stat-value">{stats.totalKeys}</span>
                                <span className="stat-label">Total Keys</span>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon security">
                                <Shield size={24} />
                            </div>
                            <div className="stat-content">
                                <span className="stat-value">{stats.activeKeys}</span>
                                <span className="stat-label">Active & Valid</span>
                            </div>
                        </div>
                    </div>

                    {/* Loading State */}
                    {loading && (
                        <div className="loading-state">
                            <div className="loading-spinner" />
                            <p>Loading providers...</p>
                        </div>
                    )}

                    {/* Providers Grid */}
                    {!loading && (
                        <section className="providers-section">
                            <div className="section-header">
                                <h2><Database size={20} /> Available Providers</h2>
                                <span className="section-badge">{providers.length} providers</span>
                            </div>

                            {providers.length === 0 ? (
                                <div className="empty-state">
                                    <Cpu size={48} />
                                    <h3>No providers available</h3>
                                    <p>Click "Seed Providers" to add default LLM providers</p>
                                </div>
                            ) : (
                                <div className="providers-grid">
                                    {providers.map(provider => (
                                        <ProviderCard
                                            key={provider.id}
                                            provider={provider}
                                            onAddKey={handleAddKey}
                                            onManage={isAdmin() ? handleEditProvider : undefined}
                                            onDelete={isAdmin() && !provider.is_system ? () => handleDeleteProvider(provider) : undefined}
                                        />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {/* API Keys Section */}
                    {!loading && (
                        <section className="keys-section">
                            <div className="section-header">
                                <h2><Shield size={20} /> Your Encrypted Keys</h2>
                                <span className="section-badge">{keys.length} keys</span>
                            </div>

                            <div className="encryption-notice">
                                <Shield size={16} />
                                <span>
                                    All API keys are encrypted using <strong>Fernet (AES-128)</strong> symmetric encryption
                                    before storage. Keys are only decrypted during agent execution and never exposed to the frontend.
                                </span>
                            </div>

                            <ApiKeyTable
                                keys={keys}
                                onDelete={handleDeleteKey}
                                onToggleActive={handleToggleActive}
                            />
                        </section>
                    )}

                    {/* Add Key Modal */}
                    {showAddModal && selectedProvider && (
                        <AddApiKeyModal
                            provider={selectedProvider}
                            onClose={() => {
                                setShowAddModal(false);
                                setSelectedProvider(null);
                            }}
                            onSubmit={handleSubmitKey}
                            loading={submitting}
                        />
                    )}

                    {/* Provider Form Modal */}
                    {showProviderModal && (
                        <ProviderFormModal
                            isOpen={showProviderModal}
                            onClose={() => {
                                setShowProviderModal(false);
                                setEditingProvider(null);
                            }}
                            onSubmit={handleSubmitProvider}
                            initialData={editingProvider || undefined}
                            isLoading={submitting}
                        />
                    )}

                    {/* Confirm Modal */}
                    <ConfirmModal
                        isOpen={confirmModal.isOpen}
                        onClose={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}
                        onConfirm={confirmModal.onConfirm}
                        title={confirmModal.title}
                        message={confirmModal.message}
                        isDestructive={confirmModal.isDestructive}
                    />
                </>
            )}
        </div>
    );
}

export default AIModelsPage;
