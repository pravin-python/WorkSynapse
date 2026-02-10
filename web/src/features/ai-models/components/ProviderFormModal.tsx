import React, { useState } from 'react';
import { FormModal } from '../../../components/ui/modals';
import { LLMProviderCreate, LLMProvider, LLMProviderUpdate } from '../api/aiModelsService';

interface ProviderFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: LLMProviderCreate | LLMProviderUpdate) => Promise<void>;
    initialData?: LLMProvider;
    isLoading?: boolean;
}

export function ProviderFormModal({
    isOpen,
    onClose,
    onSubmit,
    initialData,
    isLoading = false
}: ProviderFormModalProps) {
    const isEdit = !!initialData;

    // Form State
    const [name, setName] = useState(initialData?.name || '');
    const [displayName, setDisplayName] = useState(initialData?.display_name || '');
    const [description, setDescription] = useState(initialData?.description || '');
    const [baseUrl, setBaseUrl] = useState(initialData?.base_url || '');
    const [requiresApiKey, setRequiresApiKey] = useState(initialData?.requires_api_key ?? true);
    const [purchaseUrl, setPurchaseUrl] = useState(initialData?.purchase_url || '');
    const [documentationUrl, setDocumentationUrl] = useState(initialData?.documentation_url || '');
    // const [icon, setIcon] = useState(initialData?.icon || '');
    // const [type, setType] = useState(initialData?.type || 'custom');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const data: any = {
            display_name: displayName,
            description,
            base_url: baseUrl || null,
            requires_api_key: requiresApiKey,
            purchase_url: purchaseUrl || null,
            documentation_url: documentationUrl || null,
            // icon: icon || null,
        };

        if (!isEdit) {
            data.name = name;
            data.type = 'custom'; // Force custom for new providers
        }

        await onSubmit(data);
    };

    return (
        <FormModal
            isOpen={isOpen}
            onClose={onClose}
            title={isEdit ? 'Edit Provider' : 'Add Custom Provider'}
            onSubmit={handleSubmit}
            isLoading={isLoading}
            submitText={isEdit ? 'Update' : 'Create'}
        >
            {/* Name (ID) - Locked in Edit */}
            <div className="form-group">
                <label className="form-label">Internal Name (ID)</label>
                <input
                    type="text"
                    className="form-input"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="e.g. my-custom-llm"
                    disabled={isEdit}
                    required
                    pattern="[a-z0-9-_]+"
                    title="Lowercase letters, numbers, hyphens only"
                />
                <small className="form-hint">Unique identifier used in code (lowercase, no spaces).</small>
            </div>

            {/* Display Name */}
            <div className="form-group">
                <label className="form-label">Display Name</label>
                <input
                    type="text"
                    className="form-input"
                    value={displayName}
                    onChange={e => setDisplayName(e.target.value)}
                    placeholder="e.g. My Custom LLM"
                    required
                />
            </div>

            {/* Description */}
            <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                    className="form-textarea"
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    placeholder="Brief description of this provider..."
                    rows={3}
                />
            </div>

            {/* Base URL */}
            <div className="form-group">
                <label className="form-label">Base URL</label>
                <input
                    type="url"
                    className="form-input"
                    value={baseUrl}
                    onChange={e => setBaseUrl(e.target.value)}
                    placeholder="https://api.example.com/v1"
                />
                <small className="form-hint">Optional base URL for API requests.</small>
            </div>

            {/* URLs */}
            <div className="form-row" style={{ display: 'flex', gap: '1rem' }}>
                <div className="form-group" style={{ flex: 1 }}>
                    <label className="form-label">Purchase URL</label>
                    <input
                        type="url"
                        className="form-input"
                        value={purchaseUrl}
                        onChange={e => setPurchaseUrl(e.target.value)}
                        placeholder="https://..."
                    />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                    <label className="form-label">Docs URL</label>
                    <input
                        type="url"
                        className="form-input"
                        value={documentationUrl}
                        onChange={e => setDocumentationUrl(e.target.value)}
                        placeholder="https://..."
                    />
                </div>
            </div>

            {/* Checkbox */}
            <div className="form-check">
                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={requiresApiKey}
                        onChange={e => setRequiresApiKey(e.target.checked)}
                    />
                    Requires API Key
                </label>
            </div>
        </FormModal>
    );
}
