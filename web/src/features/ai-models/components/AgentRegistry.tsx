import { useState, useCallback, useEffect, useRef } from 'react';
import {
    Plus, RefreshCw, Filter, LayoutGrid
} from 'lucide-react';
import {
    AgentModel, getAgentModels, createAgentModel, updateAgentModel, deleteAgentModel,
    AgentModelCreate, AgentModelUpdate, LLMProvider
} from '../api/aiModelsService';
import { AgentModelCard } from '../components/AgentModelCard';
import { AgentModelModal } from '../components/AgentModelModal';
import { SearchInput } from '../../../components/ui/SearchInput';
import { useDebounce } from '../../../hooks/useDebounce';
import '../styles/AgentRegistry.css';

export function AgentRegistry() {
    const [models, setModels] = useState<AgentModel[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchText, setSearchText] = useState('');
    const debouncedSearch = useDebounce(searchText, 500);
    const [filterProviderId, setFilterProviderId] = useState<number | ''>('');
    const [showModal, setShowModal] = useState(false);
    const [editingModel, setEditingModel] = useState<AgentModel | undefined>(undefined);
    const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
    const [availableProviders, setAvailableProviders] = useState<LLMProvider[]>([]);

    const loadProviders = useCallback(async () => {
        try {
            const data = await import('../api/aiModelsService').then(m => m.default.getProviders());
            setAvailableProviders(data);
        } catch (err) {
            console.error('Failed to load providers for filter', err);
        }
    }, []);

    const loadModels = useCallback(async () => {
        setLoading(true);
        try {
            // Pass filters to backend for efficiency
            const data = await getAgentModels({
                search: debouncedSearch,
                provider_id: filterProviderId !== '' ? Number(filterProviderId) : undefined
            });
            setModels(data);
        } catch (err) {
            console.error('Failed to load agent models', err);
        } finally {
            setLoading(false);
        }
    }, [debouncedSearch, filterProviderId]);

    const mounted = useRef(false);

    // Initial load and updates on search/filter change
    useEffect(() => {
        if (!mounted.current) {
            mounted.current = true;
            loadModels();
            loadProviders();
        } else {
            // If dependencies change (debouncedSearch, filterProviderId), reload models
            loadModels();
        }
    }, [debouncedSearch, filterProviderId, loadModels, loadProviders]);

    const handleCreate = async (data: any) => {
        await createAgentModel(data as AgentModelCreate);
        loadModels();
    };

    const handleUpdate = async (data: any) => {
        if (!editingModel) return;
        await updateAgentModel(editingModel.id, data as AgentModelUpdate);
        loadModels();
    };

    const handleDelete = async (model: AgentModel) => {
        if (confirm(`Are you sure you want to soft delete ${model.display_name}?`)) {
            await deleteAgentModel(model.id);
            loadModels();
        }
    };

    // Client-side status filtering (backend supports it but we can do it here too if mixed)
    // Since we filtered provider/search in backend, we filter status here or backend.
    // Let's rely on client side for status to avoid re-fetch on status toggle if we want, 
    // BUT list is now filtered by provider.
    const filteredModels = models.filter(m => {
        if (filterStatus === 'active' && !m.is_active) return false;
        if (filterStatus === 'inactive' && m.is_active) return false;
        return true;
    });

    return (
        <div className="agent-models-registry">
            {/* Standard Toolbar Layout */}
            <div className="page-toolbar">
                <div className="toolbar-group">
                    <SearchInput
                        value={searchText}
                        onChange={setSearchText}
                        placeholder="Search models..."
                        onSearch={(val) => setSearchText(val)}
                        debounceMs={0}
                    />

                    <div className="filter-dropdown-container">
                        <select
                            className="filter-select"
                            value={filterProviderId}
                            onChange={e => setFilterProviderId(e.target.value ? Number(e.target.value) : '')}
                        >
                            <option value="">All Providers</option>
                            {availableProviders.map(p => (
                                <option key={p.id} value={p.id}>{p.display_name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="filter-dropdown-container">
                        <select
                            className="filter-select"
                            value={filterStatus}
                            onChange={e => setFilterStatus(e.target.value as any)}
                        >
                            <option value="all">All Status</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                        </select>
                    </div>
                </div>

                <div className="toolbar-actions">
                    <button className="btn btn-ghost" title="Filter" disabled>
                        <Filter size={16} /> Filters
                    </button>
                    <button className="btn btn-ghost" onClick={loadModels} disabled={loading} title="Refresh">
                        <RefreshCw size={16} className={loading ? 'spinning' : ''} />
                    </button>
                    <div className="view-toggle">
                        <button className="btn btn-icon active"><LayoutGrid size={16} /></button>
                        {/* <button className="btn btn-icon"><List size={16}/></button> */}
                    </div>
                    <button className="btn btn-primary" onClick={() => { setEditingModel(undefined); setShowModal(true); }}>
                        <Plus size={16} /> Add Model
                    </button>
                </div>
            </div>

            {/* Grid */}
            {loading ? (
                <div className="loading-state">
                    <div className="loading-spinner" />
                    <p>Loading registry...</p>
                </div>
            ) : (
                <div className="providers-grid">
                    {filteredModels.map(model => (
                        <AgentModelCard
                            key={model.id}
                            model={model}
                            onEdit={(m) => { setEditingModel(m); setShowModal(true); }}
                            onDelete={handleDelete}
                        />
                    ))}
                </div>
            )}

            {showModal && (
                <AgentModelModal
                    model={editingModel}
                    onClose={() => setShowModal(false)}
                    onSubmit={editingModel ? handleUpdate : handleCreate}
                />
            )}
        </div>
    );
}
