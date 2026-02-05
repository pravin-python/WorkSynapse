import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { loaderService } from './loaderService';

interface LoaderContextType {
    isLoading: boolean;
    showLoader: () => void;
    hideLoader: () => void;
}

const LoaderContext = createContext<LoaderContextType | undefined>(undefined);

export function LoaderProvider({ children }: { children: ReactNode }) {
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        return loaderService.subscribe((loading) => {
            setIsLoading(loading);
        });
    }, []);

    const value = {
        isLoading,
        showLoader: () => loaderService.show(),
        hideLoader: () => loaderService.hide()
    };

    return (
        <LoaderContext.Provider value={value}>
            {children}
        </LoaderContext.Provider>
    );
}

export function useLoaderContext() {
    const context = useContext(LoaderContext);
    if (context === undefined) {
        throw new Error('useLoaderContext must be used within a LoaderProvider');
    }
    return context;
}
